"""Freeze the retrieval evaluation's outcome so the recall gain (and the no-regression
/ no-noise controls) stay green in CI. The eval script lives under ``benchmarks/`` (not
collected by pytest), so it is imported here by path."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_EVAL_PATH = (
    Path(__file__).resolve().parents[2] / "benchmarks" / "e7" / "retrieval" / "run_retrieval_eval.py"
)


def _load_eval():
    spec = importlib.util.spec_from_file_location("run_retrieval_eval", _EVAL_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve types via sys.modules
    spec.loader.exec_module(module)
    return module


def test_retrieval_eval_matches_frozen_expectations():
    report = _load_eval().run_eval()
    agg = report["aggregate"]

    # Recall-additive retrieval surfaces two relevant passages the lexical lane missed.
    assert agg["lexicalRelevantRetrieved"] == 2
    assert agg["hybridRelevantRetrieved"] == 4
    assert agg["recallGain"] == 2
    # Fusion never returns the same passage twice.
    assert agg["duplicatePassageIdsTotal"] == 0

    cases = {c["caseId"]: c for c in report["cases"]}

    # The two evidence-rich cases each gain recall.
    assert cases["reworded-relevant"]["recallGain"] >= 1
    assert cases["pure-recall-lexical-empty"]["recallGain"] >= 1

    # Control: lexical already reaches the relevant source -> hybrid is identical.
    aligned = cases["aligned-no-regression"]
    assert aligned["hybridTitles"] == aligned["lexicalTitles"]
    assert aligned["hybridRelevant"] == aligned["lexicalRelevant"]

    # Absent evidence: the positive-similarity guard injects no noise.
    absent = cases["absent-evidence"]
    assert absent["hybridReturned"] == absent["lexicalReturned"] == 0
