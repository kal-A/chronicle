"""Deterministic aggregation, gates, byte-stable reports, and a single-reviewer
blinded export (E7.5).

Everything here is machine-checkable. Dimensions that need a human (semantic
entailment, usefulness) are emitted as ``incomplete`` gates, never silently
passed. Reports are byte-stable for identical inputs (no wall-clock, sorted
collections), and any model-supplied text is HTML-escaped when rendered.
"""

from __future__ import annotations

import html
import json
import random
from pathlib import Path
from typing import Literal, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field

from .benchmark import load_evaluation_benchmark
from .contracts import EvaluationCase, EvaluationProfile, StrategyId
from .metrics import StrategyScore, score_result
from .runner import load_results
from .strategies import StrategyResult

REPORT_SCHEMA_VERSION = "e7-report-v1"

#: Deterministic gate thresholds (gate policy, not model output).
_VALIDITY_THRESHOLD = 0.95
_COVERAGE_THRESHOLD = 0.80
_RECALL_THRESHOLD = 0.80

#: Ratio metrics: (name, numerator field, denominator field).
_RATIO_METRICS = (
    ("citation_validity", "citationValidNumerator", "citationValidDenominator"),
    ("citation_coverage", "coverageNumerator", "coverageDenominator"),
    ("required_evidence_recall", "requiredRecallNumerator", "requiredRecallDenominator"),
    ("role_recall", "roleRecallNumerator", "roleRecallDenominator"),
    ("temporal_coverage", "temporalNumerator", "temporalDenominator"),
)

Applicability = Literal["applicable", "not_applicable", "incomplete"]
GateStatus = Literal["pass", "fail", "incomplete", "not_applicable"]


class MetricAggregate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    numerator: int = Field(ge=0)
    denominator: int = Field(ge=0)
    value: float | None = None
    applicability: Applicability
    contributingCases: tuple[str, ...] = ()


class StrategyAggregate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    strategyId: StrategyId
    resultCount: int = Field(ge=0)
    metrics: tuple[MetricAggregate, ...]


class AggregateReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    strategies: tuple[StrategyAggregate, ...] = ()


class GateResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    gateId: str
    strategyId: StrategyId | None = None
    status: GateStatus
    detail: str


class FlaggedResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    caseId: str
    strategyId: StrategyId
    reason: str
    answerExcerpt: str


class EvaluationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    reportSchemaVersion: str
    benchmarkVersion: str
    profile: EvaluationProfile
    aggregate: AggregateReport
    gates: tuple[GateResult, ...]
    flagged: tuple[FlaggedResult, ...] = ()


def _ratio_metric(name: str, num_field: str, den_field: str, scores: Sequence[StrategyScore]) -> MetricAggregate:
    numerator = sum(getattr(s, num_field) for s in scores)
    denominator = sum(getattr(s, den_field) for s in scores)
    contributing = tuple(sorted({s.caseId for s in scores if getattr(s, den_field) > 0}))
    if denominator == 0:
        return MetricAggregate(
            name=name, numerator=0, denominator=0, value=None,
            applicability="not_applicable", contributingCases=contributing,
        )
    return MetricAggregate(
        name=name, numerator=numerator, denominator=denominator,
        value=numerator / denominator, applicability="applicable",
        contributingCases=contributing,
    )


def _count_metric(name: str, attr: str, scores: Sequence[StrategyScore]) -> MetricAggregate:
    numerator = sum(len(getattr(s, attr)) for s in scores)
    denominator = len(scores)
    contributing = tuple(sorted({s.caseId for s in scores if getattr(s, attr)}))
    return MetricAggregate(
        name=name, numerator=numerator, denominator=denominator,
        value=(numerator / denominator if denominator else None),
        applicability="applicable" if denominator else "not_applicable",
        contributingCases=contributing,
    )


def _abstention_metric(scores: Sequence[StrategyScore]) -> MetricAggregate:
    numerator = sum(1 for s in scores if s.abstentionCorrect)
    denominator = len(scores)
    contributing = tuple(sorted({s.caseId for s in scores if not s.abstentionCorrect}))
    return MetricAggregate(
        name="abstention_correct", numerator=numerator, denominator=denominator,
        value=(numerator / denominator if denominator else None),
        applicability="applicable" if denominator else "not_applicable",
        contributingCases=contributing,
    )


