"""Audit-record models every ModelProvider call produces (Phase E1).

ModelCallRecord is deliberately shaped like workflow/state.py's existing
StageRecord (same attemptCount/startedAt/completedAt/errorType/errorMessage
fields) -- a proven persistence-record pattern, reused rather than
reinvented. This is what makes "agent runs are inspectable" (the Phase E
completion gate) possible without a separate audit subsystem.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ModelCallStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class TokenUsage(BaseModel):
    """Omitted entirely (not zero-filled) on ModelCallRecord when a
    provider's response doesn't report usage -- never fabricated."""

    model_config = ConfigDict(extra="forbid")

    promptTokens: int | None = None
    completionTokens: int | None = None


class CostBasis(str, Enum):
    """What `ProviderCost.amountUsd` actually measures. Deliberately
    narrow: this records what the model *provider* billed for the call,
    never electricity, hardware amortization, or developer time -- those
    are real costs of local inference too, but a different measurement
    this field does not attempt."""

    NO_PROVIDER_CHARGE = "no_provider_charge"
    """A local/deterministic call with no billing relationship at all
    (DeterministicModelProvider, OllamaModelProvider) -- amountUsd is
    always exactly 0, not "unknown" or "free-tier", because there is no
    provider to bill."""

    PROVIDER_BILLED = "provider_billed"
    """A hosted provider actually charged this amount for the call. No
    provider in this codebase uses this basis yet (Phase E's real provider
    is Ollama, per ADR-003) -- reserved for a future paid provider."""


class ProviderCost(BaseModel):
    """Provider-billed inference cost only. See CostBasis for what this
    deliberately does not measure."""

    model_config = ConfigDict(extra="forbid")

    amountUsd: float = Field(ge=0)
    basis: CostBasis


class ModelCallRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    providerName: str = Field(min_length=1)
    providerVersion: str = Field(min_length=1)
    modelName: str = Field(min_length=1)
    modelVersion: str | None = None
    promptVersion: str = Field(min_length=1)
    status: ModelCallStatus
    attemptCount: int = Field(ge=1)
    startedAt: datetime
    completedAt: datetime
    latencyMs: float = Field(ge=0)
    usage: TokenUsage | None = None
    cost: ProviderCost
    errorType: str | None = None
    errorMessage: str | None = None


class ProviderMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    providerName: str = Field(min_length=1)
    providerVersion: str = Field(min_length=1)
    supportsStreaming: bool
    supportsStructuredOutput: bool
    isLocal: bool
    requiresApiKey: bool


class ProviderHealth(BaseModel):
    model_config = ConfigDict(extra="forbid")

    healthy: bool
    checkedAt: datetime = Field(default_factory=utcnow)
    detail: str | None = None
