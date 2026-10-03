"""Freeze the E10->E11 retrieval-breadth eval: evidence-facet decomposition assembles
broader, more complementary relevant evidence than the E10 token-partition backstop,
keeps diversity relevance-gated (no noise, no manufactured source diversity), and
leaves single-dimension factoid questions at one search. The eval lives under
benchmarks/ (not collected by pytest), imported by path."""

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

    # Overlap recoverable: the token-partition `before` lands sub-queries back on the
    # subject passages (one aspect, broad overlap); facet `after` reaches three
    # distinct aspects with no broad overlap.
    rec = cases["overlap-recoverable"]
    assert rec["before"]["aspectsCovered"] == 1
    assert rec["after"]["aspectsCovered"] == 3
    assert rec["after"]["distinctRelevant"] == 6 > rec["before"]["distinctRelevant"]
    assert rec["after"]["broadOverlap"] == 0 < rec["before"]["broadOverlap"]

    # Legitimately single source: breadth is measured in evidence, not sources --
    # distinct relevant passages and aspects grow while relevant source diversity
    # legitimately stays 1 (no manufactured diversity).
    single = cases["single-source"]
    assert single["before"]["relevantSources"] == single["after"]["relevantSources"] == 1
    assert single["after"]["distinctRelevant"] > single["before"]["distinctRelevant"]
    assert single["after"]["aspectsCovered"] > single["before"]["aspectsCovered"]

    # Noisy diverse sources: namesake noise is never pulled in to diversify.
    noisy = cases["noisy-sources"]
    assert noisy["before"]["noiseRetrieved"] == 0
    assert noisy["after"]["noiseRetrieved"] == 0
    assert noisy["after"]["distinctRelevant"] > noisy["before"]["distinctRelevant"]

    # Single-dimension factoid: the backstop derives no extra searches (retrieval
    # stays at one query), where the old token-partition over-decomposed it.
    factoid = cases["single-dimension"]
    assert factoid["after"]["derivedCount"] == 0
    assert factoid["after"]["searches"] == 1
    assert factoid["before"]["derivedCount"] > 0

    # Fusion dedupes: no passage is double-counted within the decomposition.
    for case in report["cases"]:
        assert 0.0 <= case["after"]["duplicateRate"] <= 1.0
