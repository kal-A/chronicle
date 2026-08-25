"""Structured Analyst output and grounding-report contracts for Phase E3."""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ...contracts.enums import (
    Awareness,
    EvidenceClassification,
    EvidenceLinkRole,
    LocationPrecision,
)
from ...corpus.contracts import PassageDateRole
from .plan import PlannedToolCall

ShortText = Annotated[str, Field(min_length=1, max_length=500)]
RecordReference = Annotated[str, Field(min_length=1, max_length=200)]


class AnswerStatus(str, Enum):
    ANSWERED = "answered"
    PARTIAL = "partial"
    ABSTAINED = "abstained"
    NEEDS_MORE_RETRIEVAL = "needs_more_retrieval"


class StatementKind(str, Enum):
    FACT = "fact"
    CHRONOLOGY = "chronology"
    RELATIONSHIP = "relationship"
    KNOWLEDGE = "knowledge"
    SOURCE_COMPARISON = "source_comparison"
    INTERPRETATION = "interpretation"


class StatementForm(str, Enum):
    EXTRACTED_RECORD = "extracted_record"
    EVIDENCE_SYNTHESIS = "evidence_synthesis"


class DirectnessAssessment(str, Enum):
    DIRECT = "direct"
    INFERRED = "inferred"
    NOT_RECORDED = "not_recorded"


class AnalysisCitation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    toolCallId: str = Field(min_length=1, max_length=100)
    evidenceLinkId: str | None = Field(default=None, max_length=200)
    passageId: str | None = Field(default=None, max_length=200)
    sourceId: str | None = Field(default=None, max_length=200)
    targetType: str | None = Field(default=None, max_length=80)
    targetId: str | None = Field(default=None, max_length=200)
    role: EvidenceLinkRole | None = None

    @model_validator(mode="after")
    def _require_evidence_reference(self) -> "AnalysisCitation":
        if not any((self.evidenceLinkId, self.passageId, self.sourceId, self.targetId)):
            raise ValueError("citation must identify at least one retrieved record")
        return self


class AnalysisStatement(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    statementId: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=1_200)
    statementKind: StatementKind
    statementForm: StatementForm
    basisRecordRefs: list[RecordReference] = Field(default_factory=list, max_length=12)
    citations: list[AnalysisCitation] = Field(min_length=1, max_length=6)
    directness: DirectnessAssessment
    evidenceClassification: EvidenceClassification | None = None
    geographicPrecision: LocationPrecision | None = None
    knowledgeAwareness: Awareness | None = None
    temporalRoles: list[PassageDateRole] = Field(default_factory=list, max_length=5)
    temporalQualifications: list[ShortText] = Field(default_factory=list, max_length=4)
    limitations: list[ShortText] = Field(default_factory=list, max_length=4)
    requiresHumanReview: bool = True

    @model_validator(mode="after")
    def _synthesis_is_inferred(self) -> "AnalysisStatement":
        if self.statementForm is StatementForm.EVIDENCE_SYNTHESIS and self.directness is not DirectnessAssessment.INFERRED:
            raise ValueError("evidence synthesis must be marked inferred")
        if self.statementKind is StatementKind.KNOWLEDGE and self.knowledgeAwareness is None:
            raise ValueError("knowledge statements require structured knowledgeAwareness")
        if self.statementKind is not StatementKind.KNOWLEDGE and self.knowledgeAwareness is not None:
            raise ValueError("knowledgeAwareness is only valid for knowledge statements")
        return self


class AnalysisDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    analysisVersion: str = Field(min_length=1, max_length=80)
    runId: str = Field(min_length=1, max_length=100)
    planId: str = Field(min_length=1, max_length=100)
    corpusId: str = Field(min_length=1, max_length=200)
    status: AnswerStatus
    statements: list[AnalysisStatement] = Field(default_factory=list, max_length=8)
    disagreements: list[ShortText] = Field(default_factory=list, max_length=6)
    counterevidenceSummary: list[ShortText] = Field(default_factory=list, max_length=6)
    limitations: list[ShortText] = Field(default_factory=list, max_length=8)
    unansweredQuestions: list[ShortText] = Field(default_factory=list, max_length=6)
    suggestedFollowUpToolCall: PlannedToolCall | None = None
    abstentionReason: str | None = Field(default=None, max_length=800)

    @model_validator(mode="after")
    def _validate_status(self) -> "AnalysisDraft":
        if self.status is AnswerStatus.ABSTAINED and not self.abstentionReason:
            raise ValueError("abstained analysis requires abstentionReason")
        if self.status is AnswerStatus.ABSTAINED and self.statements:
            raise ValueError("abstained analysis cannot contain statements")
        if self.status is AnswerStatus.ANSWERED and not self.statements:
            raise ValueError("answered analysis requires at least one statement")
        if self.status is AnswerStatus.NEEDS_MORE_RETRIEVAL and self.suggestedFollowUpToolCall is None:
            raise ValueError("needs_more_retrieval requires one suggested tool call")
        if self.status is not AnswerStatus.NEEDS_MORE_RETRIEVAL and self.suggestedFollowUpToolCall is not None:
            raise ValueError("follow-up tool call is only valid for needs_more_retrieval")
        return self


class GroundingIssueCode(str, Enum):
    UNKNOWN_TOOL_CALL = "unknown_tool_call"
    UNKNOWN_RECORD = "unknown_record"
    CITATION_MISMATCH = "citation_mismatch"
    MISSING_CITATION = "missing_citation"
    INVALID_DIRECTNESS = "invalid_directness"
    STATUS_MISMATCH = "status_mismatch"


class GroundingIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    code: GroundingIssueCode
    statementId: str | None = Field(default=None, max_length=100)
    message: str = Field(min_length=1, max_length=500)


class GroundingValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    valid: bool
    issues: list[GroundingIssue] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def _valid_means_no_issues(self) -> "GroundingValidationReport":
        if self.valid == bool(self.issues):
            raise ValueError("valid must be true exactly when issues is empty")
        return self
