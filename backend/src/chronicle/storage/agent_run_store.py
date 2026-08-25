"""Atomic, hash-verified file persistence for Phase E3 agent runs."""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
import time
from pathlib import Path
from threading import RLock
from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from ..ai.contracts.run import AgentRunRecord, ArtifactReference
from ..ai.tools.contracts import ToolCallRecord, ToolCallStatus
from ..workflow.hashing import stable_json_hash

T = TypeVar("T", bound=BaseModel)


class _StoredToolRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    executionIdentityHash: str = Field(min_length=1, max_length=200)
    record: ToolCallRecord

_SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")


class AgentRunStoreError(Exception):
    pass


class AgentRunNotFoundError(AgentRunStoreError):
    pass


class AgentRunIntegrityError(AgentRunStoreError):
    pass


class UnsafeAgentRunIdError(AgentRunStoreError):
    pass


class AgentRunStore:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self._lock = RLock()

    def _run_dir(self, run_id: str) -> Path:
        if not _SAFE_COMPONENT.fullmatch(run_id):
            raise UnsafeAgentRunIdError(f"Unsafe agent run id: {run_id!r}")
        return self.root / run_id

    def run_exists(self, run_id: str) -> bool:
        return (self._run_dir(run_id) / "run.json").is_file()

    def save_run(self, run: AgentRunRecord) -> None:
        try:
            validated = AgentRunRecord.model_validate(run.model_dump(mode="python"))
        except Exception as exc:
            raise AgentRunIntegrityError("agent run failed schema or identity validation") from exc
        with self._lock:
            _atomic_write(
                self._run_dir(validated.runId) / "run.json",
                validated.model_dump_json(indent=2),
            )

    def load_run(self, run_id: str) -> AgentRunRecord:
        path = self._run_dir(run_id) / "run.json"
        with self._lock:
            if not path.is_file():
                raise AgentRunNotFoundError(f'No agent run found for id "{run_id}"')
            record = AgentRunRecord.model_validate_json(path.read_text(encoding="utf-8"))
        if record.runId != run_id or record.request.runId != run_id:
            raise AgentRunIntegrityError("persisted run identity does not match its directory")
        return record

    def save_artifact(self, run_id: str, artifact_kind: str, value: Any) -> ArtifactReference:
        if not _SAFE_COMPONENT.fullmatch(artifact_kind):
            raise UnsafeAgentRunIdError(f"Unsafe artifact kind: {artifact_kind!r}")
        from pydantic import TypeAdapter

        serialized = TypeAdapter(Any).dump_json(value, indent=2).decode("utf-8")
        relative_path = f"artifacts/{artifact_kind}.json"
        _atomic_write(self._run_dir(run_id) / relative_path, serialized)
        return ArtifactReference(
            artifactKind=artifact_kind,
            relativePath=relative_path,
            contentHash=_hash_text(serialized),
            serializedCharacters=len(serialized),
        )

    def load_artifact(
        self,
        run_id: str,
        reference: ArtifactReference,
        artifact_model: type[T],
    ) -> T:
        expected_path = f"artifacts/{reference.artifactKind}.json"
        if reference.relativePath != expected_path:
            raise AgentRunIntegrityError("artifact reference path is not canonical")
        path = self._run_dir(run_id) / expected_path
        if not path.is_file():
            raise AgentRunNotFoundError(f"Agent artifact not found: {reference.artifactKind}")
        serialized = path.read_text(encoding="utf-8")
        if _hash_text(serialized) != reference.contentHash:
            raise AgentRunIntegrityError(f"Agent artifact hash mismatch: {reference.artifactKind}")
        return artifact_model.model_validate_json(serialized)

    def list_runs(self) -> list[str]:
        if not self.root.exists():
            return []
        return sorted(path.name for path in self.root.iterdir() if (path / "run.json").is_file())

    def save_tool_result(
        self,
        run_id: str,
        sequence: int,
        record: ToolCallRecord,
        output: BaseModel,
        *,
        execution_identity_hash: str,
    ) -> None:
        if sequence < 0 or sequence > 999:
            raise AgentRunIntegrityError("tool sequence must be between 0 and 999")
        if record.status is not ToolCallStatus.SUCCEEDED or record.outputHash is None:
            raise AgentRunIntegrityError("only successful tool calls with output hashes are resumable")
        if record.completedAt is None or record.latencyMs is None:
            raise AgentRunIntegrityError("successful resumable tool calls require completion metadata")
        if record.agentRunId != run_id:
            raise AgentRunIntegrityError("tool call record is not bound to this run")
        if stable_json_hash(output.model_dump(mode="json")) != record.outputHash:
            raise AgentRunIntegrityError("tool output does not match its audit-record hash")
        tools_dir = self._run_dir(run_id) / "tools"
        stem = f"{sequence:03d}"
        _atomic_write(tools_dir / f"{stem}-output.json", output.model_dump_json(indent=2))
        stored_record = _StoredToolRecord(
            executionIdentityHash=execution_identity_hash,
            record=record,
        )
        _atomic_write(tools_dir / f"{stem}-record.json", stored_record.model_dump_json(indent=2))

    def load_successful_tool_result(
        self,
        run_id: str,
        sequence: int,
        output_model: type[T],
        *,
        expected_input_hash: str,
        expected_tool_name: str,
        expected_tool_version: str,
        expected_corpus_id: str,
        expected_execution_identity_hash: str,
    ) -> tuple[ToolCallRecord, T] | None:
        if sequence < 0 or sequence > 999:
            raise AgentRunIntegrityError("tool sequence must be between 0 and 999")
        tools_dir = self._run_dir(run_id) / "tools"
        stem = f"{sequence:03d}"
        record_path = tools_dir / f"{stem}-record.json"
        output_path = tools_dir / f"{stem}-output.json"
        if not record_path.is_file() or not output_path.is_file():
            return None
        stored = _StoredToolRecord.model_validate_json(record_path.read_text(encoding="utf-8"))
        if stored.executionIdentityHash != expected_execution_identity_hash:
            return None
        record = stored.record
        if record.status is not ToolCallStatus.SUCCEEDED or record.outputHash is None:
            return None
        if record.agentRunId != run_id:
            raise AgentRunIntegrityError("stored tool call is not bound to this run")
        if (
            record.inputHash != expected_input_hash
            or record.toolName != expected_tool_name
            or record.toolVersion != expected_tool_version
            or record.corpusId != expected_corpus_id
        ):
            return None
        output = output_model.model_validate_json(output_path.read_text(encoding="utf-8"))
        if stable_json_hash(output.model_dump(mode="json")) != record.outputHash:
            raise AgentRunIntegrityError(f"Tool output hash mismatch at sequence {sequence}")
        return record, output


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _atomic_write(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(contents)
            handle.flush()
            os.fsync(handle.fileno())
        for attempt in range(5):
            try:
                os.replace(temporary_name, path)
                break
            except PermissionError:
                if attempt == 4:
                    raise
                time.sleep(0.01 * (2**attempt))
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
