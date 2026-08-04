"""Deterministic pipeline orchestration.

`generate()` and `resume()` both funnel through the same `run_pipeline()`.
Reuse-vs-rerun is decided per stage in `run_stage()` by comparing the
current input's hash against the hash recorded on that stage's last PASSED
attempt — a changed upstream output produces a different input hash at the
next stage automatically, so "invalidate downstream" needs no separate
bookkeeping (see the design note in the C1 plan).

C1's 8 stage functions (DEFAULT_STAGE_FNS) are deterministic stubs, not real
providers — Phase C2's providers/registry.py's MOCK_STAGE_FNS replaces them
without any change to this module's stage-execution contract.

`stage_fns` is REQUIRED on generate()/resume()/run_pipeline() (a deliberate
C2 change from C1, where it silently defaulted to DEFAULT_STAGE_FNS) — the
caller now always states explicitly which stage-function set it wants; the
CLI passes MOCK_STAGE_FNS, engine-mechanics tests pass DEFAULT_STAGE_FNS.
"""

from __future__ import annotations

from typing import Callable
from uuid import uuid4

from ..storage.run_store import RunStore
from .hashing import stable_json_hash
from .stages import STAGE_ORDER, RunStatus, StageName, StageRunStatus
from .state import STUB_PROVIDER_SET_VERSION, RunRecord, RunRequest, StageRecord, utcnow

StageFn = Callable[[dict], dict]

STAGE_VERSION = "1.0.0"


class StageExecutionError(Exception):
    def __init__(self, stage_name: StageName, record: StageRecord):
        super().__init__(f'Stage "{stage_name.value}" failed: {record.errorMessage}')
        self.stage_name = stage_name
        self.record = record


def make_stub_stage(stage_name: StageName) -> StageFn:
    """A deterministic pass-through stub: same input always produces the
    same output, and it never fabricates anything resembling real
    historical content — Phase C1 only needs to prove the engine works."""

    def stage_fn(input_data: dict) -> dict:
        output = dict(input_data)
        output[stage_name.value] = {
            "note": "Phase C1 stub — replaced by a real provider in Phase C2",
            "topic": input_data.get("topic"),
        }
        return output

    stage_fn.__name__ = f"stub_{stage_name.value.lower()}"
    return stage_fn


def make_failing_stage(stage_name: StageName) -> StageFn:
    """Used only by `chronicle generate --fail-at <stage>` to exercise the
    FAILED/retry/resume-after-failure path honestly, without a hidden
    magic-string trigger."""

    def stage_fn(input_data: dict) -> dict:
        raise RuntimeError(f'Induced failure at stage "{stage_name.value}" (--fail-at)')

    stage_fn.__name__ = f"failing_{stage_name.value.lower()}"
    return stage_fn


DEFAULT_STAGE_FNS: dict[StageName, StageFn] = {name: make_stub_stage(name) for name in STAGE_ORDER}


