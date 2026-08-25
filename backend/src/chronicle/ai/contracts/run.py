"""Immutable run request/snapshot plus mutable auditable run-state records."""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..models.metadata import ModelCallRecord
from ..orchestration.statuses import AgentRunStatus
from ..tools.contracts import ToolCallRecord
from .analysis import AnalysisDraft, GroundingValidationReport
from .answer import AgentAnswer, AnswerValidationReport
from .critique import CriticDecision, CriticValidationReport
from .plan import InvestigationPlan
from .retrieval import RetrievalBundle

ShortText = Annotated[str, Field(min_length=1, max_length=500)]
CapabilityName = Annotated[str, Field(min_length=1, max_length=100)]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SelectedRecordType(str, Enum):
    CLAIM = "claim"
    RELATIONSHIP = "relationship"
    EVENT = "event"
    ENTITY = "entity"
    KNOWLEDGE_STATE = "knowledge_state"
    SOURCE = "source"
    DOCUMENT = "document"
    PASSAGE = "passage"
    PLACE = "place"
    MAP_SCENE = "map_scene"


class SelectedRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    recordType: SelectedRecordType
    recordId: str = Field(min_length=1, max_length=200)


class DateRangeSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    earliest: date | None = None
    latest: date | None = None

    @model_validator(mode="after")
    def _validate_bounds(self) -> "DateRangeSnapshot":
        if self.earliest is None and self.latest is None:
            raise ValueError("at least one date bound is required")
        if self.earliest is not None and self.latest is not None and self.earliest > self.latest:
            raise ValueError("earliest must not be after latest")
        return self


class WorkspaceContextSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    sceneId: str | None = Field(default=None, max_length=200)
    selectedLensId: str | None = Field(default=None, max_length=200)
    selectedDateRange: DateRangeSnapshot | None = None
    selectedRecords: tuple[SelectedRecord, ...] = Field(default=(), max_length=12)


class InvestigationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    runId: str = Field(min_length=1, max_length=100)
    corpusId: str = Field(min_length=1, max_length=200)
    userQuestion: str = Field(min_length=1, max_length=1_000)
    conversationSummary: str | None = Field(default=None, max_length=2_000)
    workspaceContext: WorkspaceContextSnapshot | None = None


class CorpusSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    corpusId: str = Field(min_length=1, max_length=200)
    packageId: str = Field(min_length=1, max_length=200)
    packageHash: str = Field(min_length=1, max_length=128)
    packageRevision: int = Field(gt=0)
    schemaVersion: str = Field(min_length=1, max_length=100)
    capabilities: tuple[CapabilityName, ...] = Field(default=(), max_length=32)
    knownOmissions: tuple[ShortText, ...] = Field(default=(), max_length=32)

    @field_validator("capabilities", mode="before")
    @classmethod
    def _canonical_capabilities(cls, value):
        return tuple(sorted(set(value or ())))


class AgentStageName(str, Enum):
    PLANNER = "planner"
    RETRIEVAL = "retrieval"
    ANALYST = "analyst"
    CRITIC = "critic"
    GUIDE = "guide"


class AgentStageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    ABSTAINED = "abstained"
    INTERRUPTED = "interrupted"
    FAILED = "failed"
    REJECTED = "rejected"


