"""Freeze the E10 retrieval-breadth eval: decomposition assembles broader relevant
evidence, keeps diversity relevance-gated (no noise), and does not depend on source
count. The eval lives under benchmarks/ (not collected by pytest), imported by path."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_EVAL_PATH = (
    Path(__file__).resolve().parents[2] / "benchmarks" / "e7" / "retrieval" / "run_breadth_eval.py"
)


def _load_eval():
    spec = importlib.util.spec_from_file_location("run_breadth_eval", _EVAL_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve types via sys.modules
    spec.loader.exec_module(module)
    return module


def test_breadth_eval_matches_frozen_expectations():
    report = _load_eval().run_eval()
    cases = {c["caseId"]: c for c in report["cases"]}

    # Multi-aspect: one broad query reaches one aspect; decomposition reaches all three.
    multi = cases["multi-aspect"]
    assert multi["single"]["aspectsCovered"] == 1
    assert multi["decomposed"]["aspectsCovered"] == 3
    assert multi["decomposed"]["distinctRelevant"] > multi["single"]["distinctRelevant"]
    assert multi["decomposed"]["distinctRelevant"] == 6

    # Breadth is measured in evidence, not sources: distinct relevant passages grow
    # while source diversity stays 1.
    dom = cases["dominant-relevant-source"]
    assert dom["single"]["relevantSources"] == dom["decomposed"]["relevantSources"] == 1
    assert dom["decomposed"]["distinctRelevant"] > dom["single"]["distinctRelevant"]

    # Relevance-gated diversity: namesake noise sources are never pulled in.
    noise = cases["dominant-noise-source"]
    assert noise["single"]["noiseRetrieved"] == 0
    assert noise["decomposed"]["noiseRetrieved"] == 0
    assert noise["decomposed"]["distinctRelevant"] > noise["single"]["distinctRelevant"]

    # Fusion dedupes: no passage is double-counted within a query.
    for case in report["cases"]:
        assert 0.0 <= case["decomposed"]["duplicateRate"] <= 1.0
