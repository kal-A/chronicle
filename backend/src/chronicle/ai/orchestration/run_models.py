"""AgentRunRecord (Phase E1 scaffolding) -- the persistence-record shape a
future agent-run runner (E3+) will populate. Deliberately not wired to any
runner yet: no Planner/Analyst/Critic/Guide exists in this slice. Shaped
like workflow/state.py's RunRecord (same createdAt/updatedAt/touch()
pattern) -- a proven persistence-record pattern, reused rather than
reinvented, per docs/decisions/ADR-003-llm-agent-system-is-product-core.md's
note that Phase E's orchestration reuses the *pattern* from engine.py, not
its fixed-linear-pipeline code path.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

from ..models.metadata import ModelCallRecord
from .statuses import AgentRunStatus

AGENT_RUNTIME_VERSION = "e1-agent-runtime-v1"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AgentRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)
    investigationPackageId: str = Field(min_length=1)
    sceneId: str = Field(min_length=1)


class AgentRunRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runId: str
    request: AgentRunRequest
    runtimeVersion: str = AGENT_RUNTIME_VERSION
    createdAt: datetime = Field(default_factory=utcnow)
    updatedAt: datetime = Field(default_factory=utcnow)
    status: AgentRunStatus = AgentRunStatus.CREATED
    modelCalls: list[ModelCallRecord] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    abstentionReason: str | None = None
    errorMessage: str | None = None

    def touch(self) -> None:
        self.updatedAt = utcnow()
