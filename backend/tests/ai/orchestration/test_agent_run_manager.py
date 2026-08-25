from __future__ import annotations

from threading import Event, Lock

import pytest

from chronicle.ai.contracts.run import AgentRunRecord, CorpusSnapshot, InvestigationRequest
from chronicle.ai.orchestration.manager import (
    AgentRunAlreadyActiveError,
    AgentRunEventJournal,
    AgentRunManager,
    AgentRunNotCancellableError,
)
from chronicle.ai.orchestration.sequential import WorkflowSignal, WorkflowSignalType
from chronicle.ai.orchestration.statuses import AgentRunStatus
from chronicle.corpus import CorpusRegistry
from chronicle.storage.agent_run_store import AgentRunStore


def _record(run_id: str) -> AgentRunRecord:
    corpus = CorpusRegistry().get_corpus("blank-cheque-golden")
    manifest = corpus.get_manifest()
    investigation = corpus.get_investigation()
    return AgentRunRecord(
        runId=run_id,
        request=InvestigationRequest(
            runId=run_id,
            corpusId=corpus.corpus_id,
            userQuestion="What did the report say?",
        ),
        corpusSnapshot=CorpusSnapshot(
            corpusId=corpus.corpus_id,
            packageId=investigation.packageId,
            packageHash=manifest.packageHash,
            packageRevision=investigation.packageRevision,
            schemaVersion=investigation.schemaVersion,
            capabilities=tuple(manifest.supportedCapabilities),
            knownOmissions=tuple(manifest.knownOmissions),
        ),
    )


class _ControlledWorkflow:
    def __init__(self) -> None:
        self.first_started = Event()
        self.release_first = Event()
        self.second_started = Event()
        self._lock = Lock()
        self._active = 0
        self.max_active = 0

    def run(self, record, corpus, *, emit, should_cancel):
        del corpus
        with self._lock:
            self._active += 1
            self.max_active = max(self.max_active, self._active)
        try:
            emit(WorkflowSignal(type=WorkflowSignalType.RUN_STARTED, message="Run started."))
            if record.runId == "run-one":
                self.first_started.set()
                assert self.release_first.wait(timeout=2)
            else:
                self.second_started.set()
            record.status = (
                AgentRunStatus.CANCELLED if should_cancel() else AgentRunStatus.ANSWER_READY
            )
            emit(
                WorkflowSignal(
                    type=(
                        WorkflowSignalType.RUN_CANCELLED
                        if record.status is AgentRunStatus.CANCELLED
                        else WorkflowSignalType.RUN_COMPLETED
                    ),
                    message="Run stopped." if record.status is AgentRunStatus.CANCELLED else "Run complete.",
                )
            )
            return record
        finally:
            with self._lock:
                self._active -= 1


@pytest.fixture
def manager(tmp_path):
    store = AgentRunStore(tmp_path)
    workflow = _ControlledWorkflow()
    manager = AgentRunManager(
        workflow=workflow,
        store=store,
        corpus_registry=CorpusRegistry(),
        event_journal=AgentRunEventJournal(),
    )
    try:
        yield manager, workflow, store
    finally:
        workflow.release_first.set()
        manager.shutdown()


def test_manager_runs_investigations_one_at_a_time_and_replays_ordered_events(manager):
    run_manager, workflow, _store = manager

    run_manager.submit(_record("run-one"))
    assert workflow.first_started.wait(timeout=2)
    run_manager.submit(_record("run-two"))

    assert workflow.second_started.is_set() is False
    workflow.release_first.set()
    assert run_manager.wait("run-one", timeout=2).status is AgentRunStatus.ANSWER_READY
    assert run_manager.wait("run-two", timeout=2).status is AgentRunStatus.ANSWER_READY
    assert workflow.max_active == 1

    events = run_manager.events("run-two")
    assert [event.sequence for event in events] == [1, 2]
    assert [event.type for event in events] == [
        WorkflowSignalType.RUN_STARTED,
        WorkflowSignalType.RUN_COMPLETED,
    ]
    assert run_manager.events("run-two", after_sequence=1) == [events[1]]


def test_cancellation_of_queued_run_is_observed_before_agent_work_starts(manager):
    run_manager, workflow, store = manager
    run_manager.submit(_record("run-one"))
    assert workflow.first_started.wait(timeout=2)
    run_manager.submit(_record("run-two"))

    run_manager.cancel("run-two")
    workflow.release_first.set()

    assert run_manager.wait("run-two", timeout=2).status is AgentRunStatus.CANCELLED
    assert store.load_run("run-two").status is AgentRunStatus.CANCELLED
    assert run_manager.events("run-two")[-1].type is WorkflowSignalType.RUN_CANCELLED


def test_resume_rejects_duplicate_active_execution(manager):
    run_manager, workflow, _store = manager
    run_manager.submit(_record("run-one"))
    assert workflow.first_started.wait(timeout=2)

    with pytest.raises(AgentRunAlreadyActiveError):
        run_manager.resume("run-one")


def test_cancel_rejects_a_run_that_already_completed(manager):
    run_manager, _workflow, _store = manager
    run_manager.submit(_record("run-two"))
    assert run_manager.wait("run-two", timeout=2).status is AgentRunStatus.ANSWER_READY

    with pytest.raises(AgentRunNotCancellableError):
        run_manager.cancel("run-two")
