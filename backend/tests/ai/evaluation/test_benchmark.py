from __future__ import annotations

from collections import Counter

import pytest

from chronicle.ai.contracts.plan import QuestionType
from chronicle.ai.evaluation import (
    BenchmarkCase,
    BenchmarkValidationError,
    EvaluationProfile,
    load_e3_benchmark,
    load_evaluation_benchmark,
    validate_benchmark_references,
    validate_evaluation_references,
)
from chronicle.corpus.manifest import CorpusRegistry


def test_evaluation_benchmark_has_all_24_cases_with_neutral_slugs() -> None:
    cases = load_evaluation_benchmark()

    assert len(cases) == 24
    assert all(not case.caseId.startswith(("bc-", "coe-")) for case in cases)
    aliases = {alias for case in cases for alias in case.legacyAliases}
    assert {"bc-01", "coe-01", "bc-12", "coe-12"}.issubset(aliases)


def test_evaluation_profiles_split_matches_the_scope_decision() -> None:
    cases = load_evaluation_benchmark()
    by_slug = {case.caseId: case for case in cases}

    assert all(EvaluationProfile.DETERMINISTIC_FULL in c.profiles for c in cases)
    gate = {c.caseId for c in cases if EvaluationProfile.QWEN_GATE in c.profiles}
    assert len(gate) == 10
    stability = {c.caseId for c in cases if EvaluationProfile.QWEN_STABILITY in c.profiles}
    assert stability == {"direct-reported-assurance", "counterevidence-extension-limits"}
    assert stability.issubset(gate)
    assert "disputed-causal-interpretations" in by_slug  # bc-07 present under its slug


def test_e3_compat_export_preserves_legacy_case_ids() -> None:
    legacy = {case.caseId for case in load_e3_benchmark()}

    assert len(legacy) == 24
    assert {"bc-01", "coe-12"}.issubset(legacy)


def test_evaluation_references_all_resolve_inside_their_own_corpus() -> None:
    report = validate_evaluation_references(load_evaluation_benchmark(), CorpusRegistry())

    assert report.valid is True
    assert report.validatedCaseCount == 24


def test_benchmark_has_24_isolated_cases_with_the_approved_corpus_split() -> None:
    cases = load_e3_benchmark()

    assert len(cases) == 24
    assert len({case.caseId for case in cases}) == 24
    assert Counter(case.corpusId for case in cases) == {
        "blank-cheque-golden": 12,
        "concert-of-europe-1814-1822": 12,
    }
    assert Counter(case.category for case in cases) == {
        QuestionType.DIRECT_EVIDENCE: 7,
        QuestionType.TIMELINE_ORDERING: 2,
        QuestionType.RELATIONSHIP_TRACE: 1,
        QuestionType.EXPLANATION: 1,
        QuestionType.SOURCE_COMPARISON: 2,
        QuestionType.ACTOR_KNOWLEDGE: 2,
        QuestionType.COUNTEREVIDENCE: 1,
        QuestionType.DISPUTED_INTERPRETATION: 1,
        QuestionType.MISSING_EVIDENCE: 3,
        QuestionType.INVALID_PREMISE: 2,
        QuestionType.OUT_OF_CORPUS: 2,
    }


def test_every_benchmark_reference_resolves_inside_its_declared_fixture() -> None:
    report = validate_benchmark_references(load_e3_benchmark(), CorpusRegistry())

    assert report.valid is True
    assert report.validatedCaseCount == 24
    assert report.validatedReferenceCount > 40
    assert report.issues == ()


def test_reference_validation_rejects_a_real_id_from_the_other_fixture() -> None:
    original = load_e3_benchmark()[0]
    contaminated = original.model_copy(
        update={"requiredEvidenceIds": ("claim-c1-assurance-reported",)}
    )

    with pytest.raises(BenchmarkValidationError, match="claim-c1-assurance-reported"):
        validate_benchmark_references((contaminated,), CorpusRegistry())


def test_cases_are_model_answer_free_and_reject_target_essays() -> None:
    case = load_e3_benchmark()[0]

    assert "targetAnswer" not in type(case).model_fields
    assert "referenceAnswer" not in type(case).model_fields
    with pytest.raises(ValueError):
        BenchmarkCase.model_validate({**case.model_dump(), "targetAnswer": "A model-ready essay."})


def test_counterevidence_cases_require_the_counterevidence_role() -> None:
    cases = [case for case in load_e3_benchmark() if case.requiresCounterevidence]

    assert {case.caseId for case in cases} == {"coe-07", "bc-06", "bc-07", "bc-10"}
    assert all("counterevidence" in {role.value for role in case.expectedCitationRoles} for case in cases)
