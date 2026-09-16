"""Model-free Phase E3 benchmark cases and fixture-reference validation.

This module deliberately contains no production prompt imports and no target
answers, and no subject names: the 24 cases are loaded from the versioned data
file ``benchmarks/e7/cases.json`` (the sanctioned data carve-out). A benchmark
case describes observable retrieval/grounding behavior; it does not provide
prose that a model could copy.
"""

from __future__ import annotations

import json
from datetime import date
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ...contracts.enums import EvidenceLinkRole
from ...corpus.manifest import CorpusRegistry
from ..contracts.plan import QuestionType

if TYPE_CHECKING:  # avoid a circular import: contracts imports TemporalConstraint from here
    from .contracts import EvaluationCase


class TemporalConstraintKind(str, Enum):
    EVENT_ORDER = "event_order"
    DATE_BOUND = "date_bound"


class TemporalConstraint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: TemporalConstraintKind
    eventIds: tuple[str, ...] = Field(default=(), max_length=8)
    earliest: date | None = None
    latest: date | None = None

    @model_validator(mode="after")
    def _require_a_bound(self) -> "TemporalConstraint":
        if not self.eventIds and self.earliest is None and self.latest is None:
            raise ValueError("a temporal constraint requires event IDs or a date bound")
        if self.earliest and self.latest and self.earliest > self.latest:
            raise ValueError("earliest cannot be after latest")
        return self


