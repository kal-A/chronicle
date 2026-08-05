"""Return-value contracts for ModelProvider.generate_structured() and
generate_text_from_verified_records() (Phase E1).

Plain generic dataclasses, not Pydantic models -- `value` is already a
validated Pydantic instance by the time a provider returns it, and these
wrappers are in-process return values, never serialized directly, so
Pydantic's validation/serialization machinery would be pure overhead here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from ..models.metadata import ModelCallRecord

T = TypeVar("T")


@dataclass(frozen=True)
class StructuredGenerationResult(Generic[T]):
    value: T
    modelCall: ModelCallRecord


@dataclass(frozen=True)
class TextGenerationResult:
    text: str
    modelCall: ModelCallRecord
