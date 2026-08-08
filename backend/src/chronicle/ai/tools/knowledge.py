"""Actor knowledge-state retrieval without inferring awareness from availability."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ...contracts.shared import HistoricalDate
from ...corpus.contracts import EvidenceLinkProjection
from ...corpus.protocol import InvestigationCorpus
from .contracts import MAX_TOOL_RESULT_LIMIT, ToolExecutionContext
from .evidence import ToolRecordId, _evidence_projection
from .registry import ToolDefinition


class GetActorKnowledgeStateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpusId: ToolRecordId
    entityId: ToolRecordId


class KnowledgeStateEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knowledgeStateId: str
    fact: str
    asOfDate: HistoricalDate
    awareness: str
    directOrInferred: str | None
    directOrInferredAvailability: Literal["recorded", "not-recorded"]
    reviewStatus: str
    visibility: str
    evidenceTotalCount: int = Field(ge=0)
    evidenceReturnedCount: int = Field(ge=0)
    evidenceLinks: list[EvidenceLinkProjection]
    evidenceTruncated: bool


class GetActorKnowledgeStateOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpusId: str
    packageId: str
    packageRevision: int = Field(gt=0)
    packageGeneratedAt: datetime
    entityId: str
    availability: Literal["records-available", "insufficient-data"]
    dataAvailable: bool
    totalCount: int = Field(ge=0)
    returnedCount: int = Field(ge=0)
    knowledgeStates: list[KnowledgeStateEntry]
    truncated: bool
    insufficientDataReason: str | None


@dataclass
class _EvidenceBudget:
    remaining: int

    def take(self, links: list) -> list:
        returned = links[: self.remaining]
        self.remaining -= len(returned)
        return returned


def _knowledge_entry(
    state,
    evidence_budget: _EvidenceBudget,
    corpus: InvestigationCorpus,
) -> KnowledgeStateEntry:
    all_links = sorted(
        corpus.get_evidence_links_for(state.id),
        key=lambda link: link.id,
    )
    returned_links = evidence_budget.take(all_links)
    return KnowledgeStateEntry(
        knowledgeStateId=state.id,
        fact=state.fact,
        asOfDate=state.asOfDate,
        awareness=state.awareness.value,
        # GeneratedKnownAtTime does not carry directOrInferred. Expose that
        # absence explicitly instead of silently inventing a certainty class.
        directOrInferred=None,
        directOrInferredAvailability="not-recorded",
        reviewStatus=state.reviewStatus.value,
        visibility=state.visibility.value,
        evidenceTotalCount=len(all_links),
        evidenceReturnedCount=len(returned_links),
        evidenceLinks=[_evidence_projection(corpus, link) for link in returned_links],
        evidenceTruncated=len(returned_links) < len(all_links),
    )


def _get_actor_knowledge_state(
    tool_input: GetActorKnowledgeStateInput,
    context: ToolExecutionContext,
    corpus: InvestigationCorpus,
) -> GetActorKnowledgeStateOutput:
    entity = corpus.get_entity(tool_input.entityId)
    states = corpus.get_knowledge_states_for(entity.id)
    returned_states = states[: context.maximumResults]
    investigation = corpus.get_investigation()
    evidence_budget = _EvidenceBudget(context.maximumResults)

    if not states:
        reason = (
            f'Corpus "{corpus.corpus_id}" has no KnownAtTime records for entity '
            f'"{entity.id}" -- insufficient data to answer what this actor knew and when.'
        )
        availability = "insufficient-data"
    else:
        reason = None
        availability = "records-available"

    return GetActorKnowledgeStateOutput(
        corpusId=tool_input.corpusId,
        packageId=investigation.packageId,
        packageRevision=investigation.packageRevision,
        packageGeneratedAt=investigation.generatedAt,
        entityId=entity.id,
        availability=availability,
        dataAvailable=bool(states),
        totalCount=len(states),
        returnedCount=len(returned_states),
        knowledgeStates=[_knowledge_entry(state, evidence_budget, corpus) for state in returned_states],
        truncated=len(returned_states) < len(states),
        insufficientDataReason=reason,
    )


GET_ACTOR_KNOWLEDGE_STATE_TOOL = ToolDefinition(
    name="get_actor_knowledge_state",
    version="e2-get-actor-knowledge-state-v2",
    description=(
        "Return stored KnownAtTime records for one entity, preserving known/not-yet-known, "
        "review, visibility, and evidence scope. Record availability is not a support verdict."
    ),
    input_model=GetActorKnowledgeStateInput,
    output_model=GetActorKnowledgeStateOutput,
    required_capabilities=frozenset(),
    max_result_limit=MAX_TOOL_RESULT_LIMIT,
    execute=_get_actor_knowledge_state,
    use_when="Use to inspect explicit KnownAtTime records for a known person or institution ID.",
    avoid_when="Avoid inferring awareness from publication, message existence, or general information availability.",
    output_summary="Bounded knowledge-state records with explicit data availability and EvidenceLink provenance.",
)