class BenchmarkCase(BaseModel):
    """One answer-free, deterministic evaluation case."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    caseId: str = Field(pattern=r"^(bc|coe)-\d{2}$")
    corpusId: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=1_000)
    category: QuestionType
    acceptableTools: tuple[str, ...] = Field(min_length=1, max_length=10)
    requiredEvidenceIds: tuple[str, ...] = Field(default=(), max_length=12)
    forbiddenEvidenceIds: tuple[str, ...] = Field(default=(), max_length=12)
    expectedCitationRoles: tuple[EvidenceLinkRole, ...] = Field(default=(), max_length=3)
    requiresCounterevidence: bool = False
    temporalConstraints: tuple[TemporalConstraint, ...] = Field(default=(), max_length=3)
    expectedAbstention: bool = False
    unacceptableClaims: tuple[str, ...] = Field(default=(), max_length=8)

    @model_validator(mode="after")
    def _validate_case(self) -> "BenchmarkCase":
        if set(self.requiredEvidenceIds) & set(self.forbiddenEvidenceIds):
            raise ValueError("required and forbidden evidence IDs must be disjoint")
        if self.requiresCounterevidence and EvidenceLinkRole.COUNTEREVIDENCE not in self.expectedCitationRoles:
            raise ValueError("counterevidence cases must expect the counterevidence citation role")
        return self


class BenchmarkReferenceIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    caseId: str
    recordId: str
    detail: str


class BenchmarkReferenceValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    valid: bool
    validatedCaseCount: int = Field(ge=0)
    validatedReferenceCount: int = Field(ge=0)
    issues: tuple[BenchmarkReferenceIssue, ...] = ()


class BenchmarkValidationError(ValueError):
    def __init__(self, issues: tuple[BenchmarkReferenceIssue, ...]) -> None:
        self.issues = issues
        rendered = "; ".join(f"{issue.caseId}: {issue.recordId} ({issue.detail})" for issue in issues)
        super().__init__(f"benchmark fixture reference validation failed: {rendered}")


#: The versioned case data. Kept out of code so this module holds no subject
#: names and the anti-topic-branching guard can scan ``ai/evaluation``.
_CASES_PATH = Path(__file__).resolve().parents[4] / "benchmarks" / "e7" / "cases.json"


def load_evaluation_benchmark() -> tuple["EvaluationCase", ...]:
    """Load the versioned, topic-neutral E7 evaluation cases from data."""

    from .contracts import EvaluationCase  # local import breaks the module cycle

    raw = json.loads(_CASES_PATH.read_text(encoding="utf-8"))
    return tuple(EvaluationCase.model_validate(entry) for entry in raw["cases"])


def load_e3_benchmark() -> tuple[BenchmarkCase, ...]:
    """Legacy Phase E3 view: the same cases keyed by their original ``bc-##`` /
    ``coe-##`` identifiers, so existing E3 tests and metrics keep working
    unchanged. Every returned object is a fresh, frozen copy."""

    cases: list[BenchmarkCase] = []
    for case in load_evaluation_benchmark():
        if not case.legacyAliases:
            raise ValueError(f"evaluation case {case.caseId!r} has no legacy alias for the E3 view")
        cases.append(
            BenchmarkCase(
                caseId=case.legacyAliases[0],
                corpusId=case.corpusId,
                question=case.question,
                category=case.category,
                acceptableTools=case.acceptableTools,
                requiredEvidenceIds=case.requiredEvidenceIds,
                forbiddenEvidenceIds=case.forbiddenEvidenceIds,
                expectedCitationRoles=case.expectedCitationRoles,
                requiresCounterevidence=case.requiresCounterevidence,
                temporalConstraints=case.temporalConstraints,
                expectedAbstention=case.expectedAbstention,
                unacceptableClaims=case.unacceptableClaims,
            )
        )
    return tuple(cases)


def _investigation_ids(investigation) -> set[str]:
    names = (
        "entities", "events", "decisions", "communications", "knowledgeStates",
        "claims", "relationships", "perspectives", "conflicts", "uncertainties",
        "researchGaps", "sources", "documents", "passages", "evidenceLinks",
        "claimLedgers", "timeline", "mapAssets", "mapScenes", "scenes",
    )
    return {
        item.id
        for name in names
        for item in getattr(investigation, name, ())
        if getattr(item, "id", None)
    }


def validate_benchmark_references(
    cases: Iterable[BenchmarkCase], registry: CorpusRegistry
) -> BenchmarkReferenceValidationReport:
    """Fail closed when a benchmark expectation is absent from its corpus."""

    materialized = tuple(cases)
    ids_by_corpus: dict[str, set[str]] = {}
    issues: list[BenchmarkReferenceIssue] = []
    count = 0
    for case in materialized:
        if case.corpusId not in ids_by_corpus:
            ids_by_corpus[case.corpusId] = _investigation_ids(
                registry.get_corpus(case.corpusId).get_investigation()
            )
        local_ids = ids_by_corpus[case.corpusId]
        references = (
            case.requiredEvidenceIds
            + case.forbiddenEvidenceIds
            + tuple(event_id for constraint in case.temporalConstraints for event_id in constraint.eventIds)
        )
        count += len(references)
        for record_id in references:
            if record_id not in local_ids:
                issues.append(BenchmarkReferenceIssue(
                    caseId=case.caseId,
                    recordId=record_id,
                    detail=f'not present in corpus "{case.corpusId}"',
                ))
    if issues:
        raise BenchmarkValidationError(tuple(issues))
    return BenchmarkReferenceValidationReport(
        valid=True,
        validatedCaseCount=len(materialized),
        validatedReferenceCount=count,
    )


def validate_evaluation_references(
    cases: "Iterable[EvaluationCase]", registry: CorpusRegistry
) -> BenchmarkReferenceValidationReport:
    """Fail closed when an evaluation expectation is absent from its own corpus,
    or (cross-corpus leakage) resolves inside a *different* registered corpus."""

    materialized = tuple(cases)
    ids_by_corpus: dict[str, set[str]] = {}

    def corpus_ids(corpus_id: str) -> set[str]:
        if corpus_id not in ids_by_corpus:
            ids_by_corpus[corpus_id] = _investigation_ids(
                registry.get_corpus(corpus_id).get_investigation()
            )
        return ids_by_corpus[corpus_id]

    other_corpus_ids = list(registry.list_corpus_ids())
    issues: list[BenchmarkReferenceIssue] = []
    count = 0
    for case in materialized:
        local_ids = corpus_ids(case.corpusId)
        references = (
            case.requiredEvidenceIds
            + case.forbiddenEvidenceIds
            + tuple(eid for c in case.temporalConstraints for eid in c.eventIds)
            + tuple(
                rid
                for check in case.semanticChecks
                for rid in (check.subjectRecordId, check.objectRecordId, *check.supportingRecordIds)
            )
        )
        count += len(references)
        for record_id in references:
            if record_id in local_ids:
                continue
            elsewhere = [
                cid for cid in other_corpus_ids
                if cid != case.corpusId and record_id in corpus_ids(cid)
            ]
            detail = (
                f'leaks into corpus "{elsewhere[0]}"'
                if elsewhere
                else f'not present in corpus "{case.corpusId}"'
            )
            issues.append(
                BenchmarkReferenceIssue(caseId=case.caseId, recordId=record_id, detail=detail)
            )
    if issues:
        raise BenchmarkValidationError(tuple(issues))
    return BenchmarkReferenceValidationReport(
        valid=True,
        validatedCaseCount=len(materialized),
        validatedReferenceCount=count,
    )
