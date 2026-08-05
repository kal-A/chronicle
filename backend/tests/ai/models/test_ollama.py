"""OllamaModelProvider tests -- every HTTP interaction goes through
httpx.MockTransport, so this suite makes zero real network requests and
requires no running Ollama server, no downloaded model, and no internet
access."""

import json

import httpx
import pytest
from pydantic import BaseModel

from chronicle.ai.models.errors import (
    InvalidConfigurationError,
    MalformedOutputError,
    ModelUnavailableError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitError,
    RetryExhaustedError,
    SchemaValidationError,
)
from chronicle.ai.models.metadata import CostBasis
from chronicle.ai.models.ollama import OllamaModelProvider


class _SampleAnswer(BaseModel):
    summary: str
    confidence: float


def _provider_with_handler(handler, **kwargs) -> OllamaModelProvider:
    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://fake-ollama:11434")
    return OllamaModelProvider(base_url="http://fake-ollama:11434", client=client, **kwargs)


def _ok_chat_response(content: str, *, prompt_eval_count=None, eval_count=None) -> httpx.Response:
    body = {"message": {"role": "assistant", "content": content}}
    if prompt_eval_count is not None:
        body["prompt_eval_count"] = prompt_eval_count
    if eval_count is not None:
        body["eval_count"] = eval_count
    return httpx.Response(200, json=body)


def test_request_includes_the_json_schema_and_model_name():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["payload"] = json.loads(request.content)
        return _ok_chat_response(json.dumps({"summary": "ok", "confidence": 1.0}))

    provider = _provider_with_handler(handler, model="qwen2.5:7b-instruct")
    provider.generate_structured(
        system_prompt="sys", user_prompt="usr", response_model=_SampleAnswer, prompt_version="v1"
    )

    payload = captured["payload"]
    assert payload["model"] == "qwen2.5:7b-instruct"
    assert payload["format"] == _SampleAnswer.model_json_schema()
    assert payload["messages"][0] == {"role": "system", "content": "sys"}
    assert payload["messages"][1] == {"role": "user", "content": "usr"}


def test_valid_structured_response_parses_and_records_usage():
    def handler(request: httpx.Request) -> httpx.Response:
        return _ok_chat_response(
            json.dumps({"summary": "Troppau established the doctrine.", "confidence": 0.9}),
            prompt_eval_count=42,
            eval_count=17,
        )

    provider = _provider_with_handler(handler)
    result = provider.generate_structured(
        system_prompt="s", user_prompt="u", response_model=_SampleAnswer, prompt_version="v1"
    )

    assert result.value.summary == "Troppau established the doctrine."
    assert result.modelCall.attemptCount == 1
    assert result.modelCall.usage.promptTokens == 42
    assert result.modelCall.usage.completionTokens == 17


def test_structured_response_records_zero_provider_billed_cost():
    """Ollama is a local daemon -- there is no provider to bill, so the
    cost is genuinely $0, not "unknown" (docs/ai/model-provider-
    decisions.md's cost-recording section)."""

    def handler(request: httpx.Request) -> httpx.Response:
        return _ok_chat_response(json.dumps({"summary": "ok", "confidence": 1.0}))

    provider = _provider_with_handler(handler)
    result = provider.generate_structured(
        system_prompt="s", user_prompt="u", response_model=_SampleAnswer, prompt_version="v1"
    )
    assert result.modelCall.cost.amountUsd == 0.0
    assert result.modelCall.cost.basis == CostBasis.NO_PROVIDER_CHARGE


def test_usage_is_omitted_not_fabricated_when_absent():
    def handler(request: httpx.Request) -> httpx.Response:
        return _ok_chat_response(json.dumps({"summary": "ok", "confidence": 1.0}))

    provider = _provider_with_handler(handler)
    result = provider.generate_structured(
        system_prompt="s", user_prompt="u", response_model=_SampleAnswer, prompt_version="v1"
    )
    assert result.modelCall.usage is None


def test_malformed_json_response_raises_after_retry_exhaustion():
    def handler(request: httpx.Request) -> httpx.Response:
        return _ok_chat_response("this is not json")

    provider = _provider_with_handler(handler)
    with pytest.raises(RetryExhaustedError) as excinfo:
        provider.generate_structured(
            system_prompt="s", user_prompt="u", response_model=_SampleAnswer, prompt_version="v1"
        )
    assert isinstance(excinfo.value.__cause__, MalformedOutputError)


def test_schema_invalid_response_raises_after_retry_exhaustion():
    def handler(request: httpx.Request) -> httpx.Response:
        return _ok_chat_response(json.dumps({"wrong_field": "nope"}))

    provider = _provider_with_handler(handler)
    with pytest.raises(RetryExhaustedError) as excinfo:
        provider.generate_structured(
            system_prompt="s", user_prompt="u", response_model=_SampleAnswer, prompt_version="v1"
        )
    assert isinstance(excinfo.value.__cause__, SchemaValidationError)


