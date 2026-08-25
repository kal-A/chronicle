"""The provider-agnostic ModelProvider protocol (Phase E1).

A structural typing.Protocol, not a base class -- DeterministicModelProvider
and OllamaModelProvider share no implementation, only this shape, so a
future local/hosted/fine-tuned provider can be added without touching
either existing one or any agent that consumes the protocol (docs/decisions/
ADR-003-llm-agent-system-is-product-core.md).

Synchronous by design: every existing part of this codebase (engine.py, all
providers, the CLI) is synchronous. Async is deferred to Phase E5, where
FastAPI can run a sync provider call in a threadpool per its own standard
pattern for sync dependencies -- not a design gap, a deliberate sequencing
choice.
"""

from __future__ import annotations

from typing import Any, Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

from .metadata import ModelGenerationSettings, ProviderHealth, ProviderMetadata
from ..contracts.structured_generation import StructuredGenerationResult, TextGenerationResult

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class ModelProvider(Protocol):
    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        response_schema: dict[str, Any] | None = None,
        prompt_version: str,
        temperature: float = 0.0,
        generation_settings: ModelGenerationSettings | None = None,
    ) -> StructuredGenerationResult[T]:
        """Generate a response that validates against response_model.

        Implementations must raise chronicle.ai.models.errors.* on failure,
        never a bare Exception -- see that module's docstring.
        """
        ...

    def generate_text_from_verified_records(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        prompt_version: str,
        generation_settings: ModelGenerationSettings | None = None,
    ) -> TextGenerationResult:
        """Ordinary (non-schema-constrained) text generation. Named for its
        one sanctioned use per AGENTS.md §4: composing user-facing prose
        from already-verified records, never a substitute for structured
        extraction/proposal output."""
        ...

    def health_check(self) -> ProviderHealth:
        ...

    @property
    def provider_metadata(self) -> ProviderMetadata:
        ...
