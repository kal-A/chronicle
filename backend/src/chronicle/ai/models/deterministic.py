"""DeterministicModelProvider (Phase E1) -- no network calls, predictable
structured outputs, configurable failures. This is what makes every future
agent's tests (Planner/Analyst/Critic/Guide, E3-E4) not depend on live
inference, per AGENTS.md §6.

Responses are scripted in a FIFO queue per call kind. Retry-policy tests
work identically to OllamaModelProvider's: a "malformed" or "schema
invalid" queued item consumes one attempt and is retried against the next
queued item, up to orchestration.policies.MAX_STRUCTURED_OUTPUT_ATTEMPTS,
so retry/attempt-counting behavior is verified without needing a live,
flaky model.
"""

from __future__ import annotations

import time
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ValidationError

from ..contracts.structured_generation import StructuredGenerationResult, TextGenerationResult
from ..orchestration.policies import MAX_STRUCTURED_OUTPUT_ATTEMPTS, RETRYABLE_ERROR_TYPES
from .errors import (
    InvalidConfigurationError,
    MalformedOutputError,
    ModelProviderError,
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
)

DETERMINISTIC_PROVIDER_VERSION = "e1-deterministic-v1"
DETERMINISTIC_MODEL_NAME = "deterministic-test-model"

# The deterministic test provider makes no network call and has no billing
# relationship with anything -- every call costs exactly $0, always.
_NO_PROVIDER_CHARGE = ProviderCost(amountUsd=0.0, basis=CostBasis.NO_PROVIDER_CHARGE)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class _MalformedItem:
    raw_text: str = "{not valid json"


@dataclass
class _SchemaInvalidItem:
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class _ErrorItem:
    error: ModelProviderError


@dataclass
class _ValueItem:
    value: BaseModel


@dataclass
class _TextItem:
    text: str


_QueuedItem = _MalformedItem | _SchemaInvalidItem | _ErrorItem | _ValueItem | _TextItem


