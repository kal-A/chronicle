"""`chronicle evaluate` command implementations (E7.4).

Thin and directly testable (no argparse here). The ``deterministic`` provider
is the fast, reproducible default (a null/scripted provider -- a floor + safety
baseline). The ``ollama`` provider runs the real local model over the same
cases/metrics for a model-quality baseline; it needs a running Ollama daemon
and is slow/CPU-bound (bound the run with --max-cases / --strategies).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TextIO

from ..ai.evaluation.benchmark import (
    corpus_record_ids,
    load_evaluation_benchmark,
    load_registry,
)
from ..ai.evaluation.contracts import EvaluationProfile, StrategyId
from ..ai.evaluation.reporting import (
    build_report,
    export_review,
    foreign_ids_by_corpus,
    render_json,
    render_markdown,
)
from ..ai.evaluation.runner import load_manifest, load_results, run_benchmark
from ..ai.evaluation.strategies import build_strategies
from ..ai.models.deterministic import DeterministicModelProvider
from ..ai.models.ollama import OllamaModelProvider, resolve_timeout_from_env
from ..corpus.manifest import CorpusRegistry


def _provider_factory(provider: str):
    if provider == "deterministic":
        return lambda case, strategy, repeat: DeterministicModelProvider()
    if provider == "ollama":
        # Real local-model baseline. Shares one provider config across the run;
        # the model tag comes from CHRONICLE_OLLAMA_MODEL (see ollama.py). Slow
        # and CPU-bound -- bound the run with --max-cases / --strategies.
        timeout = resolve_timeout_from_env(300.0)
        return lambda case, strategy, repeat: OllamaModelProvider(timeout=timeout)
    return None


def cmd_evaluate_run(
    *,
    profile: str,
    provider: str,
    output: str,
    cases: str | None,
    strategies: str | None,
    max_cases: int | None,
    repeats: int,
    out: TextIO = sys.stdout,
) -> int:
    try:
        evaluation_profile = EvaluationProfile(profile)
    except ValueError:
        valid = ", ".join(p.value for p in EvaluationProfile)
        print(f'Unknown profile "{profile}". Valid profiles: {valid}', file=out)
        return 2

    factory = _provider_factory(provider)
    if factory is None:
        print(f'Provider "{provider}" is not available in this slice (use "deterministic").', file=out)
        return 2

    strategy_filter: list[StrategyId] | None = None
    if strategies:
        try:
            strategy_filter = [StrategyId(token.strip()) for token in strategies.split(",") if token.strip()]
        except ValueError:
            valid = ", ".join(s.value for s in StrategyId)
            print(f"Unknown strategy in {strategies!r}. Valid strategies: {valid}", file=out)
            return 2

    case_filter = [token.strip() for token in cases.split(",") if token.strip()] if cases else None

    manifest = run_benchmark(
        load_registry(),
        load_evaluation_benchmark(),
        build_strategies(),
        factory,
        CorpusRegistry(),
        profile=evaluation_profile,
        output_dir=Path(output),
        cases_filter=case_filter,
        strategies_filter=strategy_filter,
        max_cases=max_cases,
        repeats=repeats,
    )

    total = len(manifest.completed) + len(manifest.remaining)
    print(f"Run {manifest.runId}", file=out)
    print(f"  profile: {manifest.profile.value}", file=out)
    print(f"  provider: {manifest.providerName} ({manifest.providerVersion})", file=out)
    print(f"  completed {len(manifest.completed)} of {total} identities", file=out)
    print(f"  output: {output}", file=out)
    return 0


def cmd_evaluate_status(run: str, out: TextIO = sys.stdout) -> int:
    manifest = load_manifest(Path(run))
    if manifest is None:
        print(f'No evaluation run found at "{run}"', file=out)
        return 2

    total = len(manifest.completed) + len(manifest.remaining)
    print(f"Run {manifest.runId}", file=out)
    print(f"  profile: {manifest.profile.value}", file=out)
    print(f"  benchmark: {manifest.benchmarkVersion}", file=out)
    print(f"  provider: {manifest.providerName} ({manifest.providerVersion})", file=out)
    print(f"  completed: {len(manifest.completed)} of {total}", file=out)
    print(f"  remaining: {len(manifest.remaining)}", file=out)
    return 0


def cmd_evaluate_report(
    run: str,
    output_json: str | None = None,
    output_md: str | None = None,
    out: TextIO = sys.stdout,
) -> int:
    manifest = load_manifest(Path(run))
    if manifest is None:
        print(f'No evaluation run found at "{run}"', file=out)
        return 2
    results = [result for _identity, result in load_results(run)]
    if not results:
        print(f'No results to report at "{run}"', file=out)
        return 2

    cases = {case.caseId: case for case in load_evaluation_benchmark()}
    foreign = foreign_ids_by_corpus(corpus_record_ids(CorpusRegistry()))
    report = build_report(
        cases,
        results,
        benchmark_version=manifest.benchmarkVersion,
        profile=manifest.profile,
        foreign_ids_by_corpus=foreign,
    )

    json_path = Path(output_json) if output_json else Path(run) / "report.json"
    md_path = Path(output_md) if output_md else Path(run) / "report.md"
    json_path.write_text(render_json(report), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")

    failed = [g for g in report.gates if g.status == "fail"]
    print(f"Report written: {json_path} , {md_path}", file=out)
    print(f"  strategies: {len(report.aggregate.strategies)}", file=out)
    print(f"  gates failed: {len(failed)}", file=out)
    print(f"  flagged answers: {len(report.flagged)}", file=out)
    return 0


def cmd_evaluate_export_review(
    run: str,
    output: str,
    seed: int,
    key: str | None = None,
    out: TextIO = sys.stdout,
) -> int:
    if load_manifest(Path(run)) is None:
        print(f'No evaluation run found at "{run}"', file=out)
        return 2
    export_review(run, output, key_path=key, shuffle_seed=seed)
    print(f"Blinded review written: {output}", file=out)
    return 0
