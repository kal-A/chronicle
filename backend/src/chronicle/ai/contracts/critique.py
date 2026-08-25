"""Historical Critic decisions and their deterministic validation report."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .plan import PlannedToolCall


class CriticVerdict(str, Enum):
    APPROVE = "approve"
    APPROVE_WITH_DOWNGRADES = "approve_with_downgrades"
    RETRIEVE_MORE = "retrieve_more"
    REJECT = "reject"
    ABSTAIN = "abstain"


class StatementDowngrade(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    statementId: str = Field(min_length=1, max_length=100)
    revisedText: str = Field(min_length=1, max_length=1_200)
    limitations: list[str] = Field(min_length=1, max_length=4)


class StatementRejection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    statementId: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=500)


class CriticDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    criticVersion: str = Field(min_length=1, max_length=80)
    runId: str = Field(min_length=1, max_length=100)
    planId: str = Field(min_length=1, max_length=100)
    corpusId: str = Field(min_length=1, max_length=200)
    verdict: CriticVerdict
    acceptedStatementIds: list[str] = Field(default_factory=list, max_length=8)
    downgradedStatements: list[StatementDowngrade] = Field(default_factory=list, max_length=8)
    rejectedStatements: list[StatementRejection] = Field(default_factory=list, max_length=8)
    additionalToolCalls: list[PlannedToolCall] = Field(default_factory=list, max_length=1)
    limitationsToSurface: list[str] = Field(default_factory=list, max_length=8)
    rationaleSummary: str = Field(min_length=1, max_length=800)

    @model_validator(mode="after")
    def _validate_verdict_shape(self) -> "CriticDecision":
        accepted = self.acceptedStatementIds
        downgraded = [item.statementId for item in self.downgradedStatements]
        rejected = [item.statementId for item in self.rejectedStatements]
        all_ids = accepted + downgraded + rejected
        if len(all_ids) != len(set(all_ids)):
            raise ValueError("statement dispositions must be unique and non-overlapping")
        if self.verdict is CriticVerdict.RETRIEVE_MORE:
            if len(self.additionalToolCalls) != 1:
                raise ValueError("retrieve_more requires exactly one additional tool call")
            if all_ids:
                raise ValueError("retrieve_more defers statement disposition until reanalysis")
        elif self.additionalToolCalls:
            raise ValueError("additional tool calls are only valid for retrieve_more")
        if self.verdict is CriticVerdict.APPROVE:
            if not accepted:
                raise ValueError("approve requires at least one accepted statement")
            if downgraded or rejected:
                raise ValueError("approve cannot downgrade or reject statements")
        if self.verdict is CriticVerdict.APPROVE_WITH_DOWNGRADES and not downgraded:
            raise ValueError("approve_with_downgrades requires a downgraded statement")
        if self.verdict is CriticVerdict.REJECT and not rejected:
            raise ValueError("reject requires at least one rejected statement")
        if self.verdict is CriticVerdict.ABSTAIN and all_ids:
            raise ValueError("abstain cannot expose statement dispositions")
        return self


class CriticValidationIssueCode(str, Enum):
    IDENTITY_MISMATCH = "identity_mismatch"
    UNGROUNDED_ANALYSIS = "ungrounded_analysis"
    UNKNOWN_STATEMENT = "unknown_statement"
    INCOMPLETE_REVIEW = "incomplete_review"
    INVALID_TOOL_CALL = "invalid_tool_call"


class CriticValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: CriticValidationIssueCode
    statementId: str | None = Field(default=None, max_length=100)
    message: str = Field(min_length=1, max_length=500)


class CriticValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    valid: bool
    issues: list[CriticValidationIssue] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def _valid_means_no_issues(self) -> "CriticValidationReport":
        if self.valid == bool(self.issues):
            raise ValueError("valid must be true exactly when issues is empty")
        return self
