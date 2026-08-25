from __future__ import annotations

import json

import httpx
import pytest
from pydantic import BaseModel

from chronicle.ai.models.deterministic import DeterministicModelProvider
from chronicle.ai.models.errors import ProviderUnavailableError, RetryExhaustedError
from chronicle.ai.models.metadata import ModelCallStatus, ModelGenerationSettings
from chronicle.ai.models.ollama import OllamaModelProvider


class _Answer(BaseModel):
    answer: str


def test_deterministic_terminal_failure_carries_a_complete_failed_call_record():
    provider = DeterministicModelProvider()
    provider.enqueue_malformed()
    provider.enqueue_malformed()

    with pytest.raises(RetryExhaustedError) as excinfo:
        provider.generate_structured(
            system_prompt="system",
            user_prompt="user",
            response_model=_Answer,
            prompt_version="e3-test-v1",
        )

    record = excinfo.value.callRecord
    assert record.status is ModelCallStatus.FAILED
    assert record.attemptCount == 2
    assert record.inputHash
    assert record.errorType == "RetryExhaustedError"
    assert record.completedAt >= record.startedAt


def test_nonretryable_provider_failure_also_carries_an_audit_record():
    provider = DeterministicModelProvider()
    provider.enqueue_error(ProviderUnavailableError("down"))

    with pytest.raises(ProviderUnavailableError) as excinfo:
        provider.generate_structured(
            system_prompt="s", user_prompt="u", response_model=_Answer, prompt_version="v1"
        )
    assert excinfo.value.callRecord.status is ModelCallStatus.FAILED
    assert excinfo.value.callRecord.attemptCount == 1


def test_ollama_generation_settings_map_to_local_runtime_options():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"message": {"content": '{"answer":"ok"}'}})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://fake:11434")
    provider = OllamaModelProvider(base_url="http://fake:11434", client=client)
    settings = ModelGenerationSettings(
        temperature=0.0, contextTokens=8_192, maxCompletionTokens=900
    )
    result = provider.generate_structured(
        system_prompt="s",
        user_prompt="u",
        response_model=_Answer,
        prompt_version="v1",
        generation_settings=settings,
    )

    assert captured["payload"]["options"] == {
        "temperature": 0.0,
        "num_ctx": 8_192,
        "num_predict": 900,
    }
    assert result.modelCall.generationSettings == settings
    assert result.modelCall.inputHash


def test_text_generation_accepts_the_same_local_runtime_limits():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"message": {"content": "plain baseline"}})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://fake:11434")
    provider = OllamaModelProvider(base_url="http://fake:11434", client=client)
    settings = ModelGenerationSettings(contextTokens=8_192, maxCompletionTokens=1_800)
    provider.generate_text_from_verified_records(
        system_prompt="s",
        user_prompt="u",
        prompt_version="baseline-a-v1",
        generation_settings=settings,
    )
    assert captured["payload"]["options"]["num_ctx"] == 8_192
    assert captured["payload"]["options"]["num_predict"] == 1_800


def test_retry_usage_is_accumulated_across_structured_attempts():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        content = "not-json" if calls["count"] == 1 else '{"answer":"ok"}'
        return httpx.Response(
            200,
            json={
                "message": {"content": content},
                "prompt_eval_count": 10 * calls["count"],
                "eval_count": calls["count"],
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://fake:11434")
    result = OllamaModelProvider(base_url="http://fake:11434", client=client).generate_structured(
        system_prompt="s", user_prompt="u", response_model=_Answer, prompt_version="v1"
    )
    assert result.modelCall.usage.promptTokens == 30
    assert result.modelCall.usage.completionTokens == 3
