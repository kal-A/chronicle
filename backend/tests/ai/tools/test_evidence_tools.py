"""get_claim_evidence and find_counterevidence -- never summarize or
reinterpret evidence; an empty counterevidence/contextual list is a
valid, honest answer."""

from __future__ import annotations

import pytest

from chronicle.ai.tools import ToolExecutionContext
from chronicle.ai.tools.errors import CorpusRetrievalError


def test_get_claim_evidence_every_claim_has_supporting_evidence(tool_registry, corpus, corpus_id, context):
    """Rule 6 of validate_generated_investigation guarantees every claim
    has >=1 supporting EvidenceLink -- confirm the tool surfaces it."""
    for claim in corpus.get_investigation().claims:
        output, _record = tool_registry.invoke(
            "get_claim_evidence", {"corpusId": corpus_id, "claimId": claim.id}, context, corpus
        )
        assert output.claimId == claim.id
        assert output.statement == claim.statement
        assert output.supportingEvidence.totalCount >= 1
        for entry in output.supportingEvidence.entries:
            assert entry.evidenceLink.role == "supporting"
            assert entry.evidenceLink.targetType == "claim"
            assert entry.evidenceLink.targetId == claim.id
            assert entry.passageLocator
            assert entry.documentVisibility
            assert entry.sourceType


def test_get_claim_evidence_unknown_claim_raises(tool_registry, corpus, corpus_id, context):
    with pytest.raises(CorpusRetrievalError):
        tool_registry.invoke(
            "get_claim_evidence", {"corpusId": corpus_id, "claimId": "no-such-claim"}, context, corpus
        )


def test_get_claim_evidence_ledger_is_surfaced_when_present(tool_registry, corpus, corpus_id, context):
    investigation = corpus.get_investigation()
    ledgered_claim_ids = {ledger.claimId for ledger in investigation.claimLedgers}
    if not ledgered_claim_ids:
        pytest.skip("this corpus has no claim ledgers")
    claim_id = next(iter(ledgered_claim_ids))
    output, _record = tool_registry.invoke(
        "get_claim_evidence", {"corpusId": corpus_id, "claimId": claim_id}, context, corpus
    )
    assert output.ledgerConclusion is not None


def test_find_counterevidence_on_a_claim_with_no_counterevidence_is_empty(tool_registry, corpus, corpus_id, context):
    investigation = corpus.get_investigation()
    contested_claim_ids = {
        link.targetId
        for link in investigation.evidenceLinks
        if link.targetType.value == "claim" and link.role.value == "counterevidence"
    }
    uncontested = next((c for c in investigation.claims if c.id not in contested_claim_ids), None)
    if uncontested is None:
        pytest.skip("every claim in this corpus has counterevidence")
    output, _record = tool_registry.invoke(
        "find_counterevidence", {"corpusId": corpus_id, "recordId": uncontested.id}, context, corpus
    )
    assert output.contradictingEvidence.entries == []
    assert output.contradictingEvidence.totalCount == 0
    assert output.recordType == "claim"


def test_find_counterevidence_resolves_relationship_record_type(tool_registry, corpus, corpus_id, context):
    relationships = corpus.get_investigation().relationships
    if not relationships:
        pytest.skip("this corpus has no relationships")
    output, _record = tool_registry.invoke(
        "find_counterevidence", {"corpusId": corpus_id, "recordId": relationships[0].id}, context, corpus
    )
    assert output.recordType == "relationship"


def test_find_counterevidence_unknown_record_raises(tool_registry, corpus, corpus_id, context):
    with pytest.raises(CorpusRetrievalError):
        tool_registry.invoke(
            "find_counterevidence", {"corpusId": corpus_id, "recordId": "no-such-record"}, context, corpus
        )


def test_claim_evidence_uses_one_global_context_budget_and_truthful_role_totals(
    tool_registry, corpus_registry
):
    corpus = corpus_registry.get_corpus("blank-cheque-golden")
    relationship = next(
        relationship
        for relationship in corpus.get_investigation().relationships
        if len(corpus.get_evidence_links_for(relationship.id)) >= 2
    )
    context = ToolExecutionContext(corpusId=corpus.corpus_id, maximumResults=1)

    output, _ = tool_registry.invoke(
        "find_counterevidence",
        {"corpusId": corpus.corpus_id, "recordId": relationship.id},
        context,
        corpus,
    )

    assert output.totalCount == 1
    assert output.returnedCount == 1
    assert output.truncated is False
    assert sum(
        group.returnedCount
        for group in (output.contradictingEvidence, output.contextualEvidence)
    ) <= context.maximumResults


def test_evidence_excerpt_is_bounded_and_temporal_roles_are_not_collapsed(
    tool_registry, corpus_registry
):
    corpus = corpus_registry.get_corpus("blank-cheque-golden")
    claim = corpus.get_investigation().claims[0]
    output, _ = tool_registry.invoke(
        "get_claim_evidence",
        {"corpusId": corpus.corpus_id, "claimId": claim.id},
        ToolExecutionContext(corpusId=corpus.corpus_id),
        corpus,
    )
    entry = output.supportingEvidence.entries[0]
    passage = corpus.get_passage(entry.evidenceLink.passageId)

    assert len(entry.excerpt) <= 500
    assert entry.sentTime == passage.sentTime
    assert entry.receivedTime == passage.receivedTime
    assert entry.sourceDate == corpus.get_source(entry.evidenceLink.sourceId).dateOfSource


@pytest.mark.parametrize(
    ("tool_name", "id_field"),
    [
        ("get_claim_evidence", "claimId"),
        ("find_counterevidence", "recordId"),
        ("get_source_metadata", "sourceId"),
        ("get_actor_knowledge_state", "entityId"),
    ],
)
def test_owned_scalar_tool_inputs_have_explicit_length_bounds(tool_registry, tool_name, id_field):
    schema = tool_registry.get(tool_name).input_model.model_json_schema()["properties"]
    assert schema["corpusId"]["maxLength"] == 200
    assert schema[id_field]["maxLength"] == 200
