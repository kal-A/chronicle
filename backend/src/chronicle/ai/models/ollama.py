"""OllamaModelProvider (Phase E1) -- talks to a local Ollama server over
HTTP. Contains no agent-specific business logic: it only knows how to ask
Ollama for a JSON-schema-constrained response and enforce that schema
through Pydantic on top, per docs/decisions/ADR-003-llm-agent-system-is-
product-core.md's Ollama-first, provider-agnostic decision.

Structured-output recovery policy (bounded, per
orchestration/policies.py): on malformed JSON or schema-invalid output,
retry once with the validation error appended to the conversation as
concise feedback, then raise RetryExhaustedError honestly rather than
looping indefinitely.

The default model (qwen2.5:7b-instruct) and base URL
(CHRONICLE_OLLAMA_BASE_URL, defaulting to the local Ollama daemon) are
configuration, never secrets -- Ollama requires no API key.
"""

from __future__ import annotations

import json
import hashlib
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from ..contracts.structured_generation import StructuredGenerationResult, TextGenerationResult
from ..orchestration.policies import (
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
    MAX_STRUCTURED_OUTPUT_ATTEMPTS,
    RETRYABLE_ERROR_TYPES,
)
from .errors import (
    InvalidConfigurationError,
    MalformedOutputError,
    ModelProviderError,
    ModelUnavailableError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitError,
    RetryExhaustedError,
    SchemaValidationError,
)
from .metadata import (
    CostBasis,
    ModelCallRecord,
    ModelCallStatus,
    ModelGenerationSettings,
    ProviderCost,
    ProviderHealth,
    ProviderMetadata,
    TokenUsage,
)

OLLAMA_PROVIDER_VERSION = "e1-ollama-v1"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:7b-instruct"

