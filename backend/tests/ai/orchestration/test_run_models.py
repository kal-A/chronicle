"""Tests for the Phase E1 agent-run scaffold (AgentRunRecord/AgentRunStatus).

No runner exists yet -- these only prove the scaffold's own contract:
valid construction, required-field enforcement, the status enum's
supported values, and that it stays architecturally separate from
workflow/engine.py's fixed package-generation pipeline (ADR-003). Wiring
a real runner that populates modelCalls/status/abstentionReason is E3+
work, not this suite's job.
"""

from __future__ import annotations

import inspect

import pytest
from pydantic import ValidationError

from chronicle.ai.orchestration import run_models, statuses
from chronicle.ai.orchestration.run_models import AgentRunRecord, InvestigationRequest
from chronicle.ai.orchestration.statuses import AgentRunStatus


def _valid_request() -> InvestigationRequest:
    return InvestigationRequest(
        runId="run-1",
        corpusId="concert-of-europe",
        userQuestion="How did Troppau lead to intervention in Naples?",
    )


def _valid_record(**kwargs) -> AgentRunRecord:
    return AgentRunRecord(
        runId="run-1",
        request=_valid_request(),
        corpusSnapshot={
            "corpusId": "concert-of-europe",
            "packageId": "concert-of-europe",
            "packageHash": "a" * 64,
            "packageRevision": 1,
            "schemaVersion": "1.0.0",
        },
        **kwargs,
    )


def test_valid_scaffold_record_parses():
    record = _valid_record()

    assert record.status == AgentRunStatus.CREATED
    assert record.modelCalls == []
    assert record.warnings == []
    assert record.abstentionReason is None
    assert record.request.userQuestion.startswith("How did Troppau")


@pytest.mark.parametrize(
    "field,value",
    [("runId", ""), ("corpusId", ""), ("userQuestion", "")],
)
def test_request_rejects_empty_required_fields(field, value):
    kwargs = {
        "runId": "run-1",
        "corpusId": "concert-of-europe",
        "userQuestion": "q",
    }
    kwargs[field] = value
    with pytest.raises(ValidationError):
        InvestigationRequest(**kwargs)


def test_request_rejects_missing_required_fields():
    with pytest.raises(ValidationError):
        InvestigationRequest(userQuestion="q")


def test_record_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        _valid_record(unexpectedField="nope")


@pytest.mark.parametrize("status", list(AgentRunStatus))
def test_status_enum_accepts_every_supported_state(status):
    record = _valid_record(status=status)
    assert record.status is status


def test_status_rejects_an_unsupported_value():
    with pytest.raises(ValidationError):
        _valid_record(status="not-a-real-status")


def test_touch_advances_updated_at_without_changing_created_at():
    record = _valid_record()
    created_at = record.createdAt
    updated_before = record.updatedAt

    record.touch()

    assert record.createdAt == created_at
    assert record.updatedAt >= updated_before


def test_scaffold_is_not_wired_to_the_fixed_package_generation_engine():
    """ADR-003: chronicle.ai.orchestration reuses engine.py's *patterns*
    (file-based record persistence) as a sibling module, never its
    StageName enum or run_pipeline() code path. A source-level guard so
    a future session doesn't wire this scaffold into the fixed pipeline
    without a test catching it."""
    for module in (run_models, statuses):
        source = inspect.getsource(module)
        assert "workflow.engine" not in source
        assert "run_pipeline" not in source
        assert "StageName" not in source
