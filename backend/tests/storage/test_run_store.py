from datetime import datetime, timezone

from chronicle.storage.run_store import RunStore
from chronicle.workflow.stages import StageName, StageRunStatus
from chronicle.workflow.state import RunRecord, RunRequest, StageRecord


def test_save_and_load_run_round_trips(tmp_path):
    store = RunStore(tmp_path)
    run = RunRecord(runId="run-1", request=RunRequest(topic="Round trip"))

    store.save_run(run)
    loaded = store.load_run("run-1")

    assert loaded.runId == run.runId
    assert loaded.request.topic == "Round trip"


def test_run_exists(tmp_path):
    store = RunStore(tmp_path)
    assert store.run_exists("missing") is False

    store.save_run(RunRecord(runId="present", request=RunRequest(topic="x")))
    assert store.run_exists("present") is True


def test_save_and_load_stage_round_trips(tmp_path):
    store = RunStore(tmp_path)
    now = datetime.now(timezone.utc)
    record = StageRecord(
        stageName=StageName.SCOPE_PROPOSED,
        stageVersion="1.0.0",
        providerName="stub",
        providerVersion="c1-stub-v1",
        inputHash="abc",
        outputHash="def",
        status=StageRunStatus.PASSED,
        attemptCount=1,
        startedAt=now,
        completedAt=now,
    )

    store.save_stage("run-1", 0, StageName.SCOPE_PROPOSED, record)
    loaded = store.load_stage("run-1", StageName.SCOPE_PROPOSED)

    assert loaded is not None
    assert loaded.inputHash == "abc"
    assert loaded.outputHash == "def"


def test_load_stage_returns_none_when_absent(tmp_path):
    store = RunStore(tmp_path)
    assert store.load_stage("no-such-run", StageName.SCOPE_PROPOSED) is None


def test_save_and_load_stage_output_round_trips(tmp_path):
    store = RunStore(tmp_path)
    store.save_stage_output("run-1", StageName.SCOPE_PROPOSED, {"topic": "x", "note": "stub"})

    loaded = store.load_stage_output("run-1", StageName.SCOPE_PROPOSED)

    assert loaded == {"topic": "x", "note": "stub"}


def test_list_runs(tmp_path):
    store = RunStore(tmp_path)
    assert store.list_runs() == []

    store.save_run(RunRecord(runId="run-b", request=RunRequest(topic="x")))
    store.save_run(RunRecord(runId="run-a", request=RunRequest(topic="y")))

    assert store.list_runs() == ["run-a", "run-b"]  # sorted
