"""Relationship evidence and bounded all-status relationship traversal."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from chronicle.ai.tools.contracts import ToolExecutionContext
from chronicle.ai.tools.errors import (
    CorpusRetrievalError,
    MalformedToolInputError,
    ResultLimitExceededError,
)
from chronicle.ai.tools.relationships import MAX_PATH_DEPTH, TraceRelationshipsInput


def _invoke_trace(tool_registry, corpus, corpus_id, context, **tool_input):
    return tool_registry.invoke(
        "trace_relationships",
        {"corpusId": corpus_id, **tool_input},
        context,
        corpus,
    )[0]


def _branching_graph_view(base_corpus, branch_count: int):
    """Return a synthetic read-only graph view using real relationship models."""
    investigation = base_corpus.get_investigation()
    start_node_id = investigation.claims[0].id
    template = investigation.relationships[0]
    relationships = [
        template.model_copy(
            update={
                "id": f"test-rel-{index:02d}",
                "fromId": start_node_id,
                "toId": f"test-node-{index:02d}",
                "evidenceLinkIds": [],
            }
        )
        for index in reversed(range(branch_count))
    ]
    relationships_by_id = {relationship.id: relationship for relationship in relationships}
    relationships_by_node = {
        start_node_id: [relationship.id for relationship in relationships],
        **{relationship.toId: [relationship.id] for relationship in relationships},
    }

    class CorpusView:
        def __getattr__(self, name):
            return getattr(base_corpus, name)

        @property
        def corpus_id(self):
            return base_corpus.corpus_id

        def get_relationships_touching(self, node_id):
            return [
                relationships_by_id[relationship_id]
                for relationship_id in relationships_by_node.get(node_id, [])
            ]

        def get_relationship(self, relationship_id):
            if relationship_id in relationships_by_id:
                return relationships_by_id[relationship_id]
            return base_corpus.get_relationship(relationship_id)

    return CorpusView(), start_node_id


def test_get_relationship_evidence_preserves_stored_record_and_canonical_evidence(
    tool_registry, corpus, corpus_id, context
):
    relationship = corpus.get_investigation().relationships[0]
    links = sorted(corpus.get_evidence_links_for(relationship.id), key=lambda link: link.id)

    output, _record = tool_registry.invoke(
        "get_relationship_evidence",
        {"corpusId": corpus_id, "relationshipId": relationship.id},
        context,
        corpus,
    )

    assert output.fromId == relationship.fromId
    assert output.toId == relationship.toId
    assert output.directOrInferred == relationship.directOrInferred.value
    assert output.evidenceClassification == relationship.evidenceClassification.value
    assert output.reviewStatus == relationship.reviewStatus.value
    assert output.visibility == relationship.visibility.value
    returned = (
        output.supportingEvidence.entries
        + output.contradictingEvidence.entries
        + output.contextualEvidence.entries
    )
    assert sorted(entry.evidenceLink.evidenceLinkId for entry in returned) == [link.id for link in links]
    assert {entry.evidenceLink.role for entry in returned} == {link.role.value for link in links}


def test_get_relationship_evidence_unknown_id_raises(tool_registry, corpus, corpus_id, context):
    with pytest.raises(CorpusRetrievalError):
        tool_registry.invoke(
            "get_relationship_evidence",
            {"corpusId": corpus_id, "relationshipId": "no-such-relationship"},
            context,
            corpus,
        )


def test_trace_relationships_includes_a_proposed_relationship(tool_registry, corpus, corpus_id, context):
    relationship = next(
        relationship
        for relationship in corpus.get_investigation().relationships
        if relationship.reviewStatus.value == "proposed"
    )

    output = _invoke_trace(
        tool_registry,
        corpus,
        corpus_id,
        context,
        startNodeId=relationship.fromId,
        maxDepth=1,
        maxPaths=8,
    )

    traced_ids = {edge.relationshipId for path in output.paths for edge in path.edges}
    assert relationship.id in traced_ids


def test_trace_relationships_preserves_raw_edge_fields_and_evidence(
    tool_registry, corpus, corpus_id, context
):
    relationship = corpus.get_investigation().relationships[0]
    links = sorted(corpus.get_evidence_links_for(relationship.id), key=lambda link: link.id)

    output = _invoke_trace(
        tool_registry,
        corpus,
        corpus_id,
        context,
        startNodeId=relationship.fromId,
        maxDepth=1,
        maxPaths=8,
    )
    edge = next(
        edge
        for path in output.paths
        for edge in path.edges
        if edge.relationshipId == relationship.id
    )

    assert edge.reviewStatus == relationship.reviewStatus.value
    assert edge.evidenceClassification == relationship.evidenceClassification.value
    assert edge.directOrInferred == relationship.directOrInferred.value
    assert edge.visibility == relationship.visibility.value
    assert [entry.evidenceLink.evidenceLinkId for entry in edge.evidenceLinks] == [link.id for link in links]
    assert edge.evidenceLinkIds == [link.id for link in links]
    assert [entry.evidenceLink.role for entry in edge.evidenceLinks] == [link.role.value for link in links]
    assert edge.evidenceLinkTotalCount == len(links)
    assert edge.evidenceLinkReturnedCount == len(edge.evidenceLinks)
    assert edge.evidenceLinksTruncated is False

    assert sum(
        len(path_edge.evidenceLinks)
        for path in output.paths
        for path_edge in path.edges
    ) <= context.maximumResults


def test_relationship_evidence_uses_one_global_context_budget(
    tool_registry, corpus_registry
):
    corpus = corpus_registry.get_corpus("concert-of-europe-1814-1822")
    relationship = next(
        item
        for item in corpus.get_investigation().relationships
        if len(corpus.get_evidence_links_for(item.id)) >= 2
    )
    output, _ = tool_registry.invoke(
        "get_relationship_evidence",
        {"corpusId": corpus.corpus_id, "relationshipId": relationship.id},
        ToolExecutionContext(corpusId=corpus.corpus_id, maximumResults=1),
        corpus,
    )

    returned = (
        output.supportingEvidence.entries
        + output.contradictingEvidence.entries
        + output.contextualEvidence.entries
    )
    assert len(returned) <= 1
    assert output.returnedCount == len(returned)
    assert output.truncated is True


def test_trace_relationships_true_truncation_uses_a_sentinel(tool_registry, corpus, corpus_id, context):
    corpus, start_node_id = _branching_graph_view(corpus, branch_count=3)

    output = _invoke_trace(
        tool_registry,
        corpus,
        corpus_id,
        context,
        startNodeId=start_node_id,
        maxDepth=1,
        maxPaths=2,
    )

    assert output.returnedCount == 2
    assert output.truncated is True
    assert [path.nodeIds[-1] for path in output.paths] == ["test-node-00", "test-node-01"]


def test_trace_relationships_exactly_at_limit_is_not_truncated(tool_registry, corpus, corpus_id, context):
    corpus, start_node_id = _branching_graph_view(corpus, branch_count=2)

    output = _invoke_trace(
        tool_registry,
        corpus,
        corpus_id,
        context,
        startNodeId=start_node_id,
        maxDepth=1,
        maxPaths=2,
    )

    assert output.returnedCount == 2
    assert output.truncated is False


def test_trace_relationships_rejects_context_result_limit(tool_registry, corpus, corpus_id):
    corpus, start_node_id = _branching_graph_view(corpus, branch_count=2)
    context = ToolExecutionContext(corpusId=corpus_id, maximumResults=1)

    with pytest.raises(ResultLimitExceededError):
        _invoke_trace(
            tool_registry,
            corpus,
            corpus_id,
            context,
            startNodeId=start_node_id,
            maxDepth=1,
            maxPaths=2,
        )


def test_trace_omitted_default_clamps_to_a_smaller_context(
    tool_registry, corpus, corpus_id
):
    relationship = corpus.get_investigation().relationships[0]
    context = ToolExecutionContext(corpusId=corpus_id, maximumResults=1)
    output = _invoke_trace(
        tool_registry,
        corpus,
        corpus_id,
        context,
        startNodeId=relationship.fromId,
    )
    assert output.returnedCount <= 1

    spec = next(
        item
        for item in tool_registry.list_specs(context, corpus)
        if item.name == "trace_relationships"
    )
    assert spec.maxResultLimit == 1
    assert spec.inputSchema["properties"]["maxPaths"]["default"] == 1
    assert spec.inputSchema["properties"]["maxDepth"]["maximum"] == MAX_PATH_DEPTH


def test_trace_relationships_input_schema_rejects_depth_above_hard_cap(corpus_id):
    with pytest.raises(ValidationError):
        TraceRelationshipsInput(
            corpusId=corpus_id,
            startNodeId="any-node",
            maxDepth=MAX_PATH_DEPTH + 1,
        )


def test_trace_relationships_unknown_node_raises(tool_registry, corpus, corpus_id, context):
    with pytest.raises(CorpusRetrievalError):
        _invoke_trace(
            tool_registry,
            corpus,
            corpus_id,
            context,
            startNodeId="no-such-node",
        )


def test_trace_relationships_rejects_max_depth_above_hard_cap(tool_registry, corpus, corpus_id, context):
    relationship = corpus.get_investigation().relationships[0]
    with pytest.raises(MalformedToolInputError):
        _invoke_trace(
            tool_registry,
            corpus,
            corpus_id,
            context,
            startNodeId=relationship.fromId,
            maxDepth=999,
        )


def test_trace_relationships_rejects_max_paths_above_hard_cap(tool_registry, corpus, corpus_id, context):
    relationship = corpus.get_investigation().relationships[0]
    with pytest.raises(ResultLimitExceededError):
        _invoke_trace(
            tool_registry,
            corpus,
            corpus_id,
            context,
            startNodeId=relationship.fromId,
            maxPaths=999,
        )


def test_trace_relationships_paths_never_revisit_a_node(tool_registry, corpus, corpus_id, context):
    relationship = corpus.get_investigation().relationships[0]
    output = _invoke_trace(
        tool_registry,
        corpus,
        corpus_id,
        context,
        startNodeId=relationship.fromId,
        maxDepth=5,
        maxPaths=8,
    )
    for path in output.paths:
        assert len(path.nodeIds) == len(set(path.nodeIds)), "a path revisited a node"


def test_relationship_tool_specs_tell_a_planner_when_to_use_and_avoid_them(tool_registry):
    evidence = tool_registry.get("get_relationship_evidence")
    trace = tool_registry.get("trace_relationships")

    assert "known relationship ID" in evidence.use_when
    assert "path" in evidence.avoid_when
    assert "EvidenceLink" in evidence.output_summary
    assert "multi-edge" in trace.use_when
    assert "claim, relationship, or knowledge-state node" in trace.use_when
    assert "single relationship" in trace.avoid_when
    assert "reviewStatus" in trace.output_summary
