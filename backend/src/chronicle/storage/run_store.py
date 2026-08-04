"""File-based run persistence.

Layout per chronicle_phase_c_adjusted_plan.md §12:
  <root>/<run-id>/run.json
  <root>/<run-id>/stages/NN-<stage>.json   (one per stage attempt, latest wins)
  <root>/<run-id>/output/<stage>.json      (that stage's raw output)

`root` is always passed in explicitly — tests use a pytest tmp_path, never
the real backend/runs/ directory (which is gitignored; generated run data
isn't committed unless deliberately promoted to a fixture).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..workflow.stages import STAGE_ORDER, StageName
from ..workflow.state import RunRecord, StageRecord


class RunNotFoundError(Exception):
    pass


class RunStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def _run_dir(self, run_id: str) -> Path:
        return self.root / run_id

    def _stages_dir(self, run_id: str) -> Path:
        return self._run_dir(run_id) / "stages"

    def _output_dir(self, run_id: str) -> Path:
        return self._run_dir(run_id) / "output"

    def run_exists(self, run_id: str) -> bool:
        return (self._run_dir(run_id) / "run.json").exists()

    def save_run(self, run: RunRecord) -> None:
        run_dir = self._run_dir(run.runId)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "run.json").write_text(run.model_dump_json(indent=2), encoding="utf-8")

    def load_run(self, run_id: str) -> RunRecord:
        path = self._run_dir(run_id) / "run.json"
        if not path.exists():
            raise RunNotFoundError(f'No run found for id "{run_id}"')
        return RunRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def save_stage(self, run_id: str, order_index: int, stage_name: StageName, record: StageRecord) -> None:
        stages_dir = self._stages_dir(run_id)
        stages_dir.mkdir(parents=True, exist_ok=True)
        path = stages_dir / f"{order_index:02d}-{stage_name.value}.json"
        path.write_text(record.model_dump_json(indent=2), encoding="utf-8")

    def load_stage(self, run_id: str, stage_name: StageName) -> StageRecord | None:
        order_index = STAGE_ORDER.index(stage_name)
        path = self._stages_dir(run_id) / f"{order_index:02d}-{stage_name.value}.json"
        if not path.exists():
            return None
        return StageRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def save_stage_output(self, run_id: str, stage_name: StageName, output: dict[str, Any]) -> None:
        output_dir = self._output_dir(run_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{stage_name.value}.json"
        path.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")

    def load_stage_output(self, run_id: str, stage_name: StageName) -> dict[str, Any] | None:
        path = self._output_dir(run_id) / f"{stage_name.value}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_runs(self) -> list[str]:
        if not self.root.exists():
            return []
        return sorted(p.name for p in self.root.iterdir() if (p / "run.json").exists())

    def save_output_package(self, run_id: str, package: dict[str, Any]) -> Path:
        output_dir = self._output_dir(run_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / "package.json"
        path.write_text(json.dumps(package, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def save_generation_report(self, run_id: str, report: dict[str, Any]) -> Path:
        output_dir = self._output_dir(run_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / "generation-report.json"
        path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        return path
