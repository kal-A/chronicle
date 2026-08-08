"""Tool execution context and audit-record shapes (Phase E2).

ToolCallRecord is deliberately shaped like ai/models/metadata.py's
ModelCallRecord (toolName/toolVersion <-> providerName/providerVersion,
same attemptCount/startedAt/completedAt/latencyMs/errorType/errorMessage
fields) -- a proven audit-record pattern, reused rather than reinvented.
Never stores private reasoning, because there is none: every tool here is
deterministic software, not a model call.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ...corpus.contracts import EvidenceLinkProjection


DEFAULT_TOOL_RESULT_LIMIT = 8
MAX_TOOL_RESULT_LIMIT = 20
DEFAULT_TOOL_OUTPUT_CHARACTER_LIMIT = 16_000
MAX_TOOL_OUTPUT_CHARACTER_LIMIT = 64_000


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ToolCallStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REJECTED = "rejected"
    UNSUPPORTED = "unsupported"


class ToolExecutionContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpusId: str = Field(min_length=1)
    agentRunId: str | None = None
    requestedByRole: str | None = None
    allowedToolNames: set[str] | None = None
    maximumResults: int = Field(
        default=DEFAULT_TOOL_RESULT_LIMIT,
        ge=1,
        le=MAX_TOOL_RESULT_LIMIT,
    )
    maximumOutputCharacters: int = Field(
        default=DEFAULT_TOOL_OUTPUT_CHARACTER_LIMIT,
        ge=1_000,
        le=MAX_TOOL_OUTPUT_CHARACTER_LIMIT,
    )


class ToolSpec(BaseModel):
    """Compact, serializable description safe to place in a Planner prompt."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str = Field(min_length=1)
    inputSchema: dict[str, Any]
    outputSummary: str = Field(min_length=1)
    requiredCapabilities: list[str]
    maxResultLimit: int | None = Field(default=None, ge=1)
    maxOutputCharacters: int = Field(ge=1_000)
    useWhen: str = Field(min_length=1)
    avoidWhen: str = Field(min_length=1)
    deterministic: bool = True
    currentCorpusOnly: bool = True


class ToolCallRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    toolCallId: str = Field(min_length=1)
    agentRunId: str | None = None

    toolName: str = Field(min_length=1)
    toolVersion: str = Field(min_length=1)
    corpusId: str = Field(min_length=1)

    inputHash: str = Field(min_length=1)
    outputHash: str | None = None

    status: ToolCallStatus
    attemptCount: int = Field(ge=1, default=1)

    startedAt: datetime
    completedAt: datetime | None = None
    latencyMs: float | None = Field(default=None, ge=0)

    resultCount: int | None = None
    errorType: str | None = None
    errorMessage: str | None = None
