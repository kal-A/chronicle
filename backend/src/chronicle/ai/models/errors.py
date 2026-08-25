"""Explicit failure taxonomy for ModelProvider implementations (Phase E1).

Every failure path in every provider raises one of these, never a bare
Exception -- mirrors workflow/engine.py's own discipline of a specific
StageExecutionError rather than letting arbitrary exceptions leak
(AGENTS.md §4: deterministic software owns state transitions and error
handling around the "AI"/provider layer, not the reverse).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .metadata import ModelCallRecord


class ModelProviderError(Exception):
    """Base class for every typed provider failure."""

    callRecord: "ModelCallRecord | None"

    def __init__(self, message: str, *, call_record: "ModelCallRecord | None" = None) -> None:
        super().__init__(message)
        self.callRecord = call_record


class ProviderUnavailableError(ModelProviderError):
    """The provider's backing service could not be reached at all (e.g.
    connection refused) -- distinct from a named model being missing."""


class ModelUnavailableError(ModelProviderError):
    """The provider was reachable, but the requested model is not
    available on it (e.g. Ollama returns 404 for an unpulled model)."""


class ProviderTimeoutError(ModelProviderError):
    """The request exceeded its configured timeout."""


class RateLimitError(ModelProviderError):
    """The provider reported a rate or capacity limit."""


class MalformedOutputError(ModelProviderError):
    """The provider's response was not parseable as JSON at all."""


class SchemaValidationError(ModelProviderError):
    """The response parsed as JSON but failed Pydantic validation against
    the requested response_model."""


class RetryExhaustedError(ModelProviderError):
    """A bounded retry policy ran out of attempts. Carries the last
    underlying error as __cause__ so the honest failure reason is never
    hidden behind a generic exhaustion message."""


class InvalidConfigurationError(ModelProviderError):
    """A provider was constructed or invoked with invalid configuration
    (e.g. a malformed base URL)."""


class UnsupportedCapabilityError(ModelProviderError):
    """The requested operation is not supported by this provider (e.g.
    streaming requested from a provider that cannot stream)."""


class RequestCancelledError(ModelProviderError):
    """The caller cancelled the request before it completed."""
