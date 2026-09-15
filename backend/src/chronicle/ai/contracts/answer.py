"""Critic-approved user answer and typed Chronicle workspace actions."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ...contracts.shared import HistoricalDate
from .analysis import AnalysisCitation, AnswerStatus


class FocusLocationAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    type: Literal["FOCUS_LOCATION"] = "FOCUS_LOCATION"
    locationId: str = Field(min_length=1, max_length=200)


class FocusEventAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    type: Literal["FOCUS_EVENT"] = "FOCUS_EVENT"
    eventId: str = Field(min_length=1, max_length=200)


class SetTimeAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    type: Literal["SET_TIME"] = "SET_TIME"
    date: HistoricalDate


class SetTimeRangeAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    type: Literal["SET_TIME_RANGE"] = "SET_TIME_RANGE"
    range: HistoricalDate


class ActivateLensAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    type: Literal["ACTIVATE_LENS"] = "ACTIVATE_LENS"
    lensId: str = Field(min_length=1, max_length=200)


class HighlightEventsAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    type: Literal["HIGHLIGHT_EVENTS"] = "HIGHLIGHT_EVENTS"
    eventIds: list[str] = Field(min_length=1, max_length=8)


class HighlightRelationshipAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    type: Literal["HIGHLIGHT_RELATIONSHIP"] = "HIGHLIGHT_RELATIONSHIP"
    relationshipId: str = Field(min_length=1, max_length=200)


class ShowSystemPathAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    type: Literal["SHOW_SYSTEM_PATH"] = "SHOW_SYSTEM_PATH"
    pathId: str = Field(min_length=1, max_length=200)


class CompareActorsAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    type: Literal["COMPARE_ACTORS"] = "COMPARE_ACTORS"
    actorIds: list[str] = Field(min_length=2, max_length=8)


class OpenEvidenceAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    type: Literal["OPEN_EVIDENCE"] = "OPEN_EVIDENCE"
    recordId: str = Field(min_length=1, max_length=200)


class OpenSourceAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    type: Literal["OPEN_SOURCE"] = "OPEN_SOURCE"
    sourceId: str = Field(min_length=1, max_length=200)


class ResetViewAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    type: Literal["RESET_VIEW"] = "RESET_VIEW"


AssistantAction = Annotated[
    Union[
        FocusLocationAction,
        FocusEventAction,
        SetTimeAction,
        SetTimeRangeAction,
        ActivateLensAction,
        HighlightEventsAction,
        HighlightRelationshipAction,
        ShowSystemPathAction,
        CompareActorsAction,
        OpenEvidenceAction,
        OpenSourceAction,
        ResetViewAction,
    ],
    Field(discriminator="type"),
]


class AnswerPoint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    statementId: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=1_200)


class AnswerCitation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    statementId: str = Field(min_length=1, max_length=100)
    citation: AnalysisCitation


class AgentAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    answerVersion: str = Field(min_length=1, max_length=80)
    runId: str = Field(min_length=1, max_length=100)
    planId: str = Field(min_length=1, max_length=100)
    corpusId: str = Field(min_length=1, max_length=200)
    status: AnswerStatus
    directAnswer: str = Field(min_length=1, max_length=4_000)
    keyPoints: list[AnswerPoint] = Field(default_factory=list, max_length=8)
    disagreements: list[AnswerPoint] = Field(default_factory=list, max_length=6)
    limitations: list[str] = Field(default_factory=list, max_length=12)
    citations: list[AnswerCitation] = Field(default_factory=list, max_length=32)
    suggestedQuestions: list[str] = Field(default_factory=list, max_length=6)
    actions: list[AssistantAction] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def _validate_status_shape(self) -> "AgentAnswer":
        if self.status is AnswerStatus.NEEDS_MORE_RETRIEVAL:
            raise ValueError("a final answer cannot request more retrieval")
        if self.status is AnswerStatus.ABSTAINED:
            if self.keyPoints or self.disagreements or self.citations or self.actions:
                raise ValueError("an abstained answer cannot expose claims, citations, or actions")
        elif not self.keyPoints:
            raise ValueError("an answered or partial response requires a key point")
        return self


class ActionReferenceIndex(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    locationIds: tuple[str, ...] = ()
    eventIds: tuple[str, ...] = ()
    lensIds: tuple[str, ...] = ()
    relationshipIds: tuple[str, ...] = ()
    pathIds: tuple[str, ...] = ()
    actorIds: tuple[str, ...] = ()
    evidenceRecordIds: tuple[str, ...] = ()
    sourceIds: tuple[str, ...] = ()
    # Scope bounds as HistoricalDate cross-era ordering keys (ADR-005), so a
    # time action in a BC scope can be range-checked without a calendar date.
    earliestKey: tuple[int, int]
    latestKey: tuple[int, int]


class AnswerValidationIssueCode(str, Enum):
    IDENTITY_MISMATCH = "identity_mismatch"
    UNKNOWN_STATEMENT = "unknown_statement"
    UNAPPROVED_ANSWER_TEXT = "unapproved_answer_text"
    INVALID_CITATION = "invalid_citation"
    INVALID_LIMITATION = "invalid_limitation"
    UNKNOWN_ACTION_REFERENCE = "unknown_action_reference"
    UNSUPPORTED_TIME = "unsupported_time"


class AnswerValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: AnswerValidationIssueCode
    message: str = Field(min_length=1, max_length=500)


class AnswerValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    valid: bool
    issues: list[AnswerValidationIssue] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def _valid_means_no_issues(self) -> "AnswerValidationReport":
        if self.valid == bool(self.issues):
            raise ValueError("valid must be true exactly when issues is empty")
        return self
