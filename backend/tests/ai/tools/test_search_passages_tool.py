"""search_passages tool wiring -- the scoring/filter behavior itself is
already covered by tests/corpus/test_search_passages.py against
corpus.search_passages directly; this file checks the tool-layer wrapper
specifically (registration, capability check, invoke path)."""

from __future__ import annotations

import re
import json

import pytest

from chronicle.ai.tools.contracts import ToolExecutionContext
from chronicle.ai.tools.errors import UnsupportedCapabilityError


def test_search_passages_is_registered(tool_registry):
    definition = tool_registry.get("search_passages")
    assert definition.required_capabilities == frozenset({"passages"})


def test_search_tool_spec_advertises_filter_enum_values(
    tool_registry, corpus, corpus_id
):
    spec = next(
        item
        for item in tool_registry.list_specs(
            ToolExecutionContext(corpusId=corpus_id),
            corpus,
        )
        if item.name == "search_passages"
    )
    rendered = json.dumps(spec.inputSchema)
    assert "counterevidence" in rendered
    assert "primary-official-diplomatic" in rendered


def test_invoke_search_passages_returns_hits_from_this_corpus(tool_registry, corpus, corpus_id, context):
    output, record = tool_registry.invoke(
        "search_passages", {"corpusId": corpus_id, "query": "the"}, context, corpus
    )
    known_ids = {p.id for p in corpus.get_investigation().passages}
    for hit in output.hits:
        assert hit.passageId in known_ids
    assert record.toolName == "search_passages"


def test_search_passages_honors_context_result_cap(tool_registry, corpus, corpus_id):
    from chronicle.ai.tools.contracts import ToolExecutionContext

    output, _ = tool_registry.invoke(
        "search_passages",
        {"corpusId": corpus_id, "query": "the", "maxResults": 1},
        ToolExecutionContext(corpusId=corpus_id, maximumResults=1),
        corpus,
    )
    assert len(output.hits) <= 1
    assert output.returnedCount == len(output.hits)
    assert sum(len(hit.evidenceLinks) for hit in output.hits) <= 1
    assert sum(len(hit.matchedDates) for hit in output.hits) <= 1
    assert sum(
        len(factor.matchedTerms)
        for hit in output.hits
        for factor in hit.scoreFactors
    ) <= 1
    assert sum(
        len(factor.matchedRecordIds)
        for hit in output.hits
        for factor in hit.scoreFactors
    ) <= 1
    assert all(
        hit.evidenceLinkReturnedCount == len(hit.evidenceLinks)
        and hit.evidenceLinksTruncated
        == (hit.evidenceLinkTotalCount > hit.evidenceLinkReturnedCount)
        for hit in output.hits
    )


def test_search_omitted_default_clamps_to_a_smaller_context(tool_registry, corpus, corpus_id):
    output, _ = tool_registry.invoke(
        "search_passages",
        {"corpusId": corpus_id, "query": "the"},
        ToolExecutionContext(corpusId=corpus_id, maximumResults=1),
        corpus,
    )
    assert output.returnedCount <= 1


def test_invoke_search_passages_rejects_unknown_corpus_scoped_input(tool_registry, corpus, corpus_id):
    from chronicle.ai.tools.contracts import ToolExecutionContext
    from chronicle.ai.tools.errors import CorpusMismatchError

    context = ToolExecutionContext(corpusId=corpus_id)
    with pytest.raises(CorpusMismatchError):
        tool_registry.invoke(
            "search_passages", {"corpusId": "some-other-corpus", "query": "the"}, context, corpus
        )


def test_role_filtered_search_prioritizes_the_qualifying_evidence_projection(
    tool_registry, corpus, corpus_id
):
    investigation = corpus.get_investigation()
    link = next(
        (item for item in investigation.evidenceLinks if item.role.value == "counterevidence"),
        None,
    )
    if link is None:
        pytest.skip("corpus has no counterevidence link")
    passage = corpus.get_passage(link.passageId)
    query = next(token for token in re.findall(r"\w+", passage.excerpt) if len(token) >= 4)

    output, _ = tool_registry.invoke(
        "search_passages",
        {
            "corpusId": corpus_id,
            "query": query,
            "evidenceRoles": ["counterevidence"],
            "maxResults": 1,
        },
        ToolExecutionContext(corpusId=corpus_id, maximumResults=1),
        corpus,
    )

    assert output.hits
    assert output.hits[0].evidenceLinks
    assert output.hits[0].evidenceLinks[0].role == "counterevidence"