class PromptMeasurement(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    promptCharacters: int = Field(ge=0)
    schemaCharacters: int = Field(default=0, ge=0)
    toolSpecCharacters: int = Field(default=0, ge=0)


class ArtifactReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    artifactKind: str = Field(min_length=1, max_length=80)
    relativePath: str = Field(min_length=1, max_length=300)
    contentHash: str = Field(min_length=1, max_length=128)
    serializedCharacters: int = Field(ge=0)


class AgentStageRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    runId: str = Field(min_length=1, max_length=100)
    stageName: AgentStageName
    round: int = Field(default=0, ge=0, le=1)
    status: AgentStageStatus = AgentStageStatus.PENDING
    startedAt: datetime | None = None
    completedAt: datetime | None = None
    latencyMs: float | None = Field(default=None, ge=0)
    inputHash: str | None = Field(default=None, max_length=128)
    outputHash: str | None = Field(default=None, max_length=128)
    promptMeasurement: PromptMeasurement | None = None
    modelCalls: list[ModelCallRecord] = Field(default_factory=list, max_length=2)
    toolCalls: list[ToolCallRecord] = Field(default_factory=list, max_length=4)
    errors: list[ShortText] = Field(default_factory=list, max_length=8)
    artifacts: list[ArtifactReference] = Field(default_factory=list, max_length=8)
    validationIssues: list[ShortText] = Field(default_factory=list, max_length=50)


class AgentRunRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    runId: str = Field(min_length=1, max_length=100)
    request: InvestigationRequest
    corpusSnapshot: CorpusSnapshot
    runtimeVersion: str = Field(default="e5-agent-runtime-v1", min_length=1, max_length=100)
    createdAt: datetime = Field(default_factory=utcnow)
    updatedAt: datetime = Field(default_factory=utcnow)
    status: AgentRunStatus = AgentRunStatus.CREATED
    stages: list[AgentStageRecord] = Field(default_factory=list, max_length=8)
    plan: InvestigationPlan | None = None
    retrievalBundle: RetrievalBundle | None = None
    analysisDraft: AnalysisDraft | None = None
    groundingValidation: GroundingValidationReport | None = None
    criticDecisions: list[CriticDecision] = Field(default_factory=list, max_length=3)
    criticValidations: list[CriticValidationReport] = Field(default_factory=list, max_length=3)
    finalAnswer: AgentAnswer | None = None
    answerValidation: AnswerValidationReport | None = None
    modelCalls: list[ModelCallRecord] = Field(default_factory=list, max_length=6)
    toolCalls: list[ToolCallRecord] = Field(default_factory=list, max_length=4)
    warnings: list[ShortText] = Field(default_factory=list, max_length=16)
    abstentionReason: str | None = Field(default=None, max_length=800)
    errorMessage: str | None = Field(default=None, max_length=800)

    def touch(self) -> None:
        self.updatedAt = utcnow()

    @model_validator(mode="after")
    def _validate_identity(self) -> "AgentRunRecord":
        if self.request.runId != self.runId:
            raise ValueError("request runId must match record runId")
        if self.request.corpusId != self.corpusSnapshot.corpusId:
            raise ValueError("request corpusId must match corpus snapshot")
        if self.plan is not None and (
            self.plan.runId != self.runId or self.plan.corpusId != self.request.corpusId
        ):
            raise ValueError("plan identity must match the run")
        if self.retrievalBundle is not None and (
            self.retrievalBundle.runId != self.runId
            or self.retrievalBundle.corpusId != self.request.corpusId
            or (self.plan is not None and self.retrievalBundle.planId != self.plan.planId)
        ):
            raise ValueError("retrieval bundle identity must match the run and plan")
        if self.analysisDraft is not None and (
            self.analysisDraft.runId != self.runId
            or self.analysisDraft.corpusId != self.request.corpusId
            or (self.plan is not None and self.analysisDraft.planId != self.plan.planId)
        ):
            raise ValueError("analysis identity must match the run and plan")
        for decision in self.criticDecisions:
            if (
                decision.runId != self.runId
                or decision.corpusId != self.request.corpusId
                or (self.plan is not None and decision.planId != self.plan.planId)
            ):
                raise ValueError("critic decision identity must match the run and plan")
        if self.criticValidations and len(self.criticValidations) != len(self.criticDecisions):
            raise ValueError("critic validations must correspond one-to-one with decisions")
        if self.finalAnswer is not None and (
            self.finalAnswer.runId != self.runId
            or self.finalAnswer.corpusId != self.request.corpusId
            or (self.plan is not None and self.finalAnswer.planId != self.plan.planId)
        ):
            raise ValueError("final answer identity must match the run and plan")
        if (self.finalAnswer is None) != (self.answerValidation is None):
            raise ValueError("final answer and answer validation must be persisted together")
        return self
