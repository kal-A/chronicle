"""Provider identity + bounded attempt artifact (E7.3).

Deterministic-provider identity is fully exercised; the Ollama identity path is
exercised with httpx.MockTransport (no live server) to prove it reads the real
model digest and never fabricates one when the server is unreachable.
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from chronicle.ai.models.artifacts import (
    MAX_ERROR_EXCERPT_CHARACTERS,
    ModelCallArtifact,
    ProviderIdentity,
)
from chronicle.ai.models.deterministic import DETERMINISTIC_MODEL_NAME, DeterministicModelProvider
from chronicle.ai.models.metadata import (
    CostBasis,
    ModelCallRecord,
    ModelCallStatus,
    ModelGenerationSettings,
    ProviderCost,
)
from chronicle.ai.models.ollama import OllamaModelProvider


def test_deterministic_provider_exposes_a_stable_identity_and_digest():
    identity = DeterministicModelProvider().provider_identity()
    assert isinstance(identity, ProviderIdentity)
    assert identity.providerName == "deterministic"
    assert identity.modelName == DETERMINISTIC_MODEL_NAME
    # A stable synthetic digest -- identical across instances, never absent.
    assert identity.modelDigest
    assert identity.modelDigest == DeterministicModelProvider().provider_identity().modelDigest


def _failed_record(message: str) -> ModelCallRecord:
    now = datetime.now(timezone.utc)
    return ModelCallRecord(
        providerName="deterministic",
        providerVersion="e1-deterministic-v1",
        modelName=DETERMINISTIC_MODEL_NAME,
        promptVersion="p-v1",
        inputHash="a" * 64,
        generationSettings=ModelGenerationSettings(temperature=0.0),
        status=ModelCallStatus.FAILED,
        attemptCount=2,
        startedAt=now,
        completedAt=now,
        latencyMs=1.0,
        cost=ProviderCost(amountUsd=0.0, basis=CostBasis.NO_PROVIDER_CHARGE),
        errorType="SchemaValidationError",
        errorMessage=message,
    )


def test_model_call_artifact_from_record_carries_a_bounded_error_excerpt():
    artifact = ModelCallArtifact.from_record(
        "call-1", _failed_record("boom " * 2000), prompt_characters=12, schema_characters=8
    )
    assert artifact.callId == "call-1"
    assert artifact.status is ModelCallStatus.FAILED
    assert artifact.attemptCount == 2
    assert artifact.promptCharacters == 12 and artifact.schemaCharacters == 8
    assert artifact.errorExcerpt is not None
    assert len(artifact.errorExcerpt) <= MAX_ERROR_EXCERPT_CHARACTERS


def _ollama(handler) -> OllamaModelProvider:
    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://localhost:11434")
    return OllamaModelProvider(client=client, model="qwen2.5:7b-instruct")


def test_ollama_identity_reads_the_model_digest_from_tags():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"models": [{"name": "qwen2.5:7b-instruct", "digest": "sha256:abc123"}]},
        )

    identity = _ollama(handler).provider_identity()
    assert identity.providerName == "ollama"
    assert identity.modelName == "qwen2.5:7b-instruct"
    assert identity.modelDigest == "sha256:abc123"


def test_ollama_identity_leaves_digest_absent_when_unreachable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("ollama is down")

    identity = _ollama(handler).provider_identity()
    assert identity.modelName == "qwen2.5:7b-instruct"  # name is known from config
    assert identity.modelDigest is None  # never fabricated
