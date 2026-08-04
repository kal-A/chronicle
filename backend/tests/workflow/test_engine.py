"""Proves the engine mechanics C1 exists to prove: a fresh run completes
deterministically, an unchanged resume reuses every stage instead of
re-executing, a changed input invalidates and reruns from that point
forward, and failure/attempt-count/resume-after-failure behave correctly.

Uses DEFAULT_STAGE_FNS (C1's content-free stubs) throughout, deliberately,
to isolate engine mechanics from C2's real mock-provider content — the
providers themselves are covered by backend/tests/providers/."""

from chronicle.storage.run_store import RunStore
from chronicle.workflow.engine import DEFAULT_STAGE_FNS, generate, make_failing_stage, resume, run_pipeline
from chronicle.workflow.stages import STAGE_ORDER, RunStatus, StageName, StageRunStatus
from chronicle.workflow.state import RunRecord, RunRequest


def test_fresh_run_completes_all_stages_ready(tmp_path):
    store = RunStore(tmp_path)
    run = generate(store, "The Concert of Europe", DEFAULT_STAGE_FNS)

    assert run.status == RunStatus.READY
    assert run.completedStages == STAGE_ORDER
    assert run.failedStage is None

    for stage_name in STAGE_ORDER:
        record = store.load_stage(run.runId, stage_name)
        assert record is not None
        assert record.status == StageRunStatus.PASSED
        assert record.attemptCount == 1


def test_unchanged_resume_reuses_every_stage(tmp_path):
    store = RunStore(tmp_path)
    run = generate(store, "The Concert of Europe", DEFAULT_STAGE_FNS)

    resumed = resume(store, run.runId, DEFAULT_STAGE_FNS)

    assert resumed.status == RunStatus.READY
    for stage_name in STAGE_ORDER:
        record = store.load_stage(run.runId, stage_name)
        assert record.attemptCount == 1  # never re-executed


def test_changed_input_invalidates_and_reruns_from_that_stage_forward(tmp_path):
    store = RunStore(tmp_path)
    run = generate(store, "The Concert of Europe", DEFAULT_STAGE_FNS)
    original_hashes = {s: store.load_stage(run.runId, s).outputHash for s in STAGE_ORDER}

    # Directly mutate the run's request to simulate an upstream input change,
    # then re-run the pipeline (as resume() would).
    loaded = store.load_run(run.runId)
    loaded.request = RunRequest(topic="A different topic entirely")
    store.save_run(loaded)
    run_pipeline(store, loaded, DEFAULT_STAGE_FNS)

    new_hashes = {s: store.load_stage(run.runId, s).outputHash for s in STAGE_ORDER}
    # every stage reruns because the first stage's input (the topic) changed,
    # and that change cascades through every subsequent input hash
    assert new_hashes != original_hashes
    for stage_name in STAGE_ORDER:
        assert store.load_stage(run.runId, stage_name).attemptCount == 2


def test_fail_at_produces_failed_status_and_partial_completion(tmp_path):
    store = RunStore(tmp_path)
    stage_fns = {**DEFAULT_STAGE_FNS, StageName.CORPUS_PREPARED: make_failing_stage(StageName.CORPUS_PREPARED)}
    run = generate(store, "A run that fails midway", stage_fns)

    assert run.status == RunStatus.FAILED
    assert run.failedStage == StageName.CORPUS_PREPARED
    assert run.completedStages == STAGE_ORDER[:4]  # everything before CORPUS_PREPARED

    failed_record = store.load_stage(run.runId, StageName.CORPUS_PREPARED)
    assert failed_record.status == StageRunStatus.FAILED
    assert failed_record.attemptCount == 1
    assert failed_record.errorType == "RuntimeError"


def test_resume_after_failure_succeeds_once_the_fault_is_removed(tmp_path):
    store = RunStore(tmp_path)
    stage_fns = {**DEFAULT_STAGE_FNS, StageName.CORPUS_PREPARED: make_failing_stage(StageName.CORPUS_PREPARED)}
    run = generate(store, "A run that fails then recovers", stage_fns)
    assert run.status == RunStatus.FAILED

    recovered = resume(store, run.runId, DEFAULT_STAGE_FNS)  # no failing override this time

    assert recovered.status == RunStatus.READY
    assert recovered.completedStages == STAGE_ORDER

    corpus_record = store.load_stage(run.runId, StageName.CORPUS_PREPARED)
    assert corpus_record.status == StageRunStatus.PASSED
    assert corpus_record.attemptCount == 2  # first attempt failed, second passed

    # stages that already passed before the failure were never re-executed
    assert store.load_stage(run.runId, StageName.SCOPE_PROPOSED).attemptCount == 1


def test_identical_topic_produces_identical_stage_output_hashes_across_runs(tmp_path):
    store = RunStore(tmp_path)
    run_a = generate(store, "Deterministic topic", DEFAULT_STAGE_FNS)
    run_b = generate(store, "Deterministic topic", DEFAULT_STAGE_FNS)

    assert run_a.runId != run_b.runId  # different run identities
    for stage_name in STAGE_ORDER:
        hash_a = store.load_stage(run_a.runId, stage_name).outputHash
        hash_b = store.load_stage(run_b.runId, stage_name).outputHash
        assert hash_a == hash_b  # but identical, deterministic content


def test_new_run_starts_created_before_pipeline_runs(tmp_path):
    store = RunStore(tmp_path)
    run = RunRecord(runId="manual-test-run", request=RunRequest(topic="Not yet started"))
    assert run.status == RunStatus.CREATED
    assert run.completedStages == []


def test_resuming_with_a_different_provider_set_reruns_every_stage(tmp_path):
    # Regression test: run_stage()'s reuse check compares providerVersion,
    # which must reflect whichever stage_fns were actually passed in — not
    # a hardcoded constant. Resuming the same run with a *different*
    # provider set (simulating stubs -> real providers, or a provider
    # upgrade) must not reuse output recorded under the old version.
    store = RunStore(tmp_path)
    run = generate(store, "Provider version change", DEFAULT_STAGE_FNS, provider_set_version="v1")
    for stage_name in STAGE_ORDER:
        assert store.load_stage(run.runId, stage_name).attemptCount == 1

    resumed = resume(store, run.runId, DEFAULT_STAGE_FNS, provider_set_version="v2")

    assert resumed.providerSetVersion == "v2"
    for stage_name in STAGE_ORDER:
        assert store.load_stage(run.runId, stage_name).attemptCount == 2  # re-executed, not reused
