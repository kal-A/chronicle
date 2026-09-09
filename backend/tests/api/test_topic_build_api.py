"""The topic-build endpoint: arbitrary topic -> built+registered corpus ->
investigation run, over the real CorpusBuildService + AgentRunManager (only the
network acquisition pipeline is faked, so no network or Ollama is needed)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient

from chronicle.acquisition.build_service import CorpusBuildService
from chronicle.acquisition.chunking import chunk_source
from chronicle.acquisition.contracts import AcquiredSource, SourceCandidate
from chronicle.acquisition.corpus_builder import build_corpus
from chronicle.acquisition.pipeline import AcquisitionResult
from chronicle.ai.orchestration.manager import AgentRunManager
from chronicle.ai.orchestration.statuses import AgentRunStatus
from chronicle.api.app import create_app
from chronicle.ai.orchestration.sequential import WorkflowSignal, WorkflowSignalType
from chronicle.contracts.enums import RightsStatus, SourceType
from chronicle.corpus import CorpusRegistry
from chronicle.storage.agent_run_store import AgentRunStore


class _ImmediateWorkflow:
    """Runs to ANSWER_READY without any model, so the endpoint's submit path is
    exercised without Ollama."""

    def run(self, record, corpus, *, emit, should_cancel):
        del corpus
        emit(WorkflowSignal(type=WorkflowSignalType.RUN_STARTED, message="Run started."))
        record.status = (
            AgentRunStatus.CANCELLED if should_cancel() else AgentRunStatus.ANSWER_READY
        )
        emit(WorkflowSignal(type=WorkflowSignalType.RUN_COMPLETED, message="Run complete."))
        return record


def _built_result() -> AcquisitionResult:
    candidate = SourceCandidate(
        candidateId="wikipedia:en:1",
        connector="wikipedia",
        title="Alpha Overview",
        sourceType=SourceType.TERTIARY_REFERENCE,
        fullTextAvailable=True,
        rightsStatus=RightsStatus.LICENSED,
        url="https://example.org/1",
        language="en",
    )
    src = AcquiredSource(
        candidate=candidate,
        text="Alpha describes the zeppelin registry in detail. " * 20,
        contentType="text/plain",
        contentSha256="hash-1",
        charCount=1000,
        retrievedAt=datetime(2026, 9, 9, tzinfo=timezone.utc),
    )
    passages = chunk_source(src)
    investigation = build_corpus(
        topic="the zeppelin registry",
        interpreted_question="What happened with the zeppelin registry?",
        geographic_scope=["Europe"],
        date_earliest=date(1900, 1, 1),
        date_latest=date(1910, 12, 31),
        acquired=[src],
        passages=passages,
    )
    return AcquisitionResult(
        investigation=investigation, discovered=1, acquired=1, passages=len(passages)
    )


@dataclass
class _FakePipeline:
    result: AcquisitionResult
    calls: list[dict] = field(default_factory=list)

    def run(self, **kwargs) -> AcquisitionResult:
        self.calls.append(kwargs)
        return self.result


def _make_app(tmp_path, *, with_build: bool):
    registry = CorpusRegistry()
    store = AgentRunStore(tmp_path / "runs")
    manager = AgentRunManager(
        workflow=_ImmediateWorkflow(),
        store=store,
        corpus_registry=registry,
    )
    build_service = (
        CorpusBuildService(
            pipeline=_FakePipeline(_built_result()),
            registry=registry,
            build_dir=tmp_path / "built",
        )
        if with_build
        else None
    )
    app = create_app(
        manager=manager,
        corpus_registry=registry,
        run_id_factory=lambda: "run-build-test",
        build_service=build_service,
    )
    return app, manager, registry


_VALID_BODY = {
    "topic": "the zeppelin registry",
    "question": "What happened with the zeppelin registry?",
    "geographicScope": ["Europe"],
    "dateEarliest": "1900-01-01",
    "dateLatest": "1910-12-31",
}


def test_build_endpoint_acquires_registers_and_starts_an_investigation(tmp_path):
    app, manager, registry = _make_app(tmp_path, with_build=True)
    with TestClient(app) as client:
        response = client.post("/api/investigations/build", json=_VALID_BODY)

        assert response.status_code == 202
        body = response.json()
        assert body["alreadyBuilt"] is False
        assert body["acquired"] == 1
        assert body["passages"] >= 1
        assert body["run"]["runId"] == "run-build-test"
        corpus_id = body["corpusId"]
        assert corpus_id.startswith("acq-")
        assert body["corpusUrl"] == f"/api/corpora/{corpus_id}"

        # the corpus is really registered and the run really executed
        assert corpus_id in registry.list_corpus_ids()
        manager.wait("run-build-test", timeout=2)
        run = client.get("/api/agent-runs/run-build-test")
        assert run.json()["status"] == AgentRunStatus.ANSWER_READY.value
        assert run.json()["request"]["corpusId"] == corpus_id


def test_build_endpoint_returns_501_when_not_configured(tmp_path):
    app, _manager, _registry = _make_app(tmp_path, with_build=False)
    with TestClient(app) as client:
        response = client.post("/api/investigations/build", json=_VALID_BODY)
        assert response.status_code == 501


@pytest.mark.parametrize(
    "override",
    [
        {"geographicScope": []},
        {"dateEarliest": "1950-01-01", "dateLatest": "1900-01-01"},
        {"topic": "   "},
    ],
)
def test_build_endpoint_rejects_invalid_submissions(tmp_path, override):
    app, _manager, _registry = _make_app(tmp_path, with_build=True)
    with TestClient(app) as client:
        response = client.post(
            "/api/investigations/build", json={**_VALID_BODY, **override}
        )
        assert response.status_code == 422
