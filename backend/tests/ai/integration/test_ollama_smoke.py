"""Real-model smoke test for OllamaModelProvider (Phase E1 closeout).

This is the ONE minimal real-inference check this repository runs: does
generate_structured() actually work end to end against a real, locally
running Ollama daemon and the configured model -- not a mock. Everything
else about the four future agents (Planner/Analyst/Critic/Guide),
historical reasoning, tool calling, and Phase E2's corpus tools remains
completely untested by this file, on purpose.

Marked `local_ollama_integration` and excluded from the default test run
(backend/pyproject.toml's addopts) -- ordinary `pytest -q` never touches
this file, never requires Ollama, and never makes a network call, per
AGENTS.md §6. Invoke explicitly:

    pytest -m local_ollama_integration -s

Skips itself (does not fail) when Ollama is unreachable or the configured
model is not pulled, so it is always safe to run in an environment where
Ollama isn't set up -- see docs/ai/learning-log.md's dated smoke-test
entry and docs/delivery/phase-e1-real-model-smoke-test-report.md for the
actual recorded result of the one real run this test has had.
"""

from __future__ import annotations

import time

import pytest
from pydantic import BaseModel

from chronicle.ai.models.metadata import CostBasis, ModelCallStatus
from chronicle.ai.models.ollama import DEFAULT_MODEL, OllamaModelProvider

pytestmark = pytest.mark.local_ollama_integration


class SmokeTestResponse(BaseModel):
    """Deliberately trivial -- this test proves JSON-schema-constrained
    generation works at all, not that any agent-shaped contract does."""

    label: str
    count: int
    confirmed: bool


SMOKE_TEST_SYSTEM_PROMPT = (
    "You are a structured-output test assistant. Respond only with JSON "
    "matching the required schema -- no prose, no explanation."
)

SMOKE_TEST_USER_PROMPT = (
    "Return a small structured object proving that the local model can "
    "follow a JSON schema. Set label to the word 'ready', count to 3, "
    "and confirmed to true."
)

SMOKE_TEST_PROMPT_VERSION = "e1-smoke-v1"


def test_real_ollama_structured_generation():
    provider = OllamaModelProvider()

    health = provider.health_check()
    if not health.healthy:
        pytest.skip(f"Ollama not reachable, skipping real-model smoke test: {health.detail}")

    started = time.perf_counter()
    result = provider.generate_structured(
        system_prompt=SMOKE_TEST_SYSTEM_PROMPT,
        user_prompt=SMOKE_TEST_USER_PROMPT,
        response_model=SmokeTestResponse,
        prompt_version=SMOKE_TEST_PROMPT_VERSION,
        temperature=0.0,
    )
    wall_clock_seconds = time.perf_counter() - started

    assert isinstance(result.value, SmokeTestResponse)
    assert result.modelCall.status == ModelCallStatus.SUCCEEDED
    assert result.modelCall.modelName == DEFAULT_MODEL
    assert result.modelCall.promptVersion == SMOKE_TEST_PROMPT_VERSION
    assert result.modelCall.attemptCount in (1, 2)
    assert result.modelCall.cost.amountUsd == 0.0
    assert result.modelCall.cost.basis == CostBasis.NO_PROVIDER_CHARGE

    print("\n--- Phase E1 real-model smoke test ---")
    print(f"model: {result.modelCall.modelName}")
    print(f"attempts: {result.modelCall.attemptCount}")
    print(f"response value: {result.value.model_dump()}")
    print(f"latencyMs (provider-measured): {result.modelCall.latencyMs:.1f}")
    print(f"wall-clock seconds (test-measured): {wall_clock_seconds:.2f}")
    print(f"usage: {result.modelCall.usage}")
    print(f"cost: {result.modelCall.cost}")
    print("--- end smoke test ---\n")