# A local Ollama daemon bills nothing per call -- there is no provider to
# invoice. This is genuinely $0, not "unknown": local inference still has
# real hardware, power, and wall-clock time cost (see latencyMs on the same
# record), but those are not what this field measures (docs/ai/model-
# provider-decisions.md). A future hosted provider would report a real
# PROVIDER_BILLED amount here instead.
_NO_PROVIDER_CHARGE = ProviderCost(amountUsd=0.0, basis=CostBasis.NO_PROVIDER_CHARGE)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _input_hash(
    system_prompt: str,
    user_prompt: str,
    response_type: str,
    prompt_version: str,
    settings: ModelGenerationSettings,
) -> str:
    payload = {
        "system": system_prompt,
        "user": user_prompt,
        "responseType": response_type,
        "promptVersion": prompt_version,
        "settings": settings.model_dump(mode="json"),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def resolve_base_url_from_env() -> str:
    return os.environ.get("CHRONICLE_OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL)


def resolve_model_from_env() -> str:
    """The Ollama model tag, overridable via CHRONICLE_OLLAMA_MODEL.

    Lets a larger local model (e.g. qwen2.5:14b-instruct) be swapped in for a
    run without a code change, while defaulting to the qwen2.5:7b-instruct the
    pipeline is tuned against. Not a topic branch -- the model is the same for
    every question."""

    return os.environ.get("CHRONICLE_OLLAMA_MODEL", DEFAULT_MODEL)


def resolve_timeout_from_env(default: float) -> float:
    """The per-request timeout, overridable via CHRONICLE_OLLAMA_TIMEOUT.

    A larger local model generates fewer tokens per second, so a single
    structured call can outrun the timeout tuned for the smaller default. This
    lets the ceiling scale with the model without a code change; an unparseable
    or non-positive value falls back to ``default``."""

    raw = os.environ.get("CHRONICLE_OLLAMA_TIMEOUT")
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if value > 0 else default


@dataclass
class _ChatResponse:
    content: str
    usage: TokenUsage | None


class OllamaModelProvider:
    """Implements the ModelProvider protocol structurally (see
    protocol.py)."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        model: str | None = None,
        provider_version: str = OLLAMA_PROVIDER_VERSION,
        timeout: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
        client: httpx.Client | None = None,
    ) -> None:
        resolved_base_url = base_url or resolve_base_url_from_env()
        if not resolved_base_url.startswith(("http://", "https://")):
            raise InvalidConfigurationError(f"Invalid Ollama base URL: {resolved_base_url!r}")
        resolved_model = resolve_model_from_env() if model is None else model
        if not resolved_model:
            raise InvalidConfigurationError("OllamaModelProvider requires a non-empty model name")

        self._base_url = resolved_base_url.rstrip("/")
        self._model = resolved_model
        self._provider_version = provider_version
        self._timeout = timeout
        self._client = client or httpx.Client(base_url=self._base_url, timeout=timeout)

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
        response_schema: dict[str, Any] | None = None,
        prompt_version: str,
        temperature: float = 0.0,
        generation_settings: ModelGenerationSettings | None = None,
    ) -> StructuredGenerationResult[BaseModel]:
        started_at = _utcnow()
        start_perf = time.perf_counter()
        schema = response_schema or response_model.model_json_schema()
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        last_error: ModelProviderError | None = None
        settings = generation_settings or ModelGenerationSettings(temperature=temperature)
        input_hash = _input_hash(
            system_prompt, user_prompt, json.dumps(schema, sort_keys=True), prompt_version, settings
        )
        accumulated_usage: TokenUsage | None = None

        for attempt in range(1, MAX_STRUCTURED_OUTPUT_ATTEMPTS + 1):
            try:
                chat_response = self._chat(messages=messages, format_schema=schema, settings=settings)
            except ModelProviderError as exc:
                if not isinstance(exc, RETRYABLE_ERROR_TYPES):
                    self._attach_failed_record(
                        exc, prompt_version, input_hash, settings, started_at, start_perf, attempt,
                        accumulated_usage,
                    )
                    raise
                last_error = exc
                continue

            accumulated_usage = _combine_usage(accumulated_usage, chat_response.usage)

            try:
                parsed = json.loads(chat_response.content)
            except json.JSONDecodeError as exc:
                last_error = MalformedOutputError(f"Ollama response was not valid JSON: {exc}")
                messages = _append_retry_feedback(messages, chat_response.content, str(last_error))
                continue

            try:
                value = response_model.model_validate(parsed)
            except ValidationError as exc:
                last_error = SchemaValidationError(str(exc))
                messages = _append_retry_feedback(messages, chat_response.content, str(last_error))
                continue

            completed_at = _utcnow()
            return StructuredGenerationResult(
                value=value,
                modelCall=ModelCallRecord(
                    providerName="ollama",
                    providerVersion=self._provider_version,
                    modelName=self._model,
                    promptVersion=prompt_version,
                    inputHash=input_hash,
                    outputHash=hashlib.sha256(value.model_dump_json().encode("utf-8")).hexdigest(),
                    generationSettings=settings,
                    status=ModelCallStatus.SUCCEEDED,
                    attemptCount=attempt,
                    startedAt=started_at,
                    completedAt=completed_at,
                    latencyMs=(time.perf_counter() - start_perf) * 1000,
                    usage=accumulated_usage,
                    cost=_NO_PROVIDER_CHARGE,
                ),
            )

        error = RetryExhaustedError(
            f"Exhausted {MAX_STRUCTURED_OUTPUT_ATTEMPTS} attempt(s) generating {response_model.__name__} via Ollama"
        )
        self._attach_failed_record(
            error, prompt_version, input_hash, settings, started_at, start_perf,
            MAX_STRUCTURED_OUTPUT_ATTEMPTS, accumulated_usage,
        )
        raise error from last_error

    def generate_text_from_verified_records(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        prompt_version: str,
        generation_settings: ModelGenerationSettings | None = None,
    ) -> TextGenerationResult:
        started_at = _utcnow()
        start_perf = time.perf_counter()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        last_error: ModelProviderError | None = None
        settings = generation_settings or ModelGenerationSettings()
        input_hash = _input_hash(system_prompt, user_prompt, "text", prompt_version, settings)

        for attempt in range(1, MAX_STRUCTURED_OUTPUT_ATTEMPTS + 1):
            try:
                chat_response = self._chat(messages=messages, format_schema=None, settings=settings)
            except ModelProviderError as exc:
                if not isinstance(exc, RETRYABLE_ERROR_TYPES):
                    self._attach_failed_record(
                        exc, prompt_version, input_hash, settings, started_at, start_perf, attempt, None
                    )
                    raise
                last_error = exc
                continue

            completed_at = _utcnow()
            return TextGenerationResult(
                text=chat_response.content,
                modelCall=ModelCallRecord(
                    providerName="ollama",
                    providerVersion=self._provider_version,
                    modelName=self._model,
                    promptVersion=prompt_version,
                    inputHash=input_hash,
                    outputHash=hashlib.sha256(chat_response.content.encode("utf-8")).hexdigest(),
                    generationSettings=settings,
                    status=ModelCallStatus.SUCCEEDED,
                    attemptCount=attempt,
                    startedAt=started_at,
                    completedAt=completed_at,
                    latencyMs=(time.perf_counter() - start_perf) * 1000,
                    usage=chat_response.usage,
                    cost=_NO_PROVIDER_CHARGE,
                ),
            )

        error = RetryExhaustedError(
            f"Exhausted {MAX_STRUCTURED_OUTPUT_ATTEMPTS} attempt(s) generating text via Ollama"
        )
        self._attach_failed_record(
            error, prompt_version, input_hash, settings, started_at, start_perf,
            MAX_STRUCTURED_OUTPUT_ATTEMPTS, None,
        )
        raise error from last_error

    def health_check(self) -> ProviderHealth:
        try:
            response = self._client.get("/api/tags", timeout=min(self._timeout, 5.0))
        except httpx.HTTPError as exc:
            return ProviderHealth(healthy=False, detail=f"Could not reach Ollama at {self._base_url}: {exc}")
        if response.status_code != 200:
            return ProviderHealth(healthy=False, detail=f"Ollama returned HTTP {response.status_code}")
        return ProviderHealth(healthy=True, detail=f"Ollama reachable at {self._base_url}")

    @property
    def provider_metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            providerName="ollama",
            providerVersion=self._provider_version,
            supportsStreaming=True,
            supportsStructuredOutput=True,
            isLocal=True,
            requiresApiKey=False,
        )

    def _chat(
        self,
        *,
        messages: list[dict[str, str]],
        format_schema: dict[str, Any] | None,
        settings: ModelGenerationSettings,
    ) -> _ChatResponse:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": settings.temperature},
        }
        if settings.contextTokens is not None:
            payload["options"]["num_ctx"] = settings.contextTokens
        if settings.maxCompletionTokens is not None:
            payload["options"]["num_predict"] = settings.maxCompletionTokens
        if format_schema is not None:
            payload["format"] = format_schema

        try:
            response = self._client.post("/api/chat", json=payload, timeout=self._timeout)
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(f"Ollama request timed out after {self._timeout}s") from exc
        except httpx.ConnectError as exc:
            raise ProviderUnavailableError(f"Could not connect to Ollama at {self._base_url}") from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(f"Ollama request failed: {exc}") from exc

        if response.status_code == 404:
            raise ModelUnavailableError(f"Model {self._model!r} is not available on this Ollama server")
        if response.status_code == 429:
            raise RateLimitError("Ollama reported a rate/capacity limit")
        if response.status_code >= 500:
            raise ProviderUnavailableError(f"Ollama server error: HTTP {response.status_code}")
        if response.status_code != 200:
            raise ProviderUnavailableError(f"Unexpected Ollama response: HTTP {response.status_code}")

        try:
            body = response.json()
        except ValueError as exc:
            raise MalformedOutputError("Ollama's response envelope was not valid JSON") from exc

        content = body.get("message", {}).get("content")
        if not isinstance(content, str):
            raise MalformedOutputError("Ollama response was missing message.content")

        return _ChatResponse(content=content, usage=_extract_usage(body))

    def _attach_failed_record(
        self,
        error: ModelProviderError,
        prompt_version: str,
        input_hash: str,
        settings: ModelGenerationSettings,
        started_at: datetime,
        start_perf: float,
            attempt: int,
        usage: TokenUsage | None,
    ) -> None:
        completed_at = _utcnow()
        error.callRecord = ModelCallRecord(
            providerName="ollama",
            providerVersion=self._provider_version,
            modelName=self._model,
            promptVersion=prompt_version,
            inputHash=input_hash,
            generationSettings=settings,
            status=ModelCallStatus.FAILED,
            attemptCount=attempt,
            startedAt=started_at,
            completedAt=completed_at,
            latencyMs=(time.perf_counter() - start_perf) * 1000,
            usage=usage,
            cost=_NO_PROVIDER_CHARGE,
            errorType=type(error).__name__,
            errorMessage=str(error)[:500],
        )


def _extract_usage(body: dict[str, Any]) -> TokenUsage | None:
    prompt_tokens = body.get("prompt_eval_count")
    completion_tokens = body.get("eval_count")
    if prompt_tokens is None and completion_tokens is None:
        return None
    return TokenUsage(promptTokens=prompt_tokens, completionTokens=completion_tokens)


def _combine_usage(current: TokenUsage | None, addition: TokenUsage | None) -> TokenUsage | None:
    if current is None:
        return addition
    if addition is None:
        return current

    def combine(left: int | None, right: int | None) -> int | None:
        if left is None and right is None:
            return None
        return (left or 0) + (right or 0)

    return TokenUsage(
        promptTokens=combine(current.promptTokens, addition.promptTokens),
        completionTokens=combine(current.completionTokens, addition.completionTokens),
    )


def _append_retry_feedback(
    messages: list[dict[str, str]], previous_content: str, feedback: str
) -> list[dict[str, str]]:
    return [
        *messages,
        {"role": "assistant", "content": previous_content},
        {
            "role": "user",
            "content": (
                f"Your previous response was invalid: {feedback}. "
                "Respond again with only valid JSON that matches the required schema exactly."
            ),
        },
    ]
