"""get_source_metadata and compare_sources -- real implementations
(E2 plan decision 3), pure metadata, never an interpretive judgment."""

from __future__ import annotations

import pytest

from chronicle.ai.tools import ToolExecutionContext
from chronicle.ai.tools.errors import MalformedToolInputError
from chronicle.ai.tools.errors import CorpusRetrievalError


def test_get_source_metadata_matches_the_real_source_record(tool_registry, corpus, corpus_id, context):
    source = corpus.get_investigation().sources[0]
    output, _record = tool_registry.invoke(
        "get_source_metadata", {"corpusId": corpus_id, "sourceId": source.id}, context, corpus
    )
    assert output.sourceId == source.id
    assert output.title == source.title
    assert output.creator == source.authorOrOrigin
    assert output.sourceType == source.sourceType.value
    assert output.primarySecondaryStatus in ("primary", "secondary", "tertiary")
    assert output.canonicalSourceReference == source.linkOrLocation
    assert output.relatedDocumentReturnedCount == len(output.relatedDocumentIds)
    assert output.relatedPassageReturnedCount == len(output.relatedPassageIds)


def test_get_source_metadata_unknown_source_raises(tool_registry, corpus, corpus_id, context):
    with pytest.raises(CorpusRetrievalError):
        tool_registry.invoke(
            "get_source_metadata", {"corpusId": corpus_id, "sourceId": "no-such-source"}, context, corpus
        )


def test_get_source_metadata_related_documents_belong_to_the_source(tool_registry, corpus, corpus_id, context):
    source = corpus.get_investigation().sources[0]
    output, _record = tool_registry.invoke(
        "get_source_metadata", {"corpusId": corpus_id, "sourceId": source.id}, context, corpus
    )
    for document_id in output.relatedDocumentIds:
        assert corpus.get_document(document_id).sourceId == source.id


def test_compare_sources_requires_capability(tool_registry):
    definition = tool_registry.get("compare_sources")
    assert definition.required_capabilities == frozenset({"source_comparison"})


def test_compare_sources_returns_one_entry_per_requested_source(tool_registry, corpus, corpus_id, context):
    sources = corpus.get_investigation().sources
    if len(sources) < 2:
        pytest.skip("this corpus has fewer than 2 sources")
    source_ids = [sources[0].id, sources[1].id]
    output, _record = tool_registry.invoke(
        "compare_sources", {"corpusId": corpus_id, "sourceIds": source_ids}, context, corpus
    )
    assert [e.sourceId for e in output.entries] == source_ids


def test_compare_sources_requires_at_least_two_sources(tool_registry, corpus, corpus_id, context):
    source = corpus.get_investigation().sources[0]
    with pytest.raises(MalformedToolInputError):
        tool_registry.invoke(
            "compare_sources", {"corpusId": corpus_id, "sourceIds": [source.id]}, context, corpus
        )


def test_compare_sources_counts_are_never_negative(tool_registry, corpus, corpus_id, context):
    sources = corpus.get_investigation().sources
    if len(sources) < 2:
        pytest.skip("this corpus has fewer than 2 sources")
    output, _record = tool_registry.invoke(
        "compare_sources",
        {"corpusId": corpus_id, "sourceIds": [sources[0].id, sources[1].id]},
        context,
        corpus,
    )
    for entry in output.entries:
        assert entry.passageCount >= 0
        assert entry.claimsSupportedCount >= 0
        assert entry.relationshipsSupportedCount >= 0


