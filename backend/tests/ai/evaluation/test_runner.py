"""Resumable sequential runner (E7.4).

These tests exercise the runner's execution/resume/atomicity contract with stub
strategies, so they are independent of any one adapter's correctness (that lives
in test_strategies.py). A stub records which identities it was asked to run and
returns a canned, latency-free StrategyResult.
"""

from __future__ import annotations

import json

from chronicle.ai.contracts.analysis import AnswerStatus
from chronicle.ai.evaluation.benchmark import load_evaluation_benchmark, load_registry
from chronicle.ai.evaluation.contracts import EvaluationProfile, StrategyId
from chronicle.ai.evaluation.runner import RunManifest, run_benchmark
from chronicle.ai.evaluation.strategies import EvaluationInput, StrategyResult
from chronicle.ai.models.deterministic import DeterministicModelProvider
from chronicle.corpus import CorpusRegistry


class _StubStrategy:
    """A strategy that records its calls and returns a fixed result."""

    def __init__(self, strategy_id: StrategyId, marker: str = "stub-answer") -> None:
        self.id = strategy_id
        self._marker = marker
        self.calls: list[tuple[str, int]] = []

    def run(self, evaluation_input: EvaluationInput) -> StrategyResult:
        case = evaluation_input.case
        self.calls.append((case.caseId, evaluation_input.repeat))
        return StrategyResult(
            caseId=case.caseId,
            strategyId=self.id,
            corpusId=case.corpusId,
            answerStatus=AnswerStatus.ANSWERED,
            answerText=self._marker,
            statements=(),
            references=None,
            modelCallCount=1,
            latencyMs=0.0,
            benchmarkVersion=case.benchmarkVersion,
            providerName="deterministic",
            providerVersion="e1-deterministic-v1",
            modelName="deterministic-test-model",
            promptVersions=("stub-v1",),
            repeat=evaluation_input.repeat,
        )


def _provider_factory(case, strategy, repeat):  # noqa: ANN001 - test helper
    return DeterministicModelProvider()


def _two_cases():
    return load_evaluation_benchmark()[:2]


def test_interrupted_run_resumes_without_repeating_completed_identities(tmp_path):
    cases = _two_cases()
    registry = load_registry()
    corpus_registry = CorpusRegistry()
    output_dir = tmp_path / "run"

    first_stub = _StubStrategy(StrategyId.SINGLE_PROMPT)
    manifest = run_benchmark(
        registry,
        cases,
        {StrategyId.SINGLE_PROMPT: first_stub},
        _provider_factory,
        corpus_registry,
        profile=EvaluationProfile.DETERMINISTIC_FULL,
        output_dir=output_dir,
    )
    assert isinstance(manifest, RunManifest)
    assert len(first_stub.calls) == 2
    assert len(manifest.completed) == 2 and not manifest.remaining

    # Simulate an interruption: one identity's result file is lost.
    lost = output_dir / "results" / f"{cases[0].caseId}__single_prompt__r0.json"
    lost.unlink()

    second_stub = _StubStrategy(StrategyId.SINGLE_PROMPT)
    resumed = run_benchmark(
        registry,
        cases,
        {StrategyId.SINGLE_PROMPT: second_stub},
        _provider_factory,
        corpus_registry,
        profile=EvaluationProfile.DETERMINISTIC_FULL,
        output_dir=output_dir,
    )
    # Only the deleted identity is recomputed; the surviving one is not.
    assert second_stub.calls == [(cases[0].caseId, 0)]
    assert len(resumed.completed) == 2 and not resumed.remaining


def test_stale_result_is_recomputed_when_case_file_hash_changes(tmp_path):
    cases = _two_cases()
    registry = load_registry()
    corpus_registry = CorpusRegistry()
    output_dir = tmp_path / "run"

    run_benchmark(
        registry,
        cases,
        {StrategyId.SINGLE_PROMPT: _StubStrategy(StrategyId.SINGLE_PROMPT)},
        _provider_factory,
        corpus_registry,
        profile=EvaluationProfile.DETERMINISTIC_FULL,
        output_dir=output_dir,
    )

    # Rewrite one result as though it came from a different benchmark version.
    stale_path = output_dir / "results" / f"{cases[0].caseId}__single_prompt__r0.json"
    stale = json.loads(stale_path.read_text(encoding="utf-8"))
    stale["caseFileSha256"] = "0" * 64
    stale_path.write_text(json.dumps(stale), encoding="utf-8")

    stub = _StubStrategy(StrategyId.SINGLE_PROMPT)
    run_benchmark(
        registry,
        cases,
        {StrategyId.SINGLE_PROMPT: stub},
        _provider_factory,
        corpus_registry,
        profile=EvaluationProfile.DETERMINISTIC_FULL,
        output_dir=output_dir,
    )
    assert stub.calls == [(cases[0].caseId, 0)]  # the mismatched identity re-ran


def test_manifest_is_byte_stable_for_identical_inputs(tmp_path):
    cases = _two_cases()
    registry = load_registry()
    corpus_registry = CorpusRegistry()

    def run_into(name: str) -> bytes:
        output_dir = tmp_path / name
        run_benchmark(
            registry,
            cases,
            {StrategyId.SINGLE_PROMPT: _StubStrategy(StrategyId.SINGLE_PROMPT)},
            _provider_factory,
            corpus_registry,
            profile=EvaluationProfile.DETERMINISTIC_FULL,
            output_dir=output_dir,
        )
        return (output_dir / "manifest.json").read_bytes()

    assert run_into("a") == run_into("b")


def test_results_are_written_under_the_output_dir_only(tmp_path):
    cases = _two_cases()
    registry = load_registry()
    corpus_registry = CorpusRegistry()
    output_dir = tmp_path / "run"

    run_benchmark(
        registry,
        cases,
        {StrategyId.SINGLE_PROMPT: _StubStrategy(StrategyId.SINGLE_PROMPT)},
        _provider_factory,
        corpus_registry,
        profile=EvaluationProfile.DETERMINISTIC_FULL,
        output_dir=output_dir,
    )
    written = sorted(p.name for p in (output_dir / "results").glob("*.json"))
    assert written == sorted(f"{c.caseId}__single_prompt__r0.json" for c in cases)
