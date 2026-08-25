from __future__ import annotations

from threading import Event

import pytest
from fastapi.testclient import TestClient

from chronicle.ai.contracts.run import AgentRunRecord, CorpusSnapshot, InvestigationRequest
from chronicle.ai.orchestration.manager import AgentRunManager
from chronicle.ai.orchestration.sequential import WorkflowSignal, WorkflowSignalType
from chronicle.ai.orchestration.statuses import AgentRunStatus
from chronicle.api.app import create_app
from chronicle.corpus import CorpusRegistry
from chronicle.storage.agent_run_store import AgentRunStore


class _ImmediateWorkflow:
    def run(self, record, corpus, *, emit, should_cancel):
        del corpus
        emit(WorkflowSignal(type=WorkflowSignalType.RUN_STARTED, message="Run started."))
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
                message="Run complete.",
            )
        )
        return record


class _BlockingWorkflow:
    def __init__(self) -> None:
        self.started = Event()
        self.release = Event()

    def run(self, record, corpus, *, emit, should_cancel):
        del corpus
        emit(WorkflowSignal(type=WorkflowSignalType.RUN_STARTED, message="Run started."))
        self.started.set()
        assert self.release.wait(timeout=2)
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
                message="Run stopped.",
            )
        )
        return record


def _record(run_id: str, registry: CorpusRegistry, *, status=AgentRunStatus.CREATED):
    corpus = registry.get_corpus("blank-cheque-golden")
    manifest = corpus.get_manifest()
    investigation = corpus.get_investigation()
    return AgentRunRecord(
        runId=run_id,
        status=status,
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


@pytest.fixture
def api(tmp_path):
    registry = CorpusRegistry()
    store = AgentRunStore(tmp_path)
    manager = AgentRunManager(
        workflow=_ImmediateWorkflow(),
        store=store,
        corpus_registry=registry,
    )
    app = create_app(
        manager=manager,
        corpus_registry=registry,
        run_id_factory=lambda: "run-api-test",
    )
    with TestClient(app) as client:
        yield client, manager, store, registry


def test_question_submission_polling_and_sse_share_one_run_contract(api):
    client, manager, _store, _registry = api

    accepted = client.post(
        "/api/investigations/blank-cheque-golden/questions",
        json={"question": "What did the report say?"},
    )

    assert accepted.status_code == 202
    assert accepted.json() == {
        "runId": "run-api-test",
        "status": "created",
        "statusUrl": "/api/agent-runs/run-api-test",
        "eventsUrl": "/api/agent-runs/run-api-test/events",
    }
    manager.wait("run-api-test", timeout=2)
    run = client.get("/api/agent-runs/run-api-test")
    assert run.status_code == 200
    assert run.json()["status"] == "answer_ready"

    events = client.get("/api/agent-runs/run-api-test/events?after=0")
    assert events.status_code == 200
    assert [event["sequence"] for event in events.json()] == [1, 2]

    stream = client.get(
        "/api/agent-runs/run-api-test/events?after=0",
        headers={"accept": "text/event-stream"},
    )
    assert stream.status_code == 200
    assert stream.headers["content-type"].startswith("text/event-stream")
    assert "id: 1" in stream.text
    assert "event: run_completed" in stream.text


def test_resume_queues_a_persisted_failed_run_and_duplicate_submission_conflicts(api):
    client, manager, store, registry = api
    record = _record("run-resume-api", registry, status=AgentRunStatus.FAILED)
    store.save_run(record)

    resumed = client.post("/api/agent-runs/run-resume-api/resume")

    assert resumed.status_code == 202
    assert resumed.json()["runId"] == "run-resume-api"
    assert manager.wait("run-resume-api", timeout=2).status is AgentRunStatus.ANSWER_READY

    first = client.post(
        "/api/investigations/blank-cheque-golden/questions",
        json={"question": "What did the report say?"},
    )
    assert first.status_code == 202
    manager.wait("run-api-test", timeout=2)
    duplicate = client.post(
        "/api/investigations/blank-cheque-golden/questions",
        json={"question": "What did the report say?"},
    )
    assert duplicate.status_code == 409


def test_unknown_corpus_and_unknown_run_are_honest_404s(api):
    client, _manager, _store, _registry = api

    assert client.post(
        "/api/investigations/not-a-corpus/questions",
        json={"question": "What happened?"},
    ).status_code == 404
    assert client.get("/api/agent-runs/not-a-run").status_code == 404


def test_health_and_corpus_discovery_are_small_frontend_bootstrap_contracts(api):
    client, _manager, _store, _registry = api

    assert client.get("/health").json() == {"status": "ok"}
    corpora = client.get("/api/corpora")
    assert corpora.status_code == 200
    assert {item["corpusId"] for item in corpora.json()} == {
        "blank-cheque-golden",
        "concert-of-europe-1814-1822",
    }


def test_cancel_endpoint_requests_a_safe_boundary_stop(tmp_path):
    registry = CorpusRegistry()
    store = AgentRunStore(tmp_path)
    workflow = _BlockingWorkflow()
    manager = AgentRunManager(
        workflow=workflow,
        store=store,
        corpus_registry=registry,
    )
    app = create_app(
        manager=manager,
        corpus_registry=registry,
        run_id_factory=lambda: "run-cancel-api",
    )
    with TestClient(app) as client:
        assert client.post(
            "/api/investigations/blank-cheque-golden/questions",
            json={"question": "What did the report say?"},
        ).status_code == 202
        assert workflow.started.wait(timeout=2)

        cancelled = client.post("/api/agent-runs/run-cancel-api/cancel")
        workflow.release.set()

        assert cancelled.status_code == 202
        assert manager.wait("run-cancel-api", timeout=2).status is AgentRunStatus.CANCELLED
