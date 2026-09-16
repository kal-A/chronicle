"""Contract tests for the E7 EvaluationCase / SemanticCheck schema (Slice 1).

These prove the topic-neutral case schema's invariants without any live model
or corpus: the deterministic guarantees the runner and scorer later depend on.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from chronicle.ai.contracts.plan import QuestionType
from chronicle.ai.evaluation.contracts import (
    EvaluationCase,
    EvaluationProfile,
    SemanticCheck,
    StrategyId,
)


def _minimal(**kw) -> EvaluationCase:
    base = dict(
        caseId="direct-reported-assurance",
        legacyAliases=("bc-01",),
        benchmarkVersion="e7-v1",
        corpusId="blank-cheque-golden",
        question="What did the report state?",
        category=QuestionType.DIRECT_EVIDENCE,
        profiles=(EvaluationProfile.DETERMINISTIC_FULL,),
        acceptableTools=("get_claim_evidence",),
    )
    base.update(kw)
    return EvaluationCase(**base)


def test_case_id_must_be_a_topic_neutral_slug():
    with pytest.raises(ValidationError):
        _minimal(caseId="bc-01")  # legacy alias shape is not a valid slug


def test_required_and_forbidden_evidence_must_be_disjoint():
    with pytest.raises(ValidationError):
        _minimal(requiredEvidenceIds=("x",), forbiddenEvidenceIds=("x",))


def test_counterevidence_case_requires_the_counterevidence_role():
    with pytest.raises(ValidationError):
        _minimal(requiresCounterevidence=True)  # no COUNTEREVIDENCE role expected


def test_semantic_check_records_directionality_flag():
    check = SemanticCheck(
        checkId="assurance-direction",
        subjectRecordId="a",
        relation="supports",
        objectRecordId="b",
        polarity="affirms",
        directionalityCritical=True,
        supportingRecordIds=("evidence-1",),
    )
    assert check.directionalityCritical is True


def test_strategy_ids_are_the_four_expected_strategies():
    assert {s.value for s in StrategyId} == {
        "single_prompt",
        "basic_rag",
        "planner_analyst",
        "full_workflow",
    }


def test_a_valid_case_round_trips_from_json():
    case = _minimal()
    reloaded = EvaluationCase.model_validate_json(case.model_dump_json())
    assert reloaded == case
