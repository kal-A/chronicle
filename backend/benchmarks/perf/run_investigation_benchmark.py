"""Reproducible per-stage + end-to-end latency benchmark for the investigation phase.

Drives the *real* four-agent LangGraph workflow (the same objects
``chronicle.api.app.create_default_app`` wires, with the same live execution
policy) over a fixed curated corpus and a fixed question, N times, then reads
the timings the system already records on each run:

  - per stage (planner / retrieval / analyst / critic / guide): ``latencyMs``
  - per stage: model-generation time  = sum of ``modelCalls[].latencyMs``
  - per stage: deterministic overhead = ``latencyMs`` - model-generation time
    (prompt/context preparation + deterministic validation/finalization)
  - end-to-end: wall clock around ``workflow.run`` and the sum of stage latency

No product code is modified -- the timing fields (AgentStageRecord.latencyMs,
ModelCallRecord.latencyMs, PromptMeasurement) are already emitted by the
pipeline. This script only orchestrates repeats and aggregates.

Usage (from ``backend/``, with the venv active and Ollama running):

    python -m benchmarks.perf.run_investigation_benchmark \
        --corpus concert-of-europe-1814-1822 \
        --question "What did the Concert of Europe agree at the Congress of Vienna?" \
        --repeats 3 --model qwen2.5:3b-instruct \
        --out benchmarks/perf/results/investigation-3b.json

Network/model dependent: this needs a local Ollama daemon and the named model
pulled. It measures wall-clock, so absolute numbers are hardware-specific.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

import sys

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from chronicle.ai.agents.analyst import EvidenceAnalyst
from chronicle.ai.agents.critic import HistoricalCritic
from chronicle.ai.agents.guide import InvestigationGuide
from chronicle.ai.agents.planner import InvestigationPlanner
from chronicle.ai.agents.planner_prompt import ToolSpecRepresentation
from chronicle.ai.models.ollama import OllamaModelProvider, resolve_model_from_env
from chronicle.ai.orchestration.finalization import FinalizationRunner
from chronicle.ai.orchestration.graph import LangGraphAgentWorkflow
from chronicle.ai.orchestration.policies import AgentExecutionPolicy
from chronicle.ai.orchestration.runner import InvestigationRunner
from chronicle.ai.tools import build_default_registry
from chronicle.api.app import _make_run_record
from chronicle.corpus import CorpusRegistry
from chronicle.storage.agent_run_store import AgentRunStore


def build_workflow(store: AgentRunStore, provider: OllamaModelProvider) -> LangGraphAgentWorkflow:
    """Mirror create_default_app's wiring and live execution policy exactly."""

    policy = AgentExecutionPolicy(
        maxResultsPerTool=2,
        maxAggregateRetrievalCharacters=8_000,
    )
    analyst = EvidenceAnalyst(provider, policy)
    retrieval = InvestigationRunner(
        build_default_registry(), store=store, policy=policy, retrieval_floor=True
    )
    return LangGraphAgentWorkflow(
        planner=InvestigationPlanner(
            provider, policy, representation=ToolSpecRepresentation.COMPACT
        ),
        retrieval_runner=retrieval,
        analyst=analyst,
        finalization_runner=FinalizationRunner(
            retrieval_runner=retrieval,
            analyst=analyst,
            critic=HistoricalCritic(provider, policy),
            guide=InvestigationGuide(provider, policy),
            store=store,
        ),
        store=store,
    )


def _stage_rows(record) -> list[dict]:
    rows = []
    for stage in record.stages:
        model_ms = sum((mc.latencyMs or 0.0) for mc in stage.modelCalls)
        stage_ms = stage.latencyMs or 0.0
        rows.append(
            {
                "stage": stage.stageName.value,
                "round": stage.round,
                "status": stage.status.value,
                "stage_ms": stage_ms,
                "model_ms": model_ms,
                "overhead_ms": max(stage_ms - model_ms, 0.0),
                "prompt_chars": (
                    stage.promptMeasurement.promptCharacters
                    if stage.promptMeasurement
                    else None
                ),
            }
        )
    return rows


def _agg(values: list[float]) -> dict:
    values = [v for v in values if v is not None]
    if not values:
        return {"n": 0}
    return {
        "n": len(values),
        "mean_s": round(statistics.mean(values) / 1000, 2),
        "min_s": round(min(values) / 1000, 2),
        "max_s": round(max(values) / 1000, 2),
        "stdev_s": round(statistics.stdev(values) / 1000, 2) if len(values) > 1 else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", default="concert-of-europe-1814-1822")
    parser.add_argument(
        "--question",
        default="What did the Concert of Europe agree at the Congress of Vienna?",
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--model", default=None, help="overrides CHRONICLE_OLLAMA_MODEL")
    parser.add_argument("--out", default="benchmarks/perf/results/investigation.json")
    args = parser.parse_args()

    if args.model:
        os.environ["CHRONICLE_OLLAMA_MODEL"] = args.model
    model = resolve_model_from_env()

    registry = CorpusRegistry()
    corpus = registry.get_corpus(args.corpus)

    store_root = Path(os.environ.get("CHRONICLE_BENCH_RUN_DIR", "runs/perf-benchmark"))
    store = AgentRunStore(store_root)
    provider = OllamaModelProvider(timeout=float(os.environ.get("CHRONICLE_OLLAMA_TIMEOUT", "300")))
    workflow = build_workflow(store, provider)

    runs = []
    for i in range(1, args.repeats + 1):
        run_id = f"perf-{model.replace(':', '_')}-{int(time.time())}-{i}"
        record = _make_run_record(corpus, run_id=run_id, question=args.question)
        start = time.perf_counter()
        result = workflow.run(record, corpus)
        wall_s = time.perf_counter() - start
        stage_rows = _stage_rows(result)
        runs.append(
            {
                "run_id": run_id,
                "status": result.status.value,
                "wall_s": round(wall_s, 2),
                "sum_stage_s": round(sum(r["stage_ms"] for r in stage_rows) / 1000, 2),
                "stages": stage_rows,
            }
        )
        print(
            f"  run {i}/{args.repeats}: {result.status.value} "
            f"wall={wall_s:.1f}s stages={sum(r['stage_ms'] for r in stage_rows)/1000:.1f}s"
        )

    # Aggregate per stage across runs.
    stage_names = ["planner", "retrieval", "analyst", "critic", "guide"]
    per_stage = {}
    for name in stage_names:
        stage_ms = [r["stage_ms"] for run in runs for r in run["stages"] if r["stage"] == name]
        model_ms = [r["model_ms"] for run in runs for r in run["stages"] if r["stage"] == name]
        overhead_ms = [r["overhead_ms"] for run in runs for r in run["stages"] if r["stage"] == name]
        if stage_ms:
            per_stage[name] = {
                "stage": _agg(stage_ms),
                "model_generation": _agg(model_ms),
                "deterministic_overhead": _agg(overhead_ms),
            }

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "corpus": args.corpus,
        "question": args.question,
        "repeats": args.repeats,
        "end_to_end_wall": _agg([r["wall_s"] * 1000 for r in runs]),
        "per_stage": per_stage,
        "runs": runs,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nend-to-end wall: {report['end_to_end_wall']}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