def test_compare_sources_only_calls_supporting_links_support(tool_registry, corpus_registry):
    # The Troppau source has a relationship counterevidence link whose target
    # is supported by a *different* source, so counting all roles would
    # incorrectly report three supported relationships here instead of two.
    corpus = corpus_registry.get_corpus("concert-of-europe-1814-1822")
    investigation = corpus.get_investigation()
    source_ids = [source.id for source in investigation.sources]
    output, _ = tool_registry.invoke(
        "compare_sources",
        {"corpusId": corpus.corpus_id, "sourceIds": source_ids},
        ToolExecutionContext(corpusId=corpus.corpus_id),
        corpus,
    )

    for entry in output.entries:
        passage_ids = {
            passage.id
            for passage in investigation.passages
            if corpus.get_document(passage.documentId).sourceId == entry.sourceId
        }
        supporting_claim_targets = {
            link.targetId
            for link in investigation.evidenceLinks
            if link.passageId in passage_ids
            and link.targetType.value == "claim"
            and link.role.value == "supporting"
        }
        supporting_relationship_targets = {
            link.targetId
            for link in investigation.evidenceLinks
            if link.passageId in passage_ids
            and link.targetType.value == "relationship"
            and link.role.value == "supporting"
        }
        assert entry.claimsSupportedCount == len(supporting_claim_targets)
        assert entry.relationshipsSupportedCount == len(supporting_relationship_targets)
        assert all(link.role == "supporting" for link in entry.claimEvidenceByRole.supporting.evidenceLinks)
        assert all(
            link.role == "counterevidence"
            for link in entry.claimEvidenceByRole.counterevidence.evidenceLinks
        )
        assert all(link.role == "context" for link in entry.claimEvidenceByRole.context.evidenceLinks)
        assert all(
            link.role == "supporting"
            for link in entry.relationshipEvidenceByRole.supporting.evidenceLinks
        )
        assert all(
            link.role == "counterevidence"
            for link in entry.relationshipEvidenceByRole.counterevidence.evidenceLinks
        )
        assert all(
            link.role == "context"
            for link in entry.relationshipEvidenceByRole.context.evidenceLinks
        )

    troppau = next(entry for entry in output.entries if entry.sourceId == "source-troppau-protocol")
    assert troppau.relationshipsSupportedCount == 2
    assert troppau.relationshipEvidenceByRole.counterevidence.targetTotalCount == 1


def test_source_tools_bound_all_lists_by_execution_context(tool_registry, corpus_registry):
    corpus = corpus_registry.get_corpus("blank-cheque-golden")
    context = ToolExecutionContext(corpusId=corpus.corpus_id, maximumResults=1)
    sources = corpus.get_investigation().sources

    metadata, metadata_record = tool_registry.invoke(
        "get_source_metadata",
        {"corpusId": corpus.corpus_id, "sourceId": sources[0].id},
        context,
        corpus,
    )
    assert len(metadata.relatedDocumentIds) <= 1
    assert len(metadata.relatedPassageIds) <= 1
    assert len(metadata.relatedDocumentIds) + len(metadata.relatedPassageIds) <= 1
    assert metadata_record.resultCount == metadata.returnedCount
    assert metadata.relatedDocumentTruncated == (
        metadata.relatedDocumentTotalCount > metadata.relatedDocumentReturnedCount
    )
    assert metadata.relatedPassageTruncated == (
        metadata.relatedPassageTotalCount > metadata.relatedPassageReturnedCount
    )

    comparison, _ = tool_registry.invoke(
        "compare_sources",
        {"corpusId": corpus.corpus_id, "sourceIds": [source.id for source in sources]},
        context,
        corpus,
    )
    assert comparison.totalCount == len(sources)
    assert comparison.returnedCount == 1
    assert comparison.truncated is True
    for entry in comparison.entries:
        for field in (
            entry.claimEvidenceByRole.supporting.evidenceLinks,
            entry.claimEvidenceByRole.counterevidence.evidenceLinks,
            entry.claimEvidenceByRole.context.evidenceLinks,
            entry.relationshipEvidenceByRole.supporting.evidenceLinks,
            entry.relationshipEvidenceByRole.counterevidence.evidenceLinks,
            entry.relationshipEvidenceByRole.context.evidenceLinks,
        ):
            assert len(field) <= 1


def test_compare_sources_uses_one_global_nested_evidence_budget(tool_registry, corpus_registry):
    corpus = corpus_registry.get_corpus("concert-of-europe-1814-1822")
    context = ToolExecutionContext(corpusId=corpus.corpus_id, maximumResults=2)

    comparison, _ = tool_registry.invoke(
        "compare_sources",
        {
            "corpusId": corpus.corpus_id,
            "sourceIds": ["source-troppau-protocol", "source-vienna-final-act"],
        },
        context,
        corpus,
    )

    coverages = [
        coverage
        for entry in comparison.entries
        for breakdown in (entry.claimEvidenceByRole, entry.relationshipEvidenceByRole)
        for coverage in (breakdown.supporting, breakdown.counterevidence, breakdown.context)
    ]
    assert sum(len(coverage.evidenceLinks) for coverage in coverages) <= 2
    assert sum(len(coverage.targetIds) for coverage in coverages) <= 2


def test_compare_sources_input_is_bounded(tool_registry, corpus, corpus_id, context):
    with pytest.raises(MalformedToolInputError):
        tool_registry.invoke(
            "compare_sources",
            {"corpusId": corpus_id, "sourceIds": [f"source-{index}" for index in range(21)]},
            context,
            corpus,
        )
