"""Public request and bootstrap response contracts for Phase E5."""

from __future__ import annotations

from typing import Callable

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..ai.contracts.run import WorkspaceContextSnapshot
from ..ai.orchestration.statuses import AgentRunStatus
from ..corpus.contracts import CorpusManifest


class QuestionSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=1_000)
    conversationSummary: str | None = Field(default=None, max_length=2_000)
    workspaceContext: WorkspaceContextSnapshot | None = None

    @field_validator("question")
    @classmethod
    def _question_has_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("question must contain text")
        return normalized


class AgentRunAccepted(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    runId: str
    status: AgentRunStatus
    statusUrl: str
    eventsUrl: str

    @classmethod
    def from_run(cls, run_id: str, status: AgentRunStatus) -> "AgentRunAccepted":
        return cls(
            runId=run_id,
            status=status,
            statusUrl=f"/api/agent-runs/{run_id}",
            eventsUrl=f"/api/agent-runs/{run_id}/events",
        )


class CorpusSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    corpusId: str
    title: str
    capabilities: tuple[str, ...]
    knownOmissions: tuple[str, ...]

    @classmethod
    def from_manifest(cls, manifest: CorpusManifest) -> "CorpusSummary":
        return cls(
            corpusId=manifest.corpusId,
            title=manifest.title,
            capabilities=tuple(sorted(manifest.supportedCapabilities)),
            knownOmissions=tuple(manifest.knownOmissions),
        )


RunIdFactory = Callable[[], str]


__all__ = ["AgentRunAccepted", "CorpusSummary", "QuestionSubmission", "RunIdFactory"]
