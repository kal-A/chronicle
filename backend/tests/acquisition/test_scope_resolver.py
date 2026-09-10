"""ScopeResolver: propose an acquisition scope from a bare question, fallback-safe.

The resolver runs one bounded structured model call to *propose* a scope (topic,
geography, date window, terms) that the frontend presents for human review. It
must never crash on a brittle local model: a malformed/exhausted call degrades to
resolved=False so the caller falls back to manual entry. These tests use the
DeterministicModelProvider (no Ollama, no network).
"""

from __future__ import annotations

from datetime import date

from chronicle.acquisition.scope_resolver import (
    ProposedScope,
    ScopeResolver,
    SCOPE_PROMPT_VERSION,
)
from chronicle.ai.models import DeterministicModelProvider


def _scope() -> ProposedScope:
    return ProposedScope(
        topic="The Great Fire of London",
        interpretedQuestion="When and where did the Great Fire of London begin?",
        geographicScope=["London", "England"],
        dateEarliest=date(1666, 1, 1),
        dateLatest=date(1666, 12, 31),
        terms=["fire", "Pudding Lane", "1666"],
    )


def test_scope_resolver_proposes_a_valid_reviewable_scope():
    provider = DeterministicModelProvider()
    provider.enqueue_value(_scope())

    result = ScopeResolver(provider).resolve("What started the Great Fire of London?")

    assert result.resolved is True
    assert result.proposal is not None
    assert result.proposal.geographicScope == ["London", "England"]
    assert result.proposal.dateEarliest == date(1666, 1, 1)
    assert result.modelCall is not None
    assert result.modelCall.promptVersion == SCOPE_PROMPT_VERSION


def test_scope_resolver_falls_back_when_the_model_cannot_comply():
    # A brittle local model that cannot produce a valid scope must degrade to a
    # manual-entry fallback, never crash.
    provider = DeterministicModelProvider()
    provider.enqueue_malformed("not a scope")
    provider.enqueue_malformed("still not a scope")

    result = ScopeResolver(provider).resolve("An impossibly vague prompt")

    assert result.resolved is False
    assert result.proposal is None
    assert result.message  # a bounded, user-safe note


def test_scope_resolver_rejects_an_empty_question_without_a_model_call():
    provider = DeterministicModelProvider()

    result = ScopeResolver(provider).resolve("   ")

    assert result.resolved is False
    assert result.proposal is None
    assert result.modelCall is None
