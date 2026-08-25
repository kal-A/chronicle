"""Bounded retry/timeout policy shared by every ModelProvider implementation
(Phase E1). Centralized so retry behavior is identical and independently
testable across providers, rather than each provider inventing its own
policy -- "retries must be bounded, observable, testable."
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..models.errors import (
    MalformedOutputError,
    ModelProviderError,
    RateLimitError,
    SchemaValidationError,
    ProviderTimeoutError,
)

# One initial attempt plus one retry -- a small, bounded, observable ceiling,
# not indefinite retrying. Structured-output recovery on retry: the failing
# response is fed back to the model as concise validation feedback
# (OllamaModelProvider); DeterministicModelProvider counts attempts
# identically so retry-policy tests don't require a live model.
MAX_STRUCTURED_OUTPUT_ATTEMPTS = 2


class AgentExecutionPolicy(BaseModel):
    """Deterministic E3-E4 budgets; models may observe but never alter them."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    maxPlannerModelCalls: int = Field(default=1, ge=1, le=1)
    maxInitialToolCalls: int = Field(default=3, ge=1, le=3)
    maxFollowUpRounds: int = Field(default=1, ge=0, le=1)
    maxFollowUpToolCalls: int = Field(default=1, ge=0, le=1)
    maxTotalToolCalls: int = Field(default=4, ge=1, le=4)
    maxResultsPerTool: int = Field(default=4, ge=1, le=4)
    maxCharactersPerToolOutput: int = Field(default=6_000, ge=1_000, le=6_000)
    maxAggregateRetrievalCharacters: int = Field(default=14_000, ge=1_000, le=14_000)
    maxAggregateResults: int = Field(default=16, ge=1, le=16)
    maxAnalystModelCalls: int = Field(default=2, ge=1, le=2)
    maxCriticModelCalls: int = Field(default=2, ge=1, le=2)
    maxGuideModelCalls: int = Field(default=1, ge=1, le=1)
    maxCritiqueRounds: int = Field(default=2, ge=1, le=2)
    maxStructuredAttempts: int = Field(default=2, ge=1, le=2)
    maxPromptCharacters: int = Field(default=24_000, ge=1_000, le=24_000)
    maxToolSpecCharacters: int = Field(default=18_000, ge=1_000, le=18_000)
    maxStatements: int = Field(default=8, ge=1, le=8)
    maxCitationsPerStatement: int = Field(default=6, ge=1, le=6)
    deadlineSeconds: int = Field(default=300, ge=1, le=300)
    modelContextTokens: int = Field(default=8_192, ge=1_024, le=8_192)
    plannerMaxCompletionTokens: int = Field(default=900, ge=1, le=900)
    analystMaxCompletionTokens: int = Field(default=1_800, ge=1, le=1_800)
    criticMaxCompletionTokens: int = Field(default=1_000, ge=1, le=1_000)
    guideMaxCompletionTokens: int = Field(default=1_400, ge=1, le=1_400)

DEFAULT_REQUEST_TIMEOUT_SECONDS = 60.0

# Failure categories worth retrying: the response was unusable, but asking
# again (with feedback, where possible) has a real chance of succeeding.
# ProviderUnavailableError/ModelUnavailableError/InvalidConfigurationError/
# UnsupportedCapabilityError/RequestCancelledError are deliberately excluded
# -- retrying against a server that's down or a model that doesn't exist
# cannot help, so those propagate immediately instead of burning attempts.
RETRYABLE_ERROR_TYPES: tuple[type[ModelProviderError], ...] = (
    MalformedOutputError,
    SchemaValidationError,
    ProviderTimeoutError,
    RateLimitError,
)