def aggregate(scores: Sequence[StrategyScore]) -> AggregateReport:
    """Group scores by strategy (in StrategyId declaration order) and sum each
    metric's numerator/denominator exactly."""

    strategies: list[StrategyAggregate] = []
    for strategy_id in StrategyId:
        subset = [s for s in scores if s.strategyId is strategy_id]
        if not subset:
            continue
        metrics = [_ratio_metric(name, n, d, subset) for name, n, d in _RATIO_METRICS]
        metrics.append(_abstention_metric(subset))
        metrics.append(_count_metric("forbidden_evidence_hits", "forbiddenHits", subset))
        metrics.append(_count_metric("cross_corpus_leakage", "leakageHits", subset))
        metrics.append(_count_metric("unacceptable_claims", "unacceptableClaimHits", subset))
        strategies.append(
            StrategyAggregate(strategyId=strategy_id, resultCount=len(subset), metrics=tuple(metrics))
        )
    return AggregateReport(strategies=tuple(strategies))


def _metric(strategy: StrategyAggregate, name: str) -> MetricAggregate:
    return next(m for m in strategy.metrics if m.name == name)


def _ratio_gate(strategy: StrategyAggregate, gate_id: str, metric_name: str, threshold: float) -> GateResult:
    metric = _metric(strategy, metric_name)
    if metric.applicability != "applicable" or metric.value is None:
        return GateResult(gateId=gate_id, strategyId=strategy.strategyId, status="not_applicable",
                          detail=f"{metric_name} has no applicable denominator")
    passed = metric.value >= threshold
    return GateResult(
        gateId=gate_id, strategyId=strategy.strategyId,
        status="pass" if passed else "fail",
        detail=f"{metric_name}={metric.value:.3f} (threshold {threshold:.2f})",
    )


def evaluate_gates(report: AggregateReport) -> tuple[GateResult, ...]:
    """Only gates computable without human judgment; human-dependent dimensions
    are reported as ``incomplete`` so they cannot be mistaken for a pass."""

    gates: list[GateResult] = []
    for strategy in report.strategies:
        forbidden = _metric(strategy, "forbidden_evidence_hits")
        leakage = _metric(strategy, "cross_corpus_leakage")
        abstention = _metric(strategy, "abstention_correct")
        gates.append(GateResult(
            gateId="no_forbidden_evidence", strategyId=strategy.strategyId,
            status="fail" if forbidden.numerator > 0 else "pass",
            detail=f"{forbidden.numerator} forbidden citation(s)",
        ))
        gates.append(GateResult(
            gateId="no_cross_corpus_leakage", strategyId=strategy.strategyId,
            status="fail" if leakage.numerator > 0 else "pass",
            detail=f"{leakage.numerator} cross-corpus citation(s)",
        ))
        gates.append(_ratio_gate(strategy, "citation_validity", "citation_validity", _VALIDITY_THRESHOLD))
        gates.append(_ratio_gate(strategy, "citation_coverage", "citation_coverage", _COVERAGE_THRESHOLD))
        gates.append(_ratio_gate(strategy, "required_evidence_recall", "required_evidence_recall", _RECALL_THRESHOLD))
        gates.append(GateResult(
            gateId="abstention_correctness", strategyId=strategy.strategyId,
            status="pass" if abstention.numerator == abstention.denominator else "fail",
            detail=f"{abstention.numerator}/{abstention.denominator} abstention decisions correct",
        ))
    # Human-judgment gates: never auto-passed.
    gates.append(GateResult(gateId="semantic_entailment", strategyId=None, status="incomplete",
                            detail="requires the single blinded human review (Slice 2)"))
    gates.append(GateResult(gateId="usefulness", strategyId=None, status="incomplete",
                            detail="requires the single blinded human review (Slice 2)"))
    return tuple(gates)


def build_report(
    cases: Mapping[str, EvaluationCase],
    results: Sequence[StrategyResult],
    *,
    benchmark_version: str,
    profile: EvaluationProfile,
    foreign_ids_by_corpus: Mapping[str, frozenset[str]],
    report_schema_version: str = REPORT_SCHEMA_VERSION,
) -> EvaluationReport:
    """Score every result, aggregate, run gates, and capture flagged answers."""

    scores: list[StrategyScore] = []
    flagged: list[FlaggedResult] = []
    for result in results:
        case = cases[result.caseId]
        foreign = foreign_ids_by_corpus.get(result.corpusId, frozenset())
        score = score_result(case, result, foreign_ids=foreign)
        scores.append(score)
        reasons = []
        if score.forbiddenHits:
            reasons.append(f"forbidden: {', '.join(score.forbiddenHits)}")
        if score.leakageHits:
            reasons.append(f"leakage: {', '.join(score.leakageHits)}")
        if score.unacceptableClaimHits:
            reasons.append(f"unacceptable-claim: {', '.join(score.unacceptableClaimHits)}")
        if reasons:
            flagged.append(FlaggedResult(
                caseId=result.caseId, strategyId=result.strategyId,
                reason="; ".join(reasons), answerExcerpt=result.answerText[:280],
            ))

    report_aggregate = aggregate(scores)
    return EvaluationReport(
        reportSchemaVersion=report_schema_version,
        benchmarkVersion=benchmark_version,
        profile=profile,
        aggregate=report_aggregate,
        gates=evaluate_gates(report_aggregate),
        flagged=tuple(sorted(flagged, key=lambda f: (f.caseId, f.strategyId.value))),
    )