class DeterministicModelProvider:
    """Implements the ModelProvider protocol structurally (see
    protocol.py) -- deliberately not a subclass, since Protocol compliance
    is structural."""

    def __init__(self, provider_version: str = DETERMINISTIC_PROVIDER_VERSION) -> None:
        self._provider_version = provider_version
        self._queue: list[_QueuedItem] = []

    def enqueue_value(self, value: BaseModel) -> None:
        self._queue.append(_ValueItem(value=value))

    def enqueue_text(self, text: str) -> None:
        self._queue.append(_TextItem(text=text))

    def enqueue_malformed(self, raw_text: str = "{not valid json") -> None:
        self._queue.append(_MalformedItem(raw_text=raw_text))

    def enqueue_schema_invalid(self, raw: dict[str, Any] | None = None) -> None:
        self._queue.append(_SchemaInvalidItem(raw=raw or {}))

    def enqueue_error(self, error: ModelProviderError) -> None:
        self._queue.append(_ErrorItem(error=error))

    def _pop(self) -> _QueuedItem:
        if not self._queue:
            raise InvalidConfigurationError(
                "DeterministicModelProvider has no scripted response queued for this call"
            )
        return self._queue.pop(0)

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
        last_error: ModelProviderError | None = None
        settings = generation_settings or ModelGenerationSettings(temperature=temperature)
        effective_schema = response_schema or response_model.model_json_schema()
        input_hash = _input_hash(
            system_prompt,
            user_prompt,
            json.dumps(effective_schema, sort_keys=True),
            prompt_version,
            settings,
        )

        for attempt in range(1, MAX_STRUCTURED_OUTPUT_ATTEMPTS + 1):
            try:
                item = self._pop()
            except ModelProviderError as exc:
                _attach_failed_record(
                    exc, self._provider_version, prompt_version, input_hash, settings,
                    started_at, start_perf, attempt,
                )
                raise

            if isinstance(item, _ErrorItem):
                if not isinstance(item.error, RETRYABLE_ERROR_TYPES):
                    _attach_failed_record(
                        item.error, self._provider_version, prompt_version, input_hash, settings,
                        started_at, start_perf, attempt,
                    )
                    raise item.error
                last_error = item.error
                continue

            try:
                value = self._resolve_value(item, response_model)
            except ModelProviderError as exc:
                last_error = exc
                continue

            completed_at = _utcnow()
            return StructuredGenerationResult(
                value=value,
                modelCall=ModelCallRecord(
                    providerName="deterministic",
                    providerVersion=self._provider_version,
                    modelName=DETERMINISTIC_MODEL_NAME,
                    promptVersion=prompt_version,
                    inputHash=input_hash,
                    outputHash=_value_hash(value),
                    generationSettings=settings,
                    status=ModelCallStatus.SUCCEEDED,
                    attemptCount=attempt,
                    startedAt=started_at,
                    completedAt=completed_at,
                    latencyMs=(time.perf_counter() - start_perf) * 1000,
                    cost=_NO_PROVIDER_CHARGE,
                ),
            )

        error = RetryExhaustedError(
            f"Exhausted {MAX_STRUCTURED_OUTPUT_ATTEMPTS} attempt(s) generating {response_model.__name__}"
        )
        _attach_failed_record(
            error, self._provider_version, prompt_version, input_hash, settings,
            started_at, start_perf, MAX_STRUCTURED_OUTPUT_ATTEMPTS,
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
        settings = generation_settings or ModelGenerationSettings()
        input_hash = _input_hash(system_prompt, user_prompt, "text", prompt_version, settings)
        try:
            item = self._pop()
        except ModelProviderError as exc:
            _attach_failed_record(
                exc, self._provider_version, prompt_version, input_hash, settings,
                started_at, start_perf, 1,
            )
            raise

        if isinstance(item, _ErrorItem):
            _attach_failed_record(
                item.error, self._provider_version, prompt_version, input_hash, settings,
                started_at, start_perf, 1,
            )
            raise item.error
        if not isinstance(item, _TextItem):
            error = InvalidConfigurationError(
                "DeterministicModelProvider's next queued item is not a text response"
            )
            _attach_failed_record(
                error, self._provider_version, prompt_version, input_hash, settings,
                started_at, start_perf, 1,
            )
            raise error

        completed_at = _utcnow()
        return TextGenerationResult(
            text=item.text,
            modelCall=ModelCallRecord(
                providerName="deterministic",
                providerVersion=self._provider_version,
                modelName=DETERMINISTIC_MODEL_NAME,
                promptVersion=prompt_version,
                inputHash=input_hash,
                outputHash=hashlib.sha256(item.text.encode("utf-8")).hexdigest(),
                generationSettings=settings,
                status=ModelCallStatus.SUCCEEDED,
                attemptCount=1,
                startedAt=started_at,
                completedAt=completed_at,
                latencyMs=(time.perf_counter() - start_perf) * 1000,
                cost=_NO_PROVIDER_CHARGE,
            ),
        )

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(healthy=True, detail="deterministic provider is always healthy")

    @property
    def provider_metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            providerName="deterministic",
            providerVersion=self._provider_version,
            supportsStreaming=False,
            supportsStructuredOutput=True,
            isLocal=True,
            requiresApiKey=False,
        )

    @staticmethod
    def _resolve_value(item: _QueuedItem, response_model: type[BaseModel]) -> BaseModel:
        if isinstance(item, _ValueItem):
            if not isinstance(item.value, response_model):
                raise SchemaValidationError(
                    f"Queued value is a {type(item.value).__name__}, expected {response_model.__name__}"
                )
            return item.value
        if isinstance(item, _MalformedItem):
            raise MalformedOutputError(f"Configured malformed response: {item.raw_text!r}")
        if isinstance(item, _SchemaInvalidItem):
            try:
                return response_model.model_validate(item.raw)
            except ValidationError as exc:
                raise SchemaValidationError(str(exc)) from exc
        raise InvalidConfigurationError(f"Unexpected queued item type: {type(item).__name__}")


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


def _value_hash(value: BaseModel) -> str:
    return hashlib.sha256(value.model_dump_json().encode("utf-8")).hexdigest()


def _attach_failed_record(
    error: ModelProviderError,
    provider_version: str,
    prompt_version: str,
    input_hash: str,
    settings: ModelGenerationSettings,
    started_at: datetime,
    start_perf: float,
    attempt: int,
) -> None:
    completed_at = _utcnow()
    error.callRecord = ModelCallRecord(
        providerName="deterministic",
        providerVersion=provider_version,
        modelName=DETERMINISTIC_MODEL_NAME,
        promptVersion=prompt_version,
        inputHash=input_hash,
        generationSettings=settings,
        status=ModelCallStatus.FAILED,
        attemptCount=attempt,
        startedAt=started_at,
        completedAt=completed_at,
        latencyMs=(time.perf_counter() - start_perf) * 1000,
        cost=_NO_PROVIDER_CHARGE,
        errorType=type(error).__name__,
        errorMessage=str(error)[:500],
    )