def test_retry_after_invalid_output_can_succeed_with_feedback_appended():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        calls.append(payload)
        if len(calls) == 1:
            return _ok_chat_response("not valid json")
        # The retry's messages must include the failed attempt and feedback.
        assert payload["messages"][-1]["role"] == "user"
        assert "invalid" in payload["messages"][-1]["content"].lower()
        return _ok_chat_response(json.dumps({"summary": "recovered", "confidence": 0.5}))

    provider = _provider_with_handler(handler)
    result = provider.generate_structured(
        system_prompt="s", user_prompt="u", response_model=_SampleAnswer, prompt_version="v1"
    )

    assert result.value.summary == "recovered"
    assert result.modelCall.attemptCount == 2
    assert len(calls) == 2


def test_connection_refused_maps_to_provider_unavailable_and_is_not_retried():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        raise httpx.ConnectError("connection refused", request=request)

    provider = _provider_with_handler(handler)
    with pytest.raises(ProviderUnavailableError):
        provider.generate_structured(
            system_prompt="s", user_prompt="u", response_model=_SampleAnswer, prompt_version="v1"
        )
    assert calls["count"] == 1


def test_model_not_found_maps_to_model_unavailable_and_is_not_retried():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(404, json={"error": "model not found"})

    provider = _provider_with_handler(handler, model="does-not-exist")
    with pytest.raises(ModelUnavailableError):
        provider.generate_structured(
            system_prompt="s", user_prompt="u", response_model=_SampleAnswer, prompt_version="v1"
        )
    assert calls["count"] == 1


def test_timeout_is_retried_and_can_succeed():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            raise httpx.TimeoutException("timed out", request=request)
        return _ok_chat_response(json.dumps({"summary": "second try", "confidence": 0.6}))

    provider = _provider_with_handler(handler)
    result = provider.generate_structured(
        system_prompt="s", user_prompt="u", response_model=_SampleAnswer, prompt_version="v1"
    )
    assert result.value.summary == "second try"
    assert result.modelCall.attemptCount == 2


def test_timeout_exhaustion_raises_retry_exhausted():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    provider = _provider_with_handler(handler)
    with pytest.raises(RetryExhaustedError) as excinfo:
        provider.generate_structured(
            system_prompt="s", user_prompt="u", response_model=_SampleAnswer, prompt_version="v1"
        )
    assert isinstance(excinfo.value.__cause__, ProviderTimeoutError)


def test_rate_limit_is_retryable():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(429, json={"error": "rate limited"})
        return _ok_chat_response(json.dumps({"summary": "after limit", "confidence": 0.4}))

    provider = _provider_with_handler(handler)
    result = provider.generate_structured(
        system_prompt="s", user_prompt="u", response_model=_SampleAnswer, prompt_version="v1"
    )
    assert result.value.summary == "after limit"


def test_server_error_maps_to_provider_unavailable_and_is_not_retried():
    # A 500 from your own local Ollama daemon (not a rate-limited/flaky
    # cloud API) usually means something is actually broken -- a crashed
    # model process, an OOM, a bad request shape -- not a transient blip
    # that a same-millisecond retry would fix. Same "fail fast and tell the
    # truth" treatment as connection-refused, deliberately not retried.
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(500, json={"error": "internal error"})

    provider = _provider_with_handler(handler)
    with pytest.raises(ProviderUnavailableError):
        provider.generate_structured(
            system_prompt="s", user_prompt="u", response_model=_SampleAnswer, prompt_version="v1"
        )
    assert calls["count"] == 1


def test_health_check_reports_healthy_on_200():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"models": []})

    provider = _provider_with_handler(handler)
    health = provider.health_check()
    assert health.healthy is True


def test_health_check_reports_unhealthy_on_connection_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    provider = _provider_with_handler(handler)
    health = provider.health_check()
    assert health.healthy is False
    assert health.detail is not None


def test_text_generation_does_not_send_a_format_field():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["payload"] = json.loads(request.content)
        return _ok_chat_response("Plain prose over verified records.")

    provider = _provider_with_handler(handler)
    result = provider.generate_text_from_verified_records(
        system_prompt="s", user_prompt="u", prompt_version="v1"
    )

    assert result.text == "Plain prose over verified records."
    assert "format" not in captured["payload"]
    assert result.modelCall.cost.amountUsd == 0.0
    assert result.modelCall.cost.basis == CostBasis.NO_PROVIDER_CHARGE


def test_invalid_base_url_is_rejected_at_construction():
    with pytest.raises(InvalidConfigurationError):
        OllamaModelProvider(base_url="not-a-url")


def test_empty_model_name_is_rejected_at_construction():
    with pytest.raises(InvalidConfigurationError):
        OllamaModelProvider(base_url="http://localhost:11434", model="")


def test_provider_metadata_reports_local_and_no_api_key():
    def handler(request: httpx.Request) -> httpx.Response:
        return _ok_chat_response("{}")

    provider = _provider_with_handler(handler)
    metadata = provider.provider_metadata
    assert metadata.isLocal is True
    assert metadata.requiresApiKey is False
