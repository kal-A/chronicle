"""Aggregation, gates, byte-stable rendering, and blinded export (E7.5)."""

from __future__ import annotations

import json

from chronicle.ai.contracts.analysis import AnalysisCitation, AnswerStatus
from chronicle.ai.evaluation.contracts import EvaluationCase, EvaluationProfile, StrategyId
from chronicle.ai.evaluation.reporting import (
    build_report,
    evaluate_gates,
    export_review,
    render_json,
    render_markdown,
)
from chronicle.ai.evaluation.strategies import EvaluationStatement, StrategyResult
from chronicle.ai.contracts.plan import QuestionType


def _case(**kw) -> EvaluationCase:
    base = dict(
        caseId="direct-reported-assurance",
        legacyAliases=("bc-01",),
        benchmarkVersion="e7-v1",
        corpusId="blank-cheque-golden",
        question="What did the report state?",
        category=QuestionType.DIRECT_EVIDENCE,
        profiles=(EvaluationProfile.DETERMINISTIC_FULL,),
        acceptableTools=("search_passages",),
    )
    base.update(kw)
    return EvaluationCase(**base)


def _result(statements=(), *, status=AnswerStatus.ANSWERED, answer_text="", **kw) -> StrategyResult:
    base = dict(
        caseId="direct-reported-assurance",
        strategyId=StrategyId.BASIC_RAG,
        corpusId="blank-cheque-golden",
        answerStatus=status,
        answerText=answer_text,
        statements=tuple(statements),
        references=None,
        modelCallCount=1,
        latencyMs=0.0,
        benchmarkVersion="e7-v1",
        providerName="deterministic",
        providerVersion="e1-deterministic-v1",
        modelName="deterministic-test-model",
        promptVersions=("eval-basic-rag-v1",),
        repeat=0,
    )
    base.update(kw)
    return StrategyResult(**base)


def _report(results, cases=None):
    cases = cases or {"direct-reported-assurance": _case()}
    return build_report(
        cases,
        results,
        benchmark_version="e7-v1",
        profile=EvaluationProfile.DETERMINISTIC_FULL,
        foreign_ids_by_corpus={},
    )


def test_report_bytes_are_stable_for_identical_input():
    results = [_result((EvaluationStatement(statementId="s1", text="a", citations=()),))]
    first = render_json(_report(results))
    second = render_json(_report(results))
    assert first == second
    md_first = render_markdown(_report(results))
    md_second = render_markdown(_report(results))
    assert md_first == md_second


def test_markdown_escapes_model_supplied_text():
    citation = AnalysisCitation(toolCallId="baseline", passageId="evidence-forbidden-1")
    result = _result(
        (EvaluationStatement(statementId="s1", text="x", citations=(citation,)),),
        answer_text="<script>alert('x')&`bad`",
    )
    case = _case(forbiddenEvidenceIds=("evidence-forbidden-1",))
    markdown = render_markdown(_report([result], cases={"direct-reported-assurance": case}))
    assert "<script>" not in markdown
    assert "&lt;script&gt;" in markdown


def test_zero_denominator_metric_is_not_applicable_never_zero():
    # An answered result with no statements -> coverage denominator 0 -> N/A.
    report = _report([_result(())])
    coverage = next(
        metric
        for strategy in report.aggregate.strategies
        for metric in strategy.metrics
        if metric.name == "citation_coverage"
    )
    assert coverage.applicability == "not_applicable"
    assert coverage.value is None


def test_leakage_gate_fails_when_a_foreign_id_is_cited():
    citation = AnalysisCitation(toolCallId="baseline", passageId="foreign-1")
    result = _result((EvaluationStatement(statementId="s1", text="x", citations=(citation,)),))
    report = build_report(
        {"direct-reported-assurance": _case()},
        [result],
        benchmark_version="e7-v1",
        profile=EvaluationProfile.DETERMINISTIC_FULL,
        foreign_ids_by_corpus={"blank-cheque-golden": frozenset({"foreign-1"})},
    )
    leakage = next(g for g in report.gates if g.gateId == "no_cross_corpus_leakage")
    assert leakage.status == "fail"


def test_human_gates_are_incomplete_not_passed():
    report = _report([_result((EvaluationStatement(statementId="s1", text="a", citations=()),))])
    human = [g for g in report.gates if g.gateId in {"semantic_entailment", "usefulness"}]
    assert human and all(g.status == "incomplete" for g in human)


def test_export_review_strips_identity_and_writes_a_separate_key(tmp_path):
    # Two persisted results in a run dir.
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    for strategy in (StrategyId.SINGLE_PROMPT, StrategyId.BASIC_RAG):
        result = _result(answer_text="an answer", strategyId=strategy)
        envelope = {
            "benchmarkVersion": "e7-v1",
            "caseFileSha256": "0" * 64,
            "identity": {
                "caseId": "direct-reported-assurance",
                "strategyId": strategy.value,
                "repeat": 0,
            },
            "result": json.loads(result.model_dump_json()),
        }
        (results_dir / f"direct-reported-assurance__{strategy.value}__r0.json").write_text(
            json.dumps(envelope), encoding="utf-8"
        )

    review_path = tmp_path / "review.json"
    key_path = tmp_path / "review.key.json"
    export_review(tmp_path, review_path, key_path=key_path, shuffle_seed=7)

    review = json.loads(review_path.read_text(encoding="utf-8"))
    blob = json.dumps(review)
    # No strategy/provider labels leak into the reviewer's copy.
    assert "single_prompt" not in blob and "basic_rag" not in blob
    assert "deterministic" not in blob
    # The blinding key maps opaque review ids back to identities, separately.
    key = json.loads(key_path.read_text(encoding="utf-8"))
    assert len(key) == 2
