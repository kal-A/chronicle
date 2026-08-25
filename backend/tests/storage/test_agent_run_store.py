from __future__ import annotations

import json
import os

import pytest
from datetime import datetime, timezone
from pydantic import BaseModel, RootModel

from chronicle.ai.contracts.run import AgentRunRecord, CorpusSnapshot, InvestigationRequest
from chronicle.storage.agent_run_store import (
    AgentRunIntegrityError,
    AgentRunNotFoundError,
    AgentRunStore,
    UnsafeAgentRunIdError,
)
from chronicle.ai.tools.contracts import ToolCallRecord, ToolCallStatus
from chronicle.workflow.hashing import stable_json_hash


class _ToolOutput(BaseModel):
    result: str


class _PlanArtifact(RootModel[dict[str, str]]):
    pass


def _record(run_id: str = "agent-run-1") -> AgentRunRecord:
    return AgentRunRecord(
        runId=run_id,
        request=InvestigationRequest(
            runId=run_id,
            corpusId="concert-of-europe",
            userQuestion="What evidence supports Troppau?",
        ),
        corpusSnapshot=CorpusSnapshot(
            corpusId="concert-of-europe",
            packageId="concert-of-europe",
            packageHash="a" * 64,
            packageRevision=1,
            schemaVersion="1.0.0",
        ),
    )


def test_agent_run_round_trip_and_artifact_hash_verification(tmp_path):
    store = AgentRunStore(tmp_path)
    record = _record()
    store.save_run(record)
    reference = store.save_artifact(record.runId, "plan", {"planId": "plan-1"})

    assert store.load_run(record.runId) == record
    assert store.load_artifact(record.runId, reference, _PlanArtifact).root == {"planId": "plan-1"}
    assert store.list_runs() == [record.runId]


def test_tampered_artifact_is_rejected(tmp_path):
    store = AgentRunStore(tmp_path)
    record = _record()
    store.save_run(record)
    reference = store.save_artifact(record.runId, "analysis", {"status": "partial"})
    path = tmp_path / record.runId / reference.relativePath
    path.write_text(json.dumps({"status": "answered"}), encoding="utf-8")

    with pytest.raises(AgentRunIntegrityError):
        store.load_artifact(record.runId, reference, _PlanArtifact)


@pytest.mark.parametrize("run_id", ["../escape", "a/b", "a\\b", "", ".", ".."])
def test_unsafe_run_ids_are_rejected(tmp_path, run_id):
    store = AgentRunStore(tmp_path)
    with pytest.raises(UnsafeAgentRunIdError):
        store.run_exists(run_id)


def test_missing_run_is_typed(tmp_path):
    with pytest.raises(AgentRunNotFoundError):
        AgentRunStore(tmp_path).load_run("missing")


def test_atomic_run_write_retries_a_transient_windows_replace_lock(tmp_path, monkeypatch):
    real_replace = os.replace
    attempts = 0

    def transiently_locked(source, destination):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise PermissionError(5, "Access is denied")
        real_replace(source, destination)

    monkeypatch.setattr("chronicle.storage.agent_run_store.os.replace", transiently_locked)
    store = AgentRunStore(tmp_path)
    record = _record("retry-run")

    store.save_run(record)

    assert store.load_run(record.runId) == record
    assert attempts == 2


def test_successful_tool_result_resumes_from_typed_hash_verified_files(tmp_path):
    store = AgentRunStore(tmp_path)
    run = _record()
    store.save_run(run)
    output = _ToolOutput(result="bounded evidence")
    now = datetime.now(timezone.utc)
    record = ToolCallRecord(
        toolCallId="tool-1",
        agentRunId=run.runId,
        toolName="search_passages",
        toolVersion="2",
        corpusId=run.request.corpusId,
        inputHash="input-hash",
        outputHash=stable_json_hash(output.model_dump(mode="json")),
        status=ToolCallStatus.SUCCEEDED,
        startedAt=now,
        completedAt=now,
        latencyMs=0,
        resultCount=1,
    )
    store.save_tool_result(
        run.runId, 0, record, output, execution_identity_hash="execution-a"
    )

    resumed = store.load_successful_tool_result(
        run.runId,
        0,
        _ToolOutput,
        expected_input_hash="input-hash",
        expected_tool_name="search_passages",
        expected_tool_version="2",
        expected_corpus_id=run.request.corpusId,
        expected_execution_identity_hash="execution-a",
    )
    assert resumed == (record, output)
    assert (tmp_path / run.runId / "tools" / "000-record.json").is_file()
    assert (tmp_path / run.runId / "tools" / "000-output.json").is_file()


def test_resume_rejects_stale_expected_input(tmp_path):
    store = AgentRunStore(tmp_path)
    run = _record()
    store.save_run(run)
    output = _ToolOutput(result="bounded evidence")
    now = datetime.now(timezone.utc)
    record = ToolCallRecord(
        toolCallId="tool-1",
        agentRunId=run.runId,
        toolName="search_passages",
        toolVersion="2",
        corpusId=run.request.corpusId,
        inputHash="old-input",
        outputHash=stable_json_hash(output.model_dump(mode="json")),
        status=ToolCallStatus.SUCCEEDED,
        startedAt=now,
        completedAt=now,
        latencyMs=0,
    )
    store.save_tool_result(
        run.runId, 0, record, output, execution_identity_hash="execution-old"
    )
    assert store.load_successful_tool_result(
        run.runId,
        0,
        _ToolOutput,
        expected_input_hash="new-input",
        expected_tool_name="search_passages",
        expected_tool_version="2",
        expected_corpus_id=run.request.corpusId,
        expected_execution_identity_hash="execution-new",
    ) is None


def test_store_rejects_cross_run_tool_record(tmp_path):
    store = AgentRunStore(tmp_path)
    run = _record()
    output = _ToolOutput(result="bounded evidence")
    now = datetime.now(timezone.utc)
    record = ToolCallRecord(
        toolCallId="tool-1",
        agentRunId="another-run",
        toolName="search_passages",
        toolVersion="2",
        corpusId=run.request.corpusId,
        inputHash="input",
        outputHash=stable_json_hash(output.model_dump(mode="json")),
        status=ToolCallStatus.SUCCEEDED,
        startedAt=now,
        completedAt=now,
        latencyMs=0,
    )
    with pytest.raises(AgentRunIntegrityError):
        store.save_tool_result(
            run.runId, 0, record, output, execution_identity_hash="execution-a"
        )


def test_resume_rejects_stale_plan_or_package_identity(tmp_path):
    store = AgentRunStore(tmp_path)
    run = _record()
    output = _ToolOutput(result="bounded evidence")
    now = datetime.now(timezone.utc)
    record = ToolCallRecord(
        toolCallId="tool-1",
        agentRunId=run.runId,
        toolName="search_passages",
        toolVersion="2",
        corpusId=run.request.corpusId,
        inputHash="same-input",
        outputHash=stable_json_hash(output.model_dump(mode="json")),
        status=ToolCallStatus.SUCCEEDED,
        startedAt=now,
        completedAt=now,
        latencyMs=0,
    )
    store.save_tool_result(
        run.runId, 0, record, output, execution_identity_hash="old-plan-package-prefix"
    )
    assert store.load_successful_tool_result(
        run.runId,
        0,
        _ToolOutput,
        expected_input_hash="same-input",
        expected_tool_name="search_passages",
        expected_tool_version="2",
        expected_corpus_id=run.request.corpusId,
        expected_execution_identity_hash="new-plan-package-prefix",
    ) is None
