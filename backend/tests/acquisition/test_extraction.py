"""Event-extraction stage unit tests (documented pipeline stage 7).

A schema-constrained model pass over acquired passages proposes historical
events, each grounded in a real passage. These tests use DeterministicModelProvider
(no network, no live model) and neutral placeholder content -- the stage is
subject-agnostic and never branches on which event it is. The deterministic
provider does not enforce the JSON schema, so these tests deliberately feed
malformed proposals to prove the post-generation grounding/period guards.
"""

from __future__ import annotations

from datetime import date

from chronicle.acquisition.extraction import (
    ExtractedEvent,
    ExtractedEvents,
    extract_events,
)
from chronicle.ai.models.deterministic import DeterministicModelProvider
from chronicle.contracts.enums import DatePrecision
from chronicle.contracts.shared import HistoricalDate, Passage


def _period() -> HistoricalDate:
    return HistoricalDate(
        precision=DatePrecision.RANGE,
        earliest=date(1660, 1, 1),
        latest=date(1670, 12, 31),
        label="1660-1670",
    )


def _passages() -> list[Passage]:
    return [
        Passage(id="p-1", documentId="d-1", excerpt="Placeholder account one.", locator="doc#1"),
        Passage(id="p-2", documentId="d-1", excerpt="Placeholder account two.", locator="doc#2"),
    ]


def _provider(events: list[ExtractedEvent]) -> DeterministicModelProvider:
    provider = DeterministicModelProvider()
    provider.enqueue_value(ExtractedEvents(events=events))
    return provider


def test_extracts_grounded_events():
    events = [
        ExtractedEvent(title="Placeholder event", placeName="Placeholdertown", year=1666, passageIds=["p-1"]),
    ]
    result = extract_events(_passages(), _period(), "A topic", _provider(events))

    assert len(result) == 1
    assert result[0].title == "Placeholder event"
    assert result[0].placeName == "Placeholdertown"
    assert result[0].passageIds == ["p-1"]


def test_drops_event_citing_a_nonexistent_passage():
    # Anti-hallucination: an event whose citation is not a real passage is dropped.
    events = [
        ExtractedEvent(title="Real", placeName="Placeholdertown", year=1666, passageIds=["p-2"]),
        ExtractedEvent(title="Fabricated", placeName="Nowhere", year=1666, passageIds=["p-999"]),
    ]
    result = extract_events(_passages(), _period(), "A topic", _provider(events))

    assert [e.title for e in result] == ["Real"]


def test_drops_event_with_year_outside_the_investigation_range():
    events = [
        ExtractedEvent(title="In range", placeName="Placeholdertown", year=1666, passageIds=["p-1"]),
        ExtractedEvent(title="Anachronistic", placeName="Placeholdertown", year=1850, passageIds=["p-1"]),
    ]
    result = extract_events(_passages(), _period(), "A topic", _provider(events))

    assert [e.title for e in result] == ["In range"]


def test_keeps_only_real_passage_ids_within_a_mixed_citation():
    events = [
        ExtractedEvent(
            title="Partly grounded", placeName="Placeholdertown", year=1666,
            passageIds=["p-1", "p-999"],
        ),
    ]
    result = extract_events(_passages(), _period(), "A topic", _provider(events))

    assert len(result) == 1
    assert result[0].passageIds == ["p-1"]  # the fabricated id is stripped


def test_empty_extraction_returns_empty_not_invented():
    result = extract_events(_passages(), _period(), "A topic", _provider([]))
    assert result == []


def test_no_passages_makes_no_model_call_and_returns_empty():
    provider = DeterministicModelProvider()  # nothing enqueued
    result = extract_events([], _period(), "A topic", provider)
    assert result == []
