"""Evidence lookup and bounded traversal over stored relationships."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ...corpus.bounds import CollectionBudget
from ...corpus.protocol import InvestigationCorpus
from .contracts import MAX_TOOL_RESULT_LIMIT, ToolExecutionContext
from .errors import PathDepthExceededError, ResultLimitExceededError
from .evidence import EvidenceEntry, EvidenceGroup, _evidence_entry, _group
from .registry import ToolDefinition

MAX_PATH_DEPTH = 5
MAX_PATHS = 20
DEFAULT_PATH_DEPTH = 3
DEFAULT_MAX_PATHS = 5


# --- get_relationship_evidence ----------------------------------------------


class GetRelationshipEvidenceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpusId: str = Field(min_length=1)
    relationshipId: str = Field(min_length=1)


class GetRelationshipEvidenceOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpusId: str
    relationshipId: str
    fromId: str
    toId: str
    relationshipType: str
    directOrInferred: str
    evidenceClassification: str
    reviewStatus: str
    visibility: str
    totalCount: int = Field(ge=0)
    returnedCount: int = Field(ge=0)
    truncated: bool
    supportingEvidence: EvidenceGroup
    contradictingEvidence: EvidenceGroup
    contextualEvidence: EvidenceGroup


def _get_relationship_evidence(
    tool_input: GetRelationshipEvidenceInput,
    context: ToolExecutionContext,
    corpus: InvestigationCorpus,
) -> GetRelationshipEvidenceOutput:
    relationship = corpus.get_relationship(tool_input.relationshipId)
    links = sorted(corpus.get_evidence_links_for(relationship.id), key=lambda link: link.id)
    returned_links = links[: context.maximumResults]
    return GetRelationshipEvidenceOutput(
        corpusId=tool_input.corpusId,
        relationshipId=relationship.id,
        fromId=relationship.fromId,
        toId=relationship.toId,
        relationshipType=relationship.relationshipType,
        directOrInferred=relationship.directOrInferred.value,
        evidenceClassification=relationship.evidenceClassification.value,
        reviewStatus=relationship.reviewStatus.value,
        visibility=relationship.visibility.value,
        totalCount=len(links),
        returnedCount=len(returned_links),
        truncated=len(returned_links) < len(links),
        supportingEvidence=_group("supporting", links, returned_links, corpus),
        contradictingEvidence=_group("counterevidence", links, returned_links, corpus),
        contextualEvidence=_group("context", links, returned_links, corpus),
    )


GET_RELATIONSHIP_EVIDENCE_TOOL = ToolDefinition(
    name="get_relationship_evidence",
    version="e2-get-relationship-evidence-v2",
    description=(
        "Return one relationship's endpoints, classification, and evidence "
        "ledger unchanged. This tool never strengthens a relationship beyond "
        "its stored evidenceClassification."
    ),
    input_model=GetRelationshipEvidenceInput,
    output_model=GetRelationshipEvidenceOutput,
    required_capabilities=frozenset({"relationships"}),
    max_result_limit=MAX_TOOL_RESULT_LIMIT,
    execute=_get_relationship_evidence,
    use_when="Use to inspect the exact evidence and stored classification for a known relationship ID.",
    avoid_when="Avoid for multi-edge path traversal, relationship discovery, or causal inference.",
    output_summary=(
        "Canonical EvidenceLink projections grouped by role, with the relationship's raw review "
        "and evidence fields."
    ),
)


# --- trace_relationships ----------------------------------------------------


class TraceRelationshipsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpusId: str = Field(min_length=1)
    startNodeId: str = Field(min_length=1)
    maxDepth: int = Field(default=DEFAULT_PATH_DEPTH, ge=1, le=MAX_PATH_DEPTH)
    maxPaths: int = Field(default=DEFAULT_MAX_PATHS, ge=1)


class RelationshipPathEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relationshipId: str
    fromId: str
    toId: str
    relationshipType: str
    reviewStatus: str
    evidenceClassification: str
    directOrInferred: str
    visibility: str
    evidenceLinkTotalCount: int = Field(ge=0)
    evidenceLinkReturnedCount: int = Field(ge=0)
    evidenceLinksTruncated: bool
    evidenceLinkIds: list[str]
    evidenceLinks: list[EvidenceEntry]


class RelationshipPath(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodeIds: list[str]
    edges: list[RelationshipPathEdge]


class TraceRelationshipsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpusId: str
    startNodeId: str
    paths: list[RelationshipPath]
    returnedCount: int = Field(ge=0)
    truncated: bool


def _path_edge(corpus: InvestigationCorpus, relationship) -> RelationshipPathEdge:
    links = sorted(corpus.get_evidence_links_for(relationship.id), key=lambda link: link.id)
    return RelationshipPathEdge(
        relationshipId=relationship.id,
        fromId=relationship.fromId,
        toId=relationship.toId,
        relationshipType=relationship.relationshipType,
        reviewStatus=relationship.reviewStatus.value,
        evidenceClassification=relationship.evidenceClassification.value,
        directOrInferred=relationship.directOrInferred.value,
        visibility=relationship.visibility.value,
        evidenceLinkTotalCount=len(links),
        evidenceLinkReturnedCount=0,
        evidenceLinksTruncated=bool(links),
        evidenceLinkIds=[],
        evidenceLinks=[],
    )


def _trace_paths(
    corpus: InvestigationCorpus,
    start_node_id: str,
    max_depth: int,
    candidate_limit: int,
) -> list[RelationshipPath]:
    raw_paths: list[tuple[list[str], list[RelationshipPathEdge]]] = []
    frontier: list[tuple[str, set[str], set[str], list[str], list[RelationshipPathEdge]]] = [
        (start_node_id, {start_node_id}, set(), [start_node_id], [])
    ]
    for _depth in range(max_depth):
        next_frontier = []
        for current_node_id, visited_nodes, visited_rel_ids, node_path, edges in frontier:
            neighbors = sorted(
                corpus.get_relationships_touching(current_node_id),
                key=lambda relationship: (
                    relationship.toId if relationship.fromId == current_node_id else relationship.fromId,
                    relationship.id,
                ),
            )
            for relationship in neighbors:
                if relationship.id in visited_rel_ids:
                    continue
                other = (
                    relationship.toId
                    if relationship.fromId == current_node_id
                    else relationship.fromId
                )
                if other in visited_nodes:
                    continue
                new_node_path = node_path + [other]
                new_edges = edges + [_path_edge(corpus, relationship)]
                raw_paths.append((new_node_path, new_edges))
                if len(raw_paths) >= candidate_limit:
                    return _build_paths(raw_paths)
                next_frontier.append(
                    (
                        other,
                        visited_nodes | {other},
                        visited_rel_ids | {relationship.id},
                        new_node_path,
                        new_edges,
                    )
                )
        frontier = next_frontier
        if not frontier:
            break
    return _build_paths(raw_paths)


def _build_paths(
    raw_paths: list[tuple[list[str], list[RelationshipPathEdge]]],
) -> list[RelationshipPath]:
    return [
        RelationshipPath(
            nodeIds=node_path,
            edges=edges,
        )
        for node_path, edges in raw_paths
    ]


def _bound_path_evidence(
    corpus: InvestigationCorpus,
    paths: list[RelationshipPath],
    limit: int,
) -> list[RelationshipPath]:
    budget = CollectionBudget(limit)
    bounded_paths: list[RelationshipPath] = []
    for path in paths:
        bounded_edges: list[RelationshipPathEdge] = []
        for edge in path.edges:
            links = sorted(
                corpus.get_evidence_links_for(edge.relationshipId),
                key=lambda link: link.id,
            )
            returned_links = budget.take(links)
            bounded_edges.append(
                edge.model_copy(
                    update={
                        "evidenceLinkReturnedCount": len(returned_links),
                        "evidenceLinksTruncated": len(returned_links) < len(links),
                        "evidenceLinkIds": [link.id for link in returned_links],
                        "evidenceLinks": [
                            _evidence_entry(corpus, link) for link in returned_links
                        ],
                    }
                )
            )
        bounded_paths.append(path.model_copy(update={"edges": bounded_edges}))
    return bounded_paths


def _trace_relationships(
    tool_input: TraceRelationshipsInput,
    context: ToolExecutionContext,
    corpus: InvestigationCorpus,
) -> TraceRelationshipsOutput:
    if tool_input.maxDepth > MAX_PATH_DEPTH:
        raise PathDepthExceededError(
            f"Requested maxDepth {tool_input.maxDepth} exceeds the hard bound of {MAX_PATH_DEPTH}"
        )
    if tool_input.maxPaths > MAX_PATHS:
        raise ResultLimitExceededError(
            f"Requested maxPaths {tool_input.maxPaths} exceeds the hard bound of {MAX_PATHS}"
        )
    if (
        "maxPaths" in tool_input.model_fields_set
        and tool_input.maxPaths > context.maximumResults
    ):
        raise ResultLimitExceededError(
            f"Requested maxPaths {tool_input.maxPaths} exceeds the context maximum of "
            f"{context.maximumResults}"
        )

    # Confirm the start node exists (claim, relationship, or knowledge state) --
    # get_relationships_touching returns [] for an unknown id rather than
    # raising, so an explicit existence check is required here.
    _require_record_id_exists(corpus, tool_input.startNodeId)

    effective_max_paths = min(tool_input.maxPaths, context.maximumResults)
    candidates = _trace_paths(
        corpus,
        tool_input.startNodeId,
        tool_input.maxDepth,
        effective_max_paths + 1,
    )
    paths = _bound_path_evidence(
        corpus,
        candidates[:effective_max_paths],
        context.maximumResults,
    )
    return TraceRelationshipsOutput(
        corpusId=tool_input.corpusId,
        startNodeId=tool_input.startNodeId,
        paths=paths,
        returnedCount=len(paths),
        truncated=len(candidates) > effective_max_paths,
    )


def _require_record_id_exists(corpus: InvestigationCorpus, record_id: str) -> None:
    from ...corpus.errors import UnknownRecordError

    for getter in (corpus.get_claim, corpus.get_relationship, corpus.get_knowledge_state):
        try:
            getter(record_id)
            return
        except UnknownRecordError:
            continue
    raise UnknownRecordError(f'"{record_id}" is not a known Claim, Relationship, or KnownAtTime record')


TRACE_RELATIONSHIPS_TOOL = ToolDefinition(
    name="trace_relationships",
    version="e2-trace-relationships-v2",
    description=(
        "Trace bounded simple paths over all stored relationship statuses. Every edge preserves "
        "its raw reviewStatus, evidenceClassification, directOrInferred, visibility, and canonical "
        "EvidenceLink projections; path existence does not imply causation or certainty."
    ),
    input_model=TraceRelationshipsInput,
    output_model=TraceRelationshipsOutput,
    required_capabilities=frozenset({"relationships"}),
    max_result_limit=MAX_PATHS,
    execute=_trace_relationships,
    use_when=(
        "Use for deterministic multi-edge traversal from a known claim, relationship, "
        "or knowledge-state node."
    ),
    avoid_when="Avoid for a single relationship's evidence ledger, causal inference, or trust decisions.",
    output_summary=(
        "Stable bounded paths whose edges preserve raw reviewStatus and classification plus "
        "canonical EvidenceLinks."
    ),
)
