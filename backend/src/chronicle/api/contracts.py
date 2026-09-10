"""Public request and bootstrap response contracts for Phase E5."""

from __future__ import annotations

from datetime import date
from typing import Callable

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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


class TopicBuildSubmission(BaseModel):
    """Ask Chronicle to acquire sources for an arbitrary topic, build a corpus,
    and immediately investigate a question over it. Scope (geography + dates) is
    caller-supplied for now; a later LLM scope-resolution stage will infer it."""

    model_config = ConfigDict(extra="forbid")

    topic: str = Field(min_length=1, max_length=300)
    question: str = Field(min_length=1, max_length=1_000)
    geographicScope: list[str] = Field(min_length=1, max_length=12)
    dateEarliest: date
    dateLatest: date
    terms: list[str] | None = Field(default=None, max_length=24)
    maxSources: int = Field(default=8, ge=1, le=24)

    @field_validator("topic", "question")
    @classmethod
    def _has_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value must contain text")
        return normalized

    @field_validator("geographicScope")
    @classmethod
    def _scope_entries_have_text(cls, value: list[str]) -> list[str]:
        cleaned = [entry.strip() for entry in value if entry.strip()]
        if not cleaned:
            raise ValueError("geographicScope must contain at least one non-empty entry")
        return cleaned

    @model_validator(mode="after")
    def _dates_ordered(self) -> "TopicBuildSubmission":
        if self.dateEarliest > self.dateLatest:
            raise ValueError("dateEarliest must not be after dateLatest")
        return self


class CorpusBuildAccepted(BaseModel):
    """The built corpus plus the investigation run started over it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    corpusId: str
    alreadyBuilt: bool
    discovered: int
    acquired: int
    passages: int
    run: AgentRunAccepted
    corpusUrl: str

    @classmethod
    def from_build(
        cls,
        *,
        corpus_id: str,
        already_built: bool,
        discovered: int,
        acquired: int,
        passages: int,
        run: AgentRunAccepted,
    ) -> "CorpusBuildAccepted":
        return cls(
            corpusId=corpus_id,
            alreadyBuilt=already_built,
            discovered=discovered,
            acquired=acquired,
            passages=passages,
            run=run,
            corpusUrl=f"/api/corpora/{corpus_id}",
        )


class ScopeResolutionRequest(BaseModel):
    """Ask Chronicle to propose an acquisition scope from a bare question."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=1_000)

    @field_validator("question")
    @classmethod
    def _question_has_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must contain text")
        return value


class ScopeResolutionResponse(BaseModel):
    """A model-proposed scope for human review, or a manual-entry fallback.

    ``resolved`` is False when the local model could not propose a valid scope;
    the scope fields are then null and the frontend collects them manually.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    resolved: bool
    topic: str | None = None
    interpretedQuestion: str | None = None
    geographicScope: list[str] | None = None
    dateEarliest: date | None = None
    dateLatest: date | None = None
    terms: list[str] | None = None
    message: str | None = None


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


__all__ = [
    "AgentRunAccepted",
    "CorpusBuildAccepted",
    "CorpusSummary",
    "QuestionSubmission",
    "RunIdFactory",
    "TopicBuildSubmission",
]
