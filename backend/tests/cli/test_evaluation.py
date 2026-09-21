"""`chronicle evaluate` CLI (E7.4).

The deterministic provider is unscripted here, so real adapters abstain via the
runner's captured-error path; that is fine — these tests verify the CLI wiring,
manifest/result output, and status reporting, not adapter answers.
"""

from __future__ import annotations

import io
import json

from chronicle.cli import evaluation as evaluation_cli
from chronicle.cli import main as cli_main


def test_evaluate_run_writes_a_manifest_and_result_files(tmp_path):
    output = tmp_path / "run"
    out = io.StringIO()

    exit_code = evaluation_cli.cmd_evaluate_run(
        profile="deterministic_full",
        provider="deterministic",
        output=str(output),
        cases=None,
        strategies="single_prompt",
        max_cases=1,
        repeats=1,
        out=out,
    )

    assert exit_code == 0
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["benchmarkVersion"] == "e7-v1"
    assert len(manifest["completed"]) == 1 and not manifest["remaining"]
    results = list((output / "results").glob("*.json"))
    assert len(results) == 1
    assert "completed 1" in out.getvalue()


def test_evaluate_status_reports_progress(tmp_path):
    output = tmp_path / "run"
    evaluation_cli.cmd_evaluate_run(
        profile="deterministic_full",
        provider="deterministic",
        output=str(output),
        cases=None,
        strategies="single_prompt",
        max_cases=1,
        repeats=1,
        out=io.StringIO(),
    )

    out = io.StringIO()
    exit_code = evaluation_cli.cmd_evaluate_status(str(output), out=out)
    assert exit_code == 0
    rendered = out.getvalue()
    assert "completed: 1" in rendered
    assert "remaining: 0" in rendered


def test_evaluate_status_reports_missing_run_cleanly(tmp_path):
    out = io.StringIO()
    exit_code = evaluation_cli.cmd_evaluate_status(str(tmp_path / "nope"), out=out)
    assert exit_code == 2
    assert "no evaluation run" in out.getvalue().casefold()


def test_evaluate_run_rejects_an_unknown_profile(tmp_path):
    out = io.StringIO()
    exit_code = evaluation_cli.cmd_evaluate_run(
        profile="not-a-profile",
        provider="deterministic",
        output=str(tmp_path / "run"),
        cases=None,
        strategies=None,
        max_cases=1,
        repeats=1,
        out=out,
    )
    assert exit_code == 2
    assert "profile" in out.getvalue().casefold()


def test_evaluate_parser_routes_run_and_status(monkeypatch, tmp_path):
    calls = []

    def fake_run(**kwargs):
        calls.append(("run", kwargs))
        return 0

    def fake_status(run, out=None):
        calls.append(("status", run))
        return 0

    monkeypatch.setattr(evaluation_cli, "cmd_evaluate_run", fake_run)
    monkeypatch.setattr(evaluation_cli, "cmd_evaluate_status", fake_status)

    assert cli_main.main(
        ["evaluate", "run", "--output", str(tmp_path), "--max-cases", "2", "--strategies", "single_prompt"]
    ) == 0
    assert cli_main.main(["evaluate", "status", str(tmp_path)]) == 0
    assert calls[0][0] == "run" and calls[0][1]["max_cases"] == 2
    assert calls[1] == ("status", str(tmp_path))
