"""get_timeline_context -- only surfaces time distinctions the data
actually carries; never invents a report-time/discovery-time/
interpretation-time the contract doesn't have."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from chronicle.ai.tools.contracts import ToolExecutionContext
from chronicle.ai.tools.timeline import _event_entries
from chronicle.contracts.shared import HistoricalDate
from chronicle.ai.tools.errors import CorpusRetrievalError


def test_uncertain_timeline_order_and_related_ids_are_explicitly_bounded(corpus):
    events = corpus.get_investigation().events
    if len(events) < 2:
        pytest.skip("corpus needs two events")
    first = events[0].model_copy(
        update={
            "eventTime": HistoricalDate(
                precision="range",
                earliest=date(1900, 1, 1),
                latest=date(1900, 1, 10),
            ),
            "relatedRecordIds": ["record-a", "record-b"],
        }
    )
    overlapping = events[1].model_copy(
        update={
            "eventTime": HistoricalDate(
                precision="range",
                earliest=date(1900, 1, 5),
                latest=date(1900, 1, 20),
            ),
            "relatedRecordIds": ["record-c", "record-d"],
        }
    )
    entries = _event_entries([first, overlapping], related_record_limit=1)

    assert entries[0].chronologyRelationToPrevious == "first"
    assert entries[1].chronologyRelationToPrevious == "overlaps-or-uncertain"
    assert sum(len(entry.relatedRecordIds) for entry in entries) == 1
    assert entries[0].relatedRecordsTruncated is True
    assert entries[1].relatedRecordsTruncated is True

    strictly_later = overlapping.model_copy(
        update={
            "eventTime": HistoricalDate(
                precision="exact",
                earliest=date(1900, 2, 1),
                latest=date(1900, 2, 1),
            )
        }
    )
    assert (
        _event_entries([first, strictly_later], related_record_limit=4)[1]
        .chronologyRelationToPrevious
        == "strictly-after"
    )


def test_requires_at_least_one_anchor(tool_registry, corpus, corpus_id, context):
    from chronicle.ai.tools.errors import MalformedToolInputError

    with pytest.raises((MalformedToolInputError, ValidationError)):
        tool_registry.invoke("get_timeline_context", {"corpusId": corpus_id}, context, corpus)


def test_timeline_omitted_default_clamps_to_a_smaller_context(
    tool_registry, corpus, corpus_id
):
    event = corpus.get_investigation().events[0]
    output, _ = tool_registry.invoke(
        "get_timeline_context",
        {"corpusId": corpus_id, "eventId": event.id},
        ToolExecutionContext(corpusId=corpus_id, maximumResults=1),
        corpus,
    )
    assert output.returnedCount <= 1


def test_rejects_ambiguous_multiple_anchor_kinds(tool_registry, corpus, corpus_id, context):
    from chronicle.ai.tools.errors import MalformedToolInputError

    event = corpus.get_investigation().events[0]
    with pytest.raises((MalformedToolInputError, ValidationError)):
        tool_registry.invoke(
            "get_timeline_context",
            {"corpusId": corpus_id, "eventId": event.id, "dateFrom": str(event.eventTime.earliest)},
            context,
            corpus,
        )


def test_rejects_reversed_date_range(tool_registry, corpus, corpus_id, context):
    from chronicle.ai.tools.errors import MalformedToolInputError

    with pytest.raises((MalformedToolInputError, ValidationError)):
        tool_registry.invoke(
            "get_timeline_context",
            {"corpusId": corpus_id, "dateFrom": "1914-08-01", "dateTo": "1914-07-01"},
            context,
            corpus,
        )


def test_event_anchor_returns_that_event(tool_registry, corpus, corpus_id, context):
    event = corpus.get_investigation().events[0]
    output, _record = tool_registry.invoke(
        "get_timeline_context",
        {"corpusId": corpus_id, "eventId": event.id, "beforeCount": 0, "afterCount": 0},
        context,
        corpus,
    )
    assert [e.eventId for e in output.events] == [event.id]


def test_event_anchor_unknown_id_raises(tool_registry, corpus, corpus_id, context):
    with pytest.raises(CorpusRetrievalError):
        tool_registry.invoke(
            "get_timeline_context", {"corpusId": corpus_id, "eventId": "no-such-event"}, context, corpus
        )


def test_before_after_counts_bound_the_window(tool_registry, corpus, corpus_id, context):
    events = corpus.get_events_ordered()
    if len(events) < 3:
        pytest.skip("this corpus has fewer than 3 events")
    # anchor on the middle event chronologically
    middle = events[len(events) // 2]
    output, _record = tool_registry.invoke(
        "get_timeline_context",
        {"corpusId": corpus_id, "eventId": middle.id, "beforeCount": 1, "afterCount": 1},
        context,
        corpus,
    )
    assert len(output.events) <= 3
    assert middle.id in [e.eventId for e in output.events]


def test_place_anchor_returns_only_events_at_that_place(tool_registry, corpus, corpus_id, context):
    place = next(e for e in corpus.get_investigation().entities if e.entityType == "place")
    output, _record = tool_registry.invoke(
        "get_timeline_context", {"corpusId": corpus_id, "placeId": place.id}, context, corpus
    )
    for entry in output.events:
        assert entry.placeId == place.id


def test_person_entity_anchor_returns_no_events_honestly(tool_registry, corpus, corpus_id, context):
    """GeneratedEvent has no person-reference field -- confirm the tool
    returns an empty, honestly-labelled result rather than guessing."""
    person = next(e for e in corpus.get_investigation().entities if e.entityType == "person")
    output, _record = tool_registry.invoke(
        "get_timeline_context", {"corpusId": corpus_id, "entityId": person.id}, context, corpus
    )
    assert output.events == []


def test_date_range_anchor_filters_by_event_time(tool_registry, corpus, corpus_id, context):
    output, _record = tool_registry.invoke(
        "get_timeline_context",
        {"corpusId": corpus_id, "dateFrom": str(date(1900, 1, 1)), "dateTo": str(date(1901, 1, 1))},
        context,
        corpus,
    )
    assert output.events == []  # no fixture events fall in this window


def test_date_range_uses_event_interval_overlap(tool_registry, corpus, corpus_id, context):
    event = corpus.get_investigation().events[0]
    output, _ = tool_registry.invoke(
        "get_timeline_context",
        {
            "corpusId": corpus_id,
            "dateFrom": str(event.eventTime.latest),
            "dateTo": str(event.eventTime.latest),
        },
        context,
        corpus,
    )
    assert event.id in [entry.eventId for entry in output.events]


def test_timeline_reports_passage_time_roles_without_collapsing_them(tool_registry, corpus, corpus_id, context):
    event = next((e for e in corpus.get_investigation().events if corpus.get_passages_for(e.id)), None)
    if event is None:
        pytest.skip("no event has linked passage evidence")
    output, _ = tool_registry.invoke(
        "get_timeline_context",
        {"corpusId": corpus_id, "eventId": event.id, "beforeCount": 0, "afterCount": 0},
        context,
        corpus,
    )
    assert all(
        item.timeRole
        in {
            "sent_time",
            "received_time",
            "source_date",
            "linked_event_time",
            "linked_actor_awareness_time",
        }
        for item in output.passageTimes
    )
    assert all(
        item.linkedTargetId is not None
        for item in output.passageTimes
        if item.timeRole in {"linked_event_time", "linked_actor_awareness_time"}
    )
    assert "event-time" in output.scopeNote


def test_timeline_reserves_space_for_event_and_passage_time_categories(
    tool_registry, corpus, corpus_id
):
    event = next(
        (item for item in corpus.get_investigation().events if corpus.get_passages_for(item.id)),
        None,
    )
    if event is None:
        pytest.skip("no event has passage time context")
    output, _ = tool_registry.invoke(
        "get_timeline_context",
        {
            "corpusId": corpus_id,
            "eventId": event.id,
            "beforeCount": 0,
            "afterCount": 0,
        },
        ToolExecutionContext(corpusId=corpus_id, maximumResults=2),
        corpus,
    )
    assert output.eventReturnedCount == 1
    assert output.passageTimeReturnedCount == 1
    assert output.passageTimeTotalCount >= output.passageTimeReturnedCount
    assert output.passageTimesTruncated == (
        output.passageTimeTotalCount > output.passageTimeReturnedCount
    )
    assert sum(output.passageTimeCountsByRole.values()) == output.passageTimeTotalCount


def test_timeline_honors_context_cap_across_returned_entries(tool_registry, corpus, corpus_id):
    from chronicle.ai.tools.contracts import ToolExecutionContext

    event = corpus.get_investigation().events[0]
    output, _ = tool_registry.invoke(
        "get_timeline_context",
        {"corpusId": corpus_id, "eventId": event.id, "beforeCount": 20, "afterCount": 20, "maxResults": 1},
        ToolExecutionContext(corpusId=corpus_id, maximumResults=1),
        corpus,
    )
    assert output.returnedCount <= 1
    assert len(output.events) + len(output.passageTimes) <= 1


def test_claim_anchor_returns_events_referencing_that_claim(tool_registry, corpus, corpus_id, context):
    investigation = corpus.get_investigation()
    referencing_claim_ids = {rid for e in investigation.events for rid in e.relatedRecordIds}
    claim_id = next((c.id for c in investigation.claims if c.id in referencing_claim_ids), None)
    if claim_id is None:
        pytest.skip("no claim in this corpus is referenced by an event's relatedRecordIds")
    output, _record = tool_registry.invoke(
        "get_timeline_context", {"corpusId": corpus_id, "claimId": claim_id}, context, corpus
    )
    for entry in output.events:
        assert claim_id in entry.relatedRecordIds
