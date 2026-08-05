"""Bounded retry/timeout policy shared by every ModelProvider implementation
(Phase E1). Centralized so retry behavior is identical and independently
testable across providers, rather than each provider inventing its own
policy -- "retries must be bounded, observable, testable."
"""

from __future__ import annotations

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