def run_stage(
    store: RunStore,
    run: RunRecord,
    stage_name: StageName,
    stage_fn: StageFn,
    input_data: dict,
    provider_version: str,
    provider_name: str = "mock",
) -> dict:
    input_hash = stable_json_hash(input_data)
    existing = store.load_stage(run.runId, stage_name)

    if (
        existing is not None
        and existing.status == StageRunStatus.PASSED
        and existing.inputHash == input_hash
        and existing.providerVersion == provider_version
    ):
        output = store.load_stage_output(run.runId, stage_name)
        if output is not None:
            return output
        # PASSED record exists but its output file is missing — treat as if
        # it never ran rather than silently returning nothing.

    attempt_count = (existing.attemptCount + 1) if existing is not None else 1
    started_at = utcnow()
    order_index = STAGE_ORDER.index(stage_name)

    try:
        output = stage_fn(input_data)
    except Exception as exc:  # noqa: BLE001 - deliberately broad: any stage failure becomes a FAILED StageRecord
        record = StageRecord(
            stageName=stage_name,
            stageVersion=STAGE_VERSION,
            providerName=provider_name,
            providerVersion=provider_version,
            inputHash=input_hash,
            outputHash="",
            status=StageRunStatus.FAILED,
            attemptCount=attempt_count,
            startedAt=started_at,
            completedAt=utcnow(),
            errorType=type(exc).__name__,
            errorMessage=str(exc),
        )
        store.save_stage(run.runId, order_index, stage_name, record)
        raise StageExecutionError(stage_name, record) from exc

    output_hash = stable_json_hash(output)
    record = StageRecord(
        stageName=stage_name,
        stageVersion=STAGE_VERSION,
        providerName=provider_name,
        providerVersion=provider_version,
        inputHash=input_hash,
        outputHash=output_hash,
        status=StageRunStatus.PASSED,
        attemptCount=attempt_count,
        startedAt=started_at,
        completedAt=utcnow(),
    )
    store.save_stage(run.runId, order_index, stage_name, record)
    store.save_stage_output(run.runId, stage_name, output)
    return output


_TERMINAL_STATUS_FROM_PACKAGE_STATUS = {
    "partial": RunStatus.PARTIAL,
    "abstained": RunStatus.ABSTAINED,
}


def run_pipeline(
    store: RunStore,
    run: RunRecord,
    stage_fns: dict[StageName, StageFn],
    provider_set_version: str = STUB_PROVIDER_SET_VERSION,
) -> RunRecord:
    # Tied to whichever stage_fns are actually passed in — this is what
    # makes run_stage's reuse check correct: resuming a run with a
    # different provider set (e.g. stubs -> real mock providers) must
    # re-execute every stage, not reuse stale output recorded under a
    # different provider version.
    run.providerSetVersion = provider_set_version
    run.status = RunStatus.RUNNING
    run.touch()
    store.save_run(run)

    data: dict = {"topic": run.request.topic}
    for stage_name in STAGE_ORDER:
        run.currentStage = stage_name
        try:
            data = run_stage(store, run, stage_name, stage_fns[stage_name], data, provider_set_version)
        except StageExecutionError:
            run.status = RunStatus.FAILED
            run.failedStage = stage_name
            run.touch()
            store.save_run(run)
            return run

        if stage_name not in run.completedStages:
            run.completedStages.append(stage_name)
        run.touch()
        store.save_run(run)

    # The VERIFIED stage's output is either a C1 stub dict (no "status" key
    # at all -> plain success) or a real assembled+validated package (has
    # both "status" and "schemaVersion") -> persist it and let its status
    # drive the run's terminal RunStatus, e.g. "partial" -> RunStatus.PARTIAL.
    run.status = _TERMINAL_STATUS_FROM_PACKAGE_STATUS.get(data.get("status"), RunStatus.READY)
    run.currentStage = None
    run.failedStage = None

    if "schemaVersion" in data:
        package_path = store.save_output_package(run.runId, data)
        report_path = store.save_generation_report(run.runId, data.get("generationReport", {}))
        run.outputPackagePath = str(package_path)
        run.generationReportPath = str(report_path)

    run.touch()
    store.save_run(run)
    return run


def generate(
    store: RunStore,
    topic: str,
    stage_fns: dict[StageName, StageFn],
    provider_set_version: str = STUB_PROVIDER_SET_VERSION,
) -> RunRecord:
    run = RunRecord(runId=uuid4().hex, request=RunRequest(topic=topic))
    store.save_run(run)
    return run_pipeline(store, run, stage_fns, provider_set_version)


def resume(
    store: RunStore,
    run_id: str,
    stage_fns: dict[StageName, StageFn],
    provider_set_version: str = STUB_PROVIDER_SET_VERSION,
) -> RunRecord:
    run = store.load_run(run_id)
    return run_pipeline(store, run, stage_fns, provider_set_version)
