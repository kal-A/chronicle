"""POST /api/investigations/resolve-scope: propose a reviewable acquisition scope.

Uses a fake resolver (no model, no network); exercises the resolved, fallback,
and unconfigured paths through the real FastAPI app.
"""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from chronicle.acquisition.scope_resolver import ProposedScope, ScopeResolutionResult
from chronicle.ai.orchestration.manager import AgentRunManager
from chronicle.api.app import create_app
from chronicle.corpus import CorpusRegistry
from chronicle.storage.agent_run_store import AgentRunStore


class _NoopWorkflow:
    def run(self, record, corpus, *, emit=None, should_cancel=None):
        return record


class _FakeResolver:
    def __init__(self, result: ScopeResolutionResult) -> None:
        self._result = result
        self.calls: list[str] = []

    def resolve(self, question: str) -> ScopeResolutionResult:
        self.calls.append(question)
        return self._result


def _make_app(tmp_path, resolver):
    registry = CorpusRegistry()
    manager = AgentRunManager(
        workflow=_NoopWorkflow(),
        store=AgentRunStore(tmp_path / "runs"),
        corpus_registry=registry,
    )
    return create_app(
        manager=manager,
        corpus_registry=registry,
        scope_resolver=resolver,
    )


def test_resolve_scope_returns_a_reviewable_proposal(tmp_path):
    proposal = ProposedScope(
        topic="The Great Fire of London",
        interpretedQuestion="When and where did the Great Fire of London begin?",
        geographicScope=["London", "England"],
        dateEarliest=date(1666, 1, 1),
        dateLatest=date(1666, 12, 31),
        terms=["fire", "1666"],
    )
    resolver = _FakeResolver(ScopeResolutionResult(resolved=True, proposal=proposal))
    app = _make_app(tmp_path, resolver)

    with TestClient(app) as client:
        response = client.post(
            "/api/investigations/resolve-scope",
            json={"question": "What started the Great Fire of London?"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["resolved"] is True
    assert body["geographicScope"] == ["London", "England"]
    assert body["dateEarliest"] == "1666-01-01"
    assert body["topic"] == "The Great Fire of London"
    assert resolver.calls == ["What started the Great Fire of London?"]


def test_resolve_scope_reports_a_fallback_when_unresolved(tmp_path):
    resolver = _FakeResolver(
        ScopeResolutionResult(resolved=False, message="could not propose a scope")
    )
    app = _make_app(tmp_path, resolver)

    with TestClient(app) as client:
        response = client.post(
            "/api/investigations/resolve-scope",
            json={"question": "an impossibly vague prompt"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["resolved"] is False
    assert body["geographicScope"] is None
    assert body["message"] == "could not propose a scope"


def test_resolve_scope_is_501_when_unconfigured(tmp_path):
    app = _make_app(tmp_path, None)

    with TestClient(app) as client:
        response = client.post(
            "/api/investigations/resolve-scope",
            json={"question": "anything"},
        )

    assert response.status_code == 501


def test_resolve_scope_rejects_a_blank_question(tmp_path):
    resolver = _FakeResolver(ScopeResolutionResult(resolved=False))
    app = _make_app(tmp_path, resolver)

    with TestClient(app) as client:
        response = client.post(
            "/api/investigations/resolve-scope",
            json={"question": "   "},
        )

    assert response.status_code == 422
    assert resolver.calls == []