def render_json(report: EvaluationReport) -> str:
    """Byte-stable JSON (Pydantic preserves field/collection order)."""

    return report.model_dump_json(indent=2)


def _escape(text: str) -> str:
    return html.escape(text, quote=False).replace("`", "&#96;")


def render_markdown(report: EvaluationReport) -> str:
    lines: list[str] = [
        f"# Evaluation report ({report.benchmarkVersion}, {report.profile.value})",
        "",
        f"Report schema: {report.reportSchemaVersion}",
        "",
    ]
    for strategy in report.aggregate.strategies:
        lines.append(f"## {strategy.strategyId.value} ({strategy.resultCount} results)")
        lines.append("")
        lines.append("| Metric | Value | n/d | Applicability |")
        lines.append("| --- | --- | --- | --- |")
        for metric in strategy.metrics:
            value = "—" if metric.value is None else f"{metric.value:.3f}"
            lines.append(
                f"| {metric.name} | {value} | {metric.numerator}/{metric.denominator} | {metric.applicability} |"
            )
        lines.append("")
    lines.append("## Gates")
    lines.append("")
    lines.append("| Gate | Strategy | Status | Detail |")
    lines.append("| --- | --- | --- | --- |")
    for gate in report.gates:
        strategy = gate.strategyId.value if gate.strategyId else "—"
        lines.append(f"| {gate.gateId} | {strategy} | {gate.status} | {_escape(gate.detail)} |")
    lines.append("")
    if report.flagged:
        lines.append("## Flagged answers")
        lines.append("")
        for flag in report.flagged:
            lines.append(f"- **{flag.caseId} / {flag.strategyId.value}** — {_escape(flag.reason)}")
            lines.append(f"  > {_escape(flag.answerExcerpt)}")
        lines.append("")
    return "\n".join(lines)


def foreign_ids_by_corpus(record_ids: Mapping[str, frozenset[str]]) -> dict[str, frozenset[str]]:
    """For each corpus, the union of every *other* corpus's record IDs."""

    result: dict[str, frozenset[str]] = {}
    for corpus_id in record_ids:
        others: frozenset[str] = frozenset()
        for other_id, ids in record_ids.items():
            if other_id != corpus_id:
                others = others | ids
        result[corpus_id] = others
    return result


def export_review(
    run_dir: Path | str,
    output: Path | str,
    *,
    key_path: Path | str | None = None,
    shuffle_seed: int,
) -> None:
    """Write a blinded reviewer file: question + answer + citations only, with
    strategy/provider/model labels stripped and answer order shuffled by seed.
    The review-id -> identity map goes to a separate key file the reviewer never
    sees. Single reviewer only -- no Reviewer B, no kappa, no adjudication."""

    cases = {case.caseId: case for case in load_evaluation_benchmark()}
    pairs = load_results(run_dir)

    order = list(range(len(pairs)))
    random.Random(shuffle_seed).shuffle(order)

    review: list[dict] = []
    key: dict[str, dict] = {}
    for position, index in enumerate(order, start=1):
        identity, result = pairs[index]
        review_id = f"answer-{position:03d}"
        question = cases[result.caseId].question if result.caseId in cases else ""
        review.append({
            "reviewId": review_id,
            "question": question,
            "directAnswer": result.answerText,
            "statements": [
                {
                    "text": statement.text,
                    "citations": [citation.model_dump(mode="json") for citation in statement.citations],
                }
                for statement in result.statements
            ],
        })
        key[review_id] = {
            "caseId": identity.caseId,
            "strategyId": identity.strategyId.value,
            "repeat": identity.repeat,
        }

    Path(output).write_text(json.dumps(review, indent=2, sort_keys=True), encoding="utf-8")
    resolved_key = Path(key_path) if key_path is not None else Path(output).with_suffix(".key.json")
    resolved_key.write_text(json.dumps(key, indent=2, sort_keys=True), encoding="utf-8")


__all__ = [
    "MetricAggregate",
    "StrategyAggregate",
    "AggregateReport",
    "GateResult",
    "FlaggedResult",
    "EvaluationReport",
    "REPORT_SCHEMA_VERSION",
    "aggregate",
    "evaluate_gates",
    "build_report",
    "render_json",
    "render_markdown",
    "foreign_ids_by_corpus",
    "export_review",
]
