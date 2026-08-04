"""Persisted run/stage records.

Fields per chronicle_phase_c_adjusted_plan.md §7 ("Workflow record" /
"Stage record"), trimmed to what C1's stub pipeline actually populates.
Everything here is plain data — no behavior lives on these models; the
engine (engine.py) owns all state transitions, per AGENTS.md §4's rule that
deterministic software (not the "AI"/provider layer) owns persistence and
state transitions.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

from ..contracts.generated_investigation import SUPPORTED_GENERATED_INVESTIGATION_VERSION
from .stages import RunStatus, StageName, StageRunStatus

WORKFLOW_VERSION = "1.0.0"
STUB_PROVIDER_SET_VERSION = "c1-stub-v1"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: str = Field(min_length=1)


class StageRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stageName: StageName
    stageVersion: str
    providerName: str
    providerVersion: str
    inputHash: str
    outputHash: str
    status: StageRunStatus
    attemptCount: int = Field(ge=1)
    startedAt: datetime
    completedAt: datetime | None = None
    errorType: str | None = None
    errorMessage: str | None = None
    warnings: list[str] = Field(default_factory=list)


class RunRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runId: str
    request: RunRequest
    workflowVersion: str = WORKFLOW_VERSION
    packageSchemaVersion: str = SUPPORTED_GENERATED_INVESTIGATION_VERSION
    providerSetVersion: str = STUB_PROVIDER_SET_VERSION
    createdAt: datetime = Field(default_factory=utcnow)
    updatedAt: datetime = Field(default_factory=utcnow)
    currentStage: StageName | None = None
    status: RunStatus = RunStatus.CREATED
    completedStages: list[StageName] = Field(default_factory=list)
    failedStage: StageName | None = None
    warnings: list[str] = Field(default_factory=list)
    outputPackagePath: str | None = None
    generationReportPath: str | None = None

    def touch(self) -> None:
        self.updatedAt = utcnow()
