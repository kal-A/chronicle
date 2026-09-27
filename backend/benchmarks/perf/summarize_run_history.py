"""Summarize timings already recorded in persisted agent-run records.

Every completed run under ``runs/`` carries real, measured per-stage latency
(AgentStageRecord.latencyMs) and per-model-call latency. This tool aggregates
that existing evidence by model, so historical 7B/14B runs (which reach the
critic/guide stages a small model may not) contribute measured numbers without
re-running anything.

Usage (from ``backend/``):

    python -m benchmarks.perf.summarize_run_history \
        --runs-dir runs --out benchmarks/perf/results/run-history.json

Only runs whose stages carry non-zero latency are counted (i.e. real
model-backed runs, not deterministic/test fixtures). This reads on-disk data
only; it makes no model or network calls.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import statistics
from collections import defaultdict
from pathlib import Path

STAGES = ["planner", "retrieval", "analyst", "critic", "guide"]


def _agg(values: list[float]) -> dict:
    values = [v for v in values if v]
    if not values:
        return {"n": 0}
    return {
        "n": len(values),
        "mean_s": round(statistics.mean(values) / 1000, 1),
        "min_s": round(min(values) / 1000, 1),
        "max_s": round(max(values) / 1000, 1),
        "stdev_s": round(statistics.stdev(values) / 1000, 1) if len(values) > 1 else 0.0,
    }


def _dominant_model(record: dict) -> str:
    names = [mc.get("modelName") for mc in record.get("modelCalls", []) if mc.get("modelName")]
    if not names:
        for stage in record.get("stages", []):
            names += [mc.get("modelName") for mc in stage.get("modelCalls", []) if mc.get("modelName")]
    return max(set(names), key=names.count) if names else "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-dir", default="runs")
    parser.add_argument("--exclude", default="perf-benchmark", help="path substring to skip")
    parser.add_argument("--out", default="benchmarks/perf/results/run-history.json")
    args = parser.parse_args()

    files = [
        f
        for f in glob.glob(os.path.join(args.runs_dir, "**", "*.json"), recursive=True)
        if args.exclude not in f.replace("\\", "/")
    ]

    by_model_e2e: dict[str, list[float]] = defaultdict(list)
    by_model_status: dict[str, list[str]] = defaultdict(list)
    by_model_stage: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    by_model_stage_model_ms: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    counted = 0

    for f in files:
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict) or "stages" not in d:
            continue
        stages = d.get("stages", [])
        total = sum((s.get("latencyMs") or 0) for s in stages)
        if total <= 0:
            continue  # deterministic/test run with no measured latency
        counted += 1
        model = _dominant_model(d)
        by_model_e2e[model].append(total)
        by_model_status[model].append(d.get("status", "?"))
        for s in stages:
            name = s.get("stageName")
            if name in STAGES and s.get("latencyMs"):
                by_model_stage[model][name].append(s.get("latencyMs"))
                by_model_stage_model_ms[model][name].append(
                    sum((mc.get("latencyMs") or 0) for mc in s.get("modelCalls", []))
                )

    report = {
        "runs_dir": args.runs_dir,
        "files_scanned": len(files),
        "runs_with_measured_latency": counted,
        "by_model": {},
    }
    for model in sorted(by_model_e2e):
        from collections import Counter

        report["by_model"][model] = {
            "runs": len(by_model_e2e[model]),
            "statuses": dict(Counter(by_model_status[model])),
            "end_to_end_stage_sum": _agg(by_model_e2e[model]),
            "per_stage": {
                name: {
                    "stage": _agg(by_model_stage[model][name]),
                    "model_generation": _agg(by_model_stage_model_ms[model][name]),
                }
                for name in STAGES
                if by_model_stage[model].get(name)
            },
        }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
