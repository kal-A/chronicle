"""Topic-neutral evaluation-case schema for the E7 comparative harness.

``EvaluationCase`` extends the answer-free :class:`BenchmarkCase` shape with the
rubric fields the human-review slice will consume (semantic checks, usefulness
criteria). It contains no target answer a model could copy, and its ``caseId`` is
a behavior-describing slug rather than a corpus abbreviation, so runtime code
stays subject-agnostic (the case *data* lives in ``benchmarks/e7/cases.json``).
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ...contracts.enums import EvidenceLinkRole
from ..contracts.plan import QuestionType
from .benchmark import TemporalConstraint

#: The legacy ``bc-##`` / ``coe-##`` identifier shape. A slug must NOT match it;
#: those values move to ``legacyAliases``.
_LEGACY_ID = re.compile(r"^(bc|coe)-\d{2}$")


class StrategyId(str, Enum):
    SINGLE_PROMPT = "single_prompt"
    BASIC_RAG = "basic_rag"
    PLANNER_ANALYST = "planner_analyst"
    FULL_WORKFLOW = "full_workflow"


class EvaluationProfile(str, Enum):
    DETERMINISTIC_FULL = "deterministic_full"
    QWEN_SMOKE = "qwen_smoke"
    QWEN_GATE = "qwen_gate"
    QWEN_STABILITY = "qwen_stability"
    QWEN_FULL = "qwen_full"


class SemanticCheck(BaseModel):
    """A reviewed proposition rubric (record IDs + normalized relation, never
    target prose). Reversing subject/object on a ``directionalityCritical`` check
    is a critical historical error even when the cited passage names both."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    checkId: str = Field(min_length=1)
    subjectRecordId: str = Field(min_length=1)
    relation: str = Field(min_length=1, max_length=80)
    objectRecordId: str = Field(min_length=1)
    polarity: Literal["affirms", "negates"]
    directionalityCritical: bool = False
    supportingRecordIds: tuple[str, ...] = Field(default=(), max_length=8)


class EvaluationCase(BaseModel):
    """One answer-free, deterministic evaluation case, topic-neutral by slug."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    caseId: str = Field(pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
    legacyAliases: tuple[str, ...] = Field(default=(), max_length=3)
    benchmarkVersion: str = Field(min_length=1)
    corpusId: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=1_000)
    category: QuestionType
    profiles: tuple[EvaluationProfile, ...] = Field(min_length=1)
    acceptableTools: tuple[str, ...] = Field(min_length=1, max_length=10)
    requiredEvidenceIds: tuple[str, ...] = Field(default=(), max_length=12)
    forbiddenEvidenceIds: tuple[str, ...] = Field(default=(), max_length=12)
    expectedCitationRoles: tuple[EvidenceLinkRole, ...] = Field(default=(), max_length=3)
    requiresCounterevidence: bool = False
    temporalConstraints: tuple[TemporalConstraint, ...] = Field(default=(), max_length=3)
    expectedAbstention: bool = False
    unacceptableClaims: tuple[str, ...] = Field(default=(), max_length=8)
    semanticChecks: tuple[SemanticCheck, ...] = Field(default=(), max_length=8)
    usefulnessCriteria: tuple[str, ...] = Field(default=(), max_length=8)
    reviewNotes: str = Field(default="", max_length=2_000)

    @model_validator(mode="after")
    def _validate(self) -> "EvaluationCase":
        if _LEGACY_ID.match(self.caseId):
            raise ValueError("caseId must be a topic-neutral slug, not a legacy alias")
        if set(self.requiredEvidenceIds) & set(self.forbiddenEvidenceIds):
            raise ValueError("required and forbidden evidence IDs must be disjoint")
        if (
            self.requiresCounterevidence
            and EvidenceLinkRole.COUNTEREVIDENCE not in self.expectedCitationRoles
        ):
            raise ValueError("counterevidence cases must expect the counterevidence citation role")
        return self


__all__ = ["StrategyId", "EvaluationProfile", "SemanticCheck", "EvaluationCase"]
