import pytest
from pydantic import BaseModel

from chronicle.ai.models.deterministic import DeterministicModelProvider
from chronicle.ai.models.errors import (
    InvalidConfigurationError,
    ModelUnavailableError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RetryExhaustedError,
)
from chronicle.ai.models.metadata import CostBasis, ModelCallStatus


class _SampleAnswer(BaseModel):
    summary: str
    confidence: float


def test_valid_structured_generation_returns_the_queued_value():
    provider = DeterministicModelProvider()
    provider.enqueue_value(_SampleAnswer(summary="Troppau established the doctrine.", confidence=0.9))

    result = provider.generate_structured(
        system_prompt="system",
        user_prompt="user",
        response_model=_SampleAnswer,
        prompt_version="v1",
    )

    assert result.value.summary == "Troppau established the doctrine."
    assert result.modelCall.status == ModelCallStatus.SUCCEEDED
    assert result.modelCall.attemptCount == 1
    assert result.modelCall.promptVersion == "v1"
    assert result.modelCall.latencyMs >= 0
    assert result.modelCall.cost.amountUsd == 0.0
    assert result.modelCall.cost.basis == CostBasis.NO_PROVIDER_CHARGE


def test_malformed_response_then_retry_exhaustion():
    provider = DeterministicModelProvider()
    provider.enqueue_malformed()
    provider.enqueue_malformed()

    with pytest.raises(RetryExhaustedError):
        provider.generate_structured(
            system_prompt="s", user_prompt="u", response_model=_SampleAnswer, prompt_version="v1"
        )


def test_schema_invalid_response_then_retry_exhaustion():
    provider = DeterministicModelProvider()
    provider.enqueue_schema_invalid({"wrong_field": "nope"})
    provider.enqueue_schema_invalid({"wrong_field": "still nope"})

    with pytest.raises(RetryExhaustedError):
        provider.generate_structured(
            system_prompt="s", user_prompt="u", response_model=_SampleAnswer, prompt_version="v1"
        )


def test_malformed_response_then_valid_response_succeeds_on_retry():
    provider = DeterministicModelProvider()
    provider.enqueue_malformed()
    provider.enqueue_value(_SampleAnswer(summary="recovered", confidence=0.5))

    result = provider.generate_structured(
        system_prompt="s", user_prompt="u", response_model=_SampleAnswer, prompt_version="v1"
    )

    assert result.value.summary == "recovered"
    assert result.modelCall.attemptCount == 2


def test_unavailable_error_is_not_retried():
    provider = DeterministicModelProvider()
    provider.enqueue_error(ProviderUnavailableError("down"))
    provider.enqueue_value(_SampleAnswer(summary="unreachable", confidence=0.1))

    with pytest.raises(ProviderUnavailableError):
        provider.generate_structured(
            system_prompt="s", user_prompt="u", response_model=_SampleAnswer, prompt_version="v1"
        )


def test_model_unavailable_error_is_not_retried():
    provider = DeterministicModelProvider()
    provider.enqueue_error(ModelUnavailableError("no such model"))

    with pytest.raises(ModelUnavailableError):
        provider.generate_structured(
            system_prompt="s", user_prompt="u", response_model=_SampleAnswer, prompt_version="v1"
        )


def test_timeout_error_is_retried_and_can_succeed():
    provider = DeterministicModelProvider()
    provider.enqueue_error(ProviderTimeoutError("slow"))
    provider.enqueue_value(_SampleAnswer(summary="eventually", confidence=0.7))

    result = provider.generate_structured(
        system_prompt="s", user_prompt="u", response_model=_SampleAnswer, prompt_version="v1"
    )

    assert result.value.summary == "eventually"
    assert result.modelCall.attemptCount == 2


def test_calling_without_a_queued_response_raises_invalid_configuration():
    provider = DeterministicModelProvider()

    with pytest.raises(InvalidConfigurationError):
        provider.generate_structured(
            system_prompt="s", user_prompt="u", response_model=_SampleAnswer, prompt_version="v1"
        )


def test_text_generation_returns_the_queued_text():
    provider = DeterministicModelProvider()
    provider.enqueue_text("This is verified-record prose.")

    result = provider.generate_text_from_verified_records(
        system_prompt="s", user_prompt="u", prompt_version="v1"
    )

    assert result.text == "This is verified-record prose."
    assert result.modelCall.status == ModelCallStatus.SUCCEEDED
    assert result.modelCall.cost.amountUsd == 0.0
    assert result.modelCall.cost.basis == CostBasis.NO_PROVIDER_CHARGE


def test_health_check_is_always_healthy():
    provider = DeterministicModelProvider()
    health = provider.health_check()
    assert health.healthy is True


def test_provider_metadata_reports_no_api_key_and_local():
    provider = DeterministicModelProvider()
    metadata = provider.provider_metadata
    assert metadata.isLocal is True
    assert metadata.requiresApiKey is False
    assert metadata.supportsStructuredOutput is True
