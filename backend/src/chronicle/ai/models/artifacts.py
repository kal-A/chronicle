"""Provider identity and the bounded per-attempt audit artifact (E7.3).

``ProviderIdentity`` records exactly which provider/model produced a result, so
an evaluation run is reproducible and auditable. ``ModelCallArtifact`` is a
bounded projection of a :class:`ModelCallRecord`: hashes, settings, status,
usage/cost/latency, and at most a sanitized error excerpt for a rejected
attempt -- never unbounded prompt or response text.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .metadata import ModelCallRecord, ModelCallStatus, ModelGenerationSettings, ProviderCost

#: Hard ceiling on a captured error/output excerpt (sanitized, rejected attempts
#: only). Providers already bound errorMessage to 500; this is the contract cap.
MAX_ERROR_EXCERPT_CHARACTERS = 4_000


class ProviderIdentity(BaseModel):
    """Who produced a result. ``modelVersion`` / ``modelDigest`` are ``None``
    when the provider cannot report them -- never fabricated."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    providerName: str = Field(min_length=1)
    providerVersion: str = Field(min_length=1)
    modelName: str = Field(min_length=1)
    modelVersion: str | None = None
    modelDigest: str | None = None


class ModelCallArtifact(BaseModel):
    """A bounded, persistable audit of one model attempt."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    callId: str = Field(min_length=1)
    inputHash: str = Field(min_length=1)
    outputHash: str | None = None
    promptCharacters: int = Field(default=0, ge=0)
    schemaCharacters: int = Field(default=0, ge=0)
    generationSettings: ModelGenerationSettings
    status: ModelCallStatus
    attemptCount: int = Field(ge=1)
    latencyMs: float = Field(ge=0)
    cost: ProviderCost
    errorExcerpt: str | None = Field(default=None, max_length=MAX_ERROR_EXCERPT_CHARACTERS)

    @classmethod
    def from_record(
        cls,
        call_id: str,
        record: ModelCallRecord,
        *,
        prompt_characters: int = 0,
        schema_characters: int = 0,
    ) -> "ModelCallArtifact":
        excerpt = record.errorMessage[:MAX_ERROR_EXCERPT_CHARACTERS] if record.errorMessage else None
        return cls(
            callId=call_id,
            inputHash=record.inputHash,
            outputHash=record.outputHash,
            promptCharacters=prompt_characters,
            schemaCharacters=schema_characters,
            generationSettings=record.generationSettings,
            status=record.status,
            attemptCount=record.attemptCount,
            latencyMs=record.latencyMs,
            cost=record.cost,
            errorExcerpt=excerpt,
        )


__all__ = ["ProviderIdentity", "ModelCallArtifact", "MAX_ERROR_EXCERPT_CHARACTERS"]
