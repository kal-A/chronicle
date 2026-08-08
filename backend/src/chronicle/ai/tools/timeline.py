"""Bounded timeline context preserving every represented time role."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ...contracts.shared import HistoricalDate
from ...corpus.bounds import CollectionBudget
from ...corpus.contracts import DEFAULT_RESULT_COUNT, MAX_RESULT_COUNT, PassageDateRole
from ...corpus.protocol import InvestigationCorpus
from .contracts import ToolExecutionContext
from .registry import ToolDefinition

DEFAULT_BEFORE_COUNT = 3
DEFAULT_AFTER_COUNT = 3


class GetTimelineContextInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpusId: str = Field(min_length=1)
    eventId: str | None = None
    claimId: str | None = None
    relationshipId: str | None = None
    entityId: str | None = None
    placeId: str | None = None
    dateFrom: date | None = None
    dateTo: date | None = None
    beforeCount: int = Field(default=DEFAULT_BEFORE_COUNT, ge=0, le=20)
    afterCount: int = Field(default=DEFAULT_AFTER_COUNT, ge=0, le=20)
    maxResults: int = Field(default=DEFAULT_RESULT_COUNT, ge=1, le=MAX_RESULT_COUNT)

    @model_validator(mode="after")
    def _validate_anchor_and_range(self):
        anchor_groups = [
            self.eventId is not None,
            self.claimId is not None,
            self.relationshipId is not None,
            self.entityId is not None,
            self.placeId is not None,
            self.dateFrom is not None or self.dateTo is not None,
        ]
        if not any(anchor_groups):
            raise ValueError(
                "get_timeline_context requires at least one anchor: eventId, "
                "claimId, relationshipId, entityId, placeId, or dateFrom/dateTo"
            )
        if sum(anchor_groups) > 1:
            raise ValueError("get_timeline_context accepts exactly one anchor kind per call")
        if self.dateFrom is not None and self.dateTo is not None and self.dateFrom > self.dateTo:
            raise ValueError("dateFrom must not be after dateTo")
        return self


class TimelineEventEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    eventId: str
    title: str
    placeId: str
    eventTime: HistoricalDate
    reviewStatus: str
    visibility: str
    relatedRecordIds: list[str]
    relatedRecordTotalCount: int = Field(ge=0)
    relatedRecordReturnedCount: int = Field(ge=0)
    relatedRecordsTruncated: bool
    chronologyRelationToPrevious: Literal[
        "first",
        "strictly-after",
        "overlaps-or-uncertain",
    ]


class TimelinePassageTimeEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passageId: str
    documentId: str
    sourceId: str
    timeRole: PassageDateRole
    linkedTargetId: str | None = None
    historicalDate: HistoricalDate


class GetTimelineContextOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpusId: str
    anchorDescription: str
    scopeNote: str
    orderingNote: str
    events: list[TimelineEventEntry]
    eventTotalCount: int = Field(ge=0)
    eventReturnedCount: int = Field(ge=0)
    eventsTruncated: bool
    passageTimes: list[TimelinePassageTimeEntry]
    passageTimeTotalCount: int = Field(ge=0)
    passageTimeReturnedCount: int = Field(ge=0)
    passageTimesTruncated: bool
    passageTimeCountsByRole: dict[PassageDateRole, int]
    returnedCount: int
    truncated: bool


def _event_entries(events: list, related_record_limit: int) -> list[TimelineEventEntry]:
    budget = CollectionBudget(related_record_limit)
    entries: list[TimelineEventEntry] = []
    previous = None
    for event in events:
        related_record_ids = budget.take(list(event.relatedRecordIds))
        if previous is None:
            chronology_relation = "first"
        elif event.eventTime.earliest > previous.eventTime.latest:
            chronology_relation = "strictly-after"
        else:
            chronology_relation = "overlaps-or-uncertain"
        entries.append(
            TimelineEventEntry(
                eventId=event.id,
                title=event.title,
                placeId=event.placeId,
                eventTime=event.eventTime,
                reviewStatus=event.reviewStatus.value,
                visibility=event.visibility.value,
                relatedRecordIds=related_record_ids,
                relatedRecordTotalCount=len(event.relatedRecordIds),
                relatedRecordReturnedCount=len(related_record_ids),
                relatedRecordsTruncated=len(related_record_ids) < len(event.relatedRecordIds),
                chronologyRelationToPrevious=chronology_relation,
            )
        )
        previous = event
    return entries


def _event_entry(event) -> TimelineEventEntry:
    """Compatibility helper for callers needing one unbounded event projection."""
    return TimelineEventEntry(
        eventId=event.id,
        title=event.title,
        placeId=event.placeId,
        eventTime=event.eventTime,
        reviewStatus=event.reviewStatus.value,
        visibility=event.visibility.value,
        relatedRecordIds=list(event.relatedRecordIds),
        relatedRecordTotalCount=len(event.relatedRecordIds),
        relatedRecordReturnedCount=len(event.relatedRecordIds),
        relatedRecordsTruncated=False,
        chronologyRelationToPrevious="first",
    )


def _overlaps(historical: HistoricalDate, start: date | None, end: date | None) -> bool:
    return (start is None or historical.latest >= start) and (end is None or historical.earliest <= end)


def _passage_time_entries(corpus: InvestigationCorpus, passage_ids: set[str]) -> list[TimelinePassageTimeEntry]:
    investigation = corpus.get_investigation()
    documents = {document.id: document for document in investigation.documents}
    sources = {source.id: source for source in investigation.sources}
    links_by_passage: dict[str, list] = {}
    for link in investigation.evidenceLinks:
        links_by_passage.setdefault(link.passageId, []).append(link)
    events = {event.id: event for event in investigation.events}
    knowledge_states = {state.id: state for state in investigation.knowledgeStates}
    entries: list[TimelinePassageTimeEntry] = []

    matching_passages = (item for item in investigation.passages if item.id in passage_ids)
    for passage in sorted(matching_passages, key=lambda item: item.id):
        document = documents[passage.documentId]
        source = sources[document.sourceId]
        represented: list[tuple[PassageDateRole, str | None, HistoricalDate]] = []
        if passage.sentTime is not None:
            represented.append((PassageDateRole.SENT_TIME, None, passage.sentTime))
        if passage.receivedTime is not None:
            represented.append((PassageDateRole.RECEIVED_TIME, None, passage.receivedTime))
        represented.append((PassageDateRole.SOURCE_DATE, None, source.dateOfSource))
        for link in links_by_passage.get(passage.id, []):
            if link.targetType.value == "event" and link.targetId in events:
                represented.append(
                    (PassageDateRole.LINKED_EVENT_TIME, link.targetId, events[link.targetId].eventTime)
                )
            elif link.targetType.value == "knownAtTime" and link.targetId in knowledge_states:
                represented.append(
                    (
                        PassageDateRole.LINKED_ACTOR_AWARENESS_TIME,
                        link.targetId,
                        knowledge_states[link.targetId].asOfDate,
                    )
                )
        unique = {
            (role, target_id, value.earliest, value.latest, value.label): value
            for role, target_id, value in represented
        }
        for (role, target_id, _earliest, _latest, _label), historical in sorted(
            unique.items(),
            key=lambda item: (
                item[0][0].value,
                item[0][1] or "",
                item[0][2],
                item[0][3],
                item[0][4] or "",
            ),
        ):
            entries.append(
                TimelinePassageTimeEntry(
                    passageId=passage.id,
                    documentId=document.id,
                    sourceId=source.id,
                    timeRole=role,
                    linkedTargetId=target_id,
                    historicalDate=historical,
                )
            )
    return entries


def _get_timeline_context(
    tool_input: GetTimelineContextInput,
    context: ToolExecutionContext,
    corpus: InvestigationCorpus,
) -> GetTimelineContextOutput:
    ordered = corpus.get_events_ordered()
    ordered_ids = [event.id for event in ordered]
    passage_ids: set[str] = set()

    if tool_input.eventId is not None:
        anchor = corpus.get_event(tool_input.eventId)
        index = ordered_ids.index(anchor.id)
        candidates = ordered[
            max(0, index - tool_input.beforeCount) : index + 1 + tool_input.afterCount
        ]
        for event in candidates:
            passage_ids.update(passage.id for passage in corpus.get_passages_for(event.id))
        anchor_description = f'events around Event "{anchor.id}"'
    elif tool_input.placeId is not None:
        place = corpus.get_place(tool_input.placeId)
        candidate_ids = {event.id for event in corpus.get_events_at_place(place.id)}
        candidates = [event for event in ordered if event.id in candidate_ids]
        for event in candidates:
            passage_ids.update(passage.id for passage in corpus.get_passages_for(event.id))
        anchor_description = f'events at Place "{place.id}"'
    elif tool_input.entityId is not None:
        entity = corpus.get_entity(tool_input.entityId)
        if entity.entityType == "place":
            candidate_ids = {event.id for event in corpus.get_events_at_place(entity.id)}
            candidates = [event for event in ordered if event.id in candidate_ids]
            for event in candidates:
                passage_ids.update(passage.id for passage in corpus.get_passages_for(event.id))
            anchor_description = f'events at Entity (place) "{entity.id}"'
        else:
            candidates = []
            anchor_description = (
                f'events structurally linked to Entity "{entity.id}" -- none: '
                "GeneratedEvent has no person-reference field in this contract"
            )
    elif tool_input.claimId is not None or tool_input.relationshipId is not None:
        record_id = tool_input.claimId or tool_input.relationshipId
        if tool_input.claimId is not None:
            corpus.get_claim(record_id)
        else:
            corpus.get_relationship(record_id)
        candidates = [event for event in ordered if record_id in event.relatedRecordIds]
        passage_ids.update(passage.id for passage in corpus.get_passages_for(record_id))
        for event in candidates:
            passage_ids.update(passage.id for passage in corpus.get_passages_for(event.id))
        anchor_description = f'events related to record "{record_id}"'
    else:
        candidates = [
            event for event in ordered if _overlaps(event.eventTime, tool_input.dateFrom, tool_input.dateTo)
        ]
        investigation = corpus.get_investigation()
        passage_ids = {passage.id for passage in investigation.passages}
        anchor_description = f"represented time entries overlapping {tool_input.dateFrom} through {tool_input.dateTo}"

    passage_times = _passage_time_entries(corpus, passage_ids)
    if tool_input.dateFrom is not None or tool_input.dateTo is not None:
        passage_times = [
            item for item in passage_times if _overlaps(item.historicalDate, tool_input.dateFrom, tool_input.dateTo)
        ]

    effective_limit = min(tool_input.maxResults, context.maximumResults)
    event_entries = _event_entries(candidates, effective_limit)
    combined_count = len(event_entries) + len(passage_times)
    if event_entries and passage_times and effective_limit >= 2:
        event_quota = (effective_limit + 1) // 2
        passage_quota = effective_limit // 2
    elif event_entries:
        event_quota = effective_limit
        passage_quota = 0
    else:
        event_quota = 0
        passage_quota = effective_limit
    limited_events = event_entries[:event_quota]
    limited_passages = passage_times[:passage_quota]
    remaining = effective_limit - len(limited_events) - len(limited_passages)
    if remaining:
        extra_events = event_entries[len(limited_events) : len(limited_events) + remaining]
        limited_events.extend(extra_events)
        remaining -= len(extra_events)
    if remaining:
        limited_passages.extend(
            passage_times[len(limited_passages) : len(limited_passages) + remaining]
        )
    returned_count = len(limited_events) + len(limited_passages)
    passage_time_counts_by_role = {
        role: sum(item.timeRole == role for item in passage_times)
        for role in PassageDateRole
    }

    return GetTimelineContextOutput(
        corpusId=tool_input.corpusId,
        anchorDescription=anchor_description,
        scopeNote=(
            "Only represented event-time and passage sent-time, received-time, source-date, "
            "linked-event-time, and linked-actor-awareness-time fields are returned. This is not "
            "a claim of report-time, discovery-time, interpretation-time, or corpus completeness."
        ),
        orderingNote=(
            "Events use stored TimelineEntry order when present, with earliest represented "
            "bound and ID only as a fallback for unlisted events. "
            "chronologyRelationToPrevious marks overlapping or uncertain intervals; list order "
            "alone does not assert a precise sequence."
        ),
        events=limited_events,
        eventTotalCount=len(event_entries),
        eventReturnedCount=len(limited_events),
        eventsTruncated=len(limited_events) < len(event_entries),
        passageTimes=limited_passages,
        passageTimeTotalCount=len(passage_times),
        passageTimeReturnedCount=len(limited_passages),
        passageTimesTruncated=len(limited_passages) < len(passage_times),
        passageTimeCountsByRole=passage_time_counts_by_role,
        returnedCount=returned_count,
        truncated=combined_count > returned_count,
    )


GET_TIMELINE_CONTEXT_TOOL = ToolDefinition(
    name="get_timeline_context",
    version="e2-get-timeline-context-v2",
    description=(
        "Return bounded event and passage time context while preserving each represented time role. "
        "Use it for chronology questions; avoid treating the result as a complete historical chronology."
    ),
    input_model=GetTimelineContextInput,
    output_model=GetTimelineContextOutput,
    required_capabilities=frozenset({"timeline"}),
    max_result_limit=MAX_RESULT_COUNT,
    use_when="A chronology question needs event or source-passage times from the selected corpus.",
    avoid_when="The question requires report, discovery, or interpretation times absent from the package.",
    output_summary="Bounded event entries and role-labelled passage times with an explicit scope note.",
    execute=_get_timeline_context,
)
