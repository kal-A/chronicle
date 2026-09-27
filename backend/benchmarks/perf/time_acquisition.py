"""Measure the acquisition phase (Phase A) wall-clock: cold vs warm cache.

Runs the real AcquisitionPipeline against free sources (Wikipedia / Gutenberg /
Internet Archive + in-repo doc registers) for one topic, twice: once with an
empty FetchCache (cold, network-bound) and once against the now-warm cache
(measures the cached-rebuild cost). Lexical path only -- no enrichment, no
embeddings, no model calls -- so this isolates discovery + fetch + chunk +
package build.

Usage (from ``backend/``, needs network):

    python -m benchmarks.perf.time_acquisition \
        --topic "Congress of Vienna" --earliest 1814 --latest 1815 \
        --max-sources 6 --out benchmarks/perf/results/acquisition.json

Live-network dependent: absolute numbers vary with the source APIs' health and
the network. This measures, it does not estimate.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from chronicle.acquisition.defaults import default_connectors
from chronicle.acquisition.fetch_cache import FetchCache
from chronicle.acquisition.pipeline import AcquisitionPipeline

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_once(cache_dir: Path, topic: str, question: str, scope: list[str], earliest: int, latest: int, max_sources: int):
    connectors = default_connectors(REPO_ROOT)
    pipeline = AcquisitionPipeline(connectors, FetchCache(cache_dir), per_connector_results=3)
    start = time.perf_counter()
    result = pipeline.run(
        topic=topic,
        interpreted_question=question,
        geographic_scope=scope,
        date_earliest=date(earliest, 1, 1) if earliest >= 1 else None,
        date_latest=date(latest, 12, 31) if latest >= 1 else None,
        year_earliest=earliest,
        year_latest=latest,
        max_sources=max_sources,
    )
    elapsed = time.perf_counter() - start
    return elapsed, result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", default="Congress of Vienna")
    parser.add_argument("--question", default=None)
    parser.add_argument("--scope", default="Europe")
    parser.add_argument("--earliest", type=int, default=1814)
    parser.add_argument("--latest", type=int, default=1815)
    parser.add_argument("--max-sources", type=int, default=6)
    parser.add_argument("--out", default="benchmarks/perf/results/acquisition.json")
    args = parser.parse_args()

    question = args.question or f"What happened regarding {args.topic}?"
    scope = [s.strip() for s in args.scope.split(",") if s.strip()]
    cache_dir = Path(tempfile.gettempdir()) / "chronicle-perf-acquire"
    if cache_dir.exists():
        shutil.rmtree(cache_dir, ignore_errors=True)

    print(f"COLD run (empty cache): {args.topic!r} {args.earliest}-{args.latest} max_sources={args.max_sources}")
    cold_s, cold = _run_once(cache_dir, args.topic, question, scope, args.earliest, args.latest, args.max_sources)
    print(f"  cold={cold_s:.1f}s  discovered={cold.discovered} acquired={cold.acquired} passages={cold.passages}")

    print("WARM run (cache populated):")
    warm_s, warm = _run_once(cache_dir, args.topic, question, scope, args.earliest, args.latest, args.max_sources)
    print(f"  warm={warm_s:.1f}s  discovered={warm.discovered} acquired={warm.acquired} passages={warm.passages}")

    report = {
        "topic": args.topic,
        "years": [args.earliest, args.latest],
        "max_sources": args.max_sources,
        "cold_seconds": round(cold_s, 1),
        "warm_seconds": round(warm_s, 1),
        "discovered": cold.discovered,
        "acquired": cold.acquired,
        "passages": cold.passages,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
