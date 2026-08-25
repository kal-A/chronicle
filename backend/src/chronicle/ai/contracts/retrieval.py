"""Bounded normalized retrieval records passed from the runner to Analyst."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ...corpus.contracts import EvidenceLinkProjection, PassageSearchResult
from ..tools.contracts import ToolCallRecord
from ..tools.contracts import ToolCallStatus
from ..tools.evidence import FindCounterevidenceOutput, GetClaimEvidenceOutput
from ..tools.knowledge import GetActorKnowledgeStateOutput
from ..tools.map_context import GetMapContextOutput
from ..tools.relationships import GetRelationshipEvidenceOutput, TraceRelationshipsOutput
from ..tools.sources import CompareSourcesOutput, GetSourceMetadataOutput
from ..tools.timeline import GetTimelineContextOutput
from .plan import ToolPurpose

RecordId = Annotated[str, Field(min_length=1, max_length=200)]


ToolOutput = Annotated[
    PassageSearchResult
    | GetSourceMetadataOutput
    | CompareSourcesOutput
    | GetClaimEvidenceOutput
    | FindCounterevidenceOutput
    | GetRelationshipEvidenceOutput
    | TraceRelationshipsOutput
    | GetTimelineContextOutput
    | GetActorKnowledgeStateOutput
    | GetMapContextOutput,
    Field(union_mode="left_to_right"),
]


class ToolResultEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    plannedCallId: str = Field(min_length=1, max_length=100)
    round: int = Field(ge=0, le=1)
    purposeCode: ToolPurpose
    resolvedInputHash: str = Field(min_length=1, max_length=128)
    callRecord: ToolCallRecord
    output: ToolOutput | None = None
    serializedCharacters: int = Field(ge=0, le=6_000)
    returnedCount: int = Field(ge=0, le=4)
    truncated: bool = False

    @model_validator(mode="after")
    def _output_matches_status(self) -> "ToolResultEnvelope":
        succeeded = self.callRecord.status is ToolCallStatus.SUCCEEDED
        if succeeded != (self.output is not None):
            raise ValueError("successful calls require output; unsuccessful calls forbid it")
        if self.callRecord.inputHash != self.resolvedInputHash:
            raise ValueError("resolvedInputHash must match the audited tool input hash")
        return self


class RetrievedReferenceIndex(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidenceLinks: list[EvidenceLinkProjection] = Field(default_factory=list, max_length=16)
    passageIds: tuple[RecordId, ...] = Field(default=(), max_length=16)
    sourceIds: tuple[RecordId, ...] = Field(default=(), max_length=16)
    documentIds: tuple[RecordId, ...] = Field(default=(), max_length=16)
    claimIds: tuple[RecordId, ...] = Field(default=(), max_length=16)
    relationshipIds: tuple[RecordId, ...] = Field(default=(), max_length=16)
    eventIds: tuple[RecordId, ...] = Field(default=(), max_length=16)
    knowledgeStateIds: tuple[RecordId, ...] = Field(default=(), max_length=16)
    placeIds: tuple[RecordId, ...] = Field(default=(), max_length=16)
    mapSceneIds: tuple[RecordId, ...] = Field(default=(), max_length=16)

    @field_validator(
        "passageIds", "sourceIds", "documentIds", "claimIds", "relationshipIds",
        "eventIds", "knowledgeStateIds", "placeIds", "mapSceneIds", mode="before",
    )
    @classmethod
    def _canonical_ids(cls, value):
        return tuple(sorted(set(value or ())))


class RetrievalBundle(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    runId: str = Field(min_length=1, max_length=100)
    planId: str = Field(min_length=1, max_length=100)
    corpusId: str = Field(min_length=1, max_length=200)
    results: list[ToolResultEnvelope] = Field(default_factory=list, max_length=4)
    referenceIndex: RetrievedReferenceIndex = Field(default_factory=RetrievedReferenceIndex)
    totalResultCount: int = Field(default=0, ge=0, le=16)
    serializedCharacters: int = Field(default=0, ge=0, le=14_000)
    truncated: bool = False
    partial: bool = False
    failedCallCount: int = Field(default=0, ge=0, le=4)

    @model_validator(mode="after")
    def _validate_bundle_totals(self) -> "RetrievalBundle":
        if any(
            result.callRecord.agentRunId != self.runId
            or result.callRecord.corpusId != self.corpusId
            for result in self.results
        ):
            raise ValueError("all tool results must be bound to this run and corpus")
        if sum(result.returnedCount for result in self.results) != self.totalResultCount:
            raise ValueError("totalResultCount must equal the result envelope counts")
        if sum(result.serializedCharacters for result in self.results) != self.serializedCharacters:
            raise ValueError("serializedCharacters must equal the result envelope sizes")
        failures = sum(result.callRecord.status is not ToolCallStatus.SUCCEEDED for result in self.results)
        if failures != self.failedCallCount:
            raise ValueError("failedCallCount must equal unsuccessful result envelopes")
        return self
