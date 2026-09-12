"""Assembly: turn grounded extractions into contract geography + events.

The glue between stages 7 (extraction), 9 (timeline), and 12 (geography). Given
the *built* passages of a corpus, it runs event extraction, resolves each
distinct place name through the period-aware geocoder, and assembles the
contract records the map-first workspace and timeline render from:

- a ``PlaceEntity`` per distinct place name (with period-accurate coordinates
  when a gazetteer can place it *in period*, and ``coordinates=None`` otherwise
  -- never a fabricated point);
- a ``GeneratedEvent`` per extracted event, located at its place and carrying
  its passage citations;
- a ``GeneratedEvidenceLink`` per (passage -> event) citation, which is the
  canonical, reverse-indexed grounding the validator enforces;
- a ``TimelineEntry`` per event, ordered by year then title.

Everything produced is ``reviewStatus=PROPOSED`` / ``visibility=PUBLIC`` -- a
draft proposal, never reviewed evidence. Honesty is inherited from
``extract_events`` (no ungrounded or anachronistic event survives) and from the
geocoder (no coordinate is invented). The step is subject-agnostic: it never
branches on the topic or which place/event it is.

It owns its own ``*-ev-*`` id namespace so ``corpus_builder`` can merge its
records alongside the scope scaffolding without id collisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from ..contracts.enums import (
    DatePrecision,
    EvidenceLinkRole,
    EvidenceTargetType,
    LocationPrecision,
    ReviewStatus,
    Visibility,
)
from ..contracts.generated_investigation import (
    GeneratedEvent,
    GeneratedEvidenceLink,
    TimelineEntry,
)
from ..contracts.shared import (
    Coordinates,
    HistoricalDate,
    Passage,
    PlaceEntity,
    PlacePeriodRecord,
)
from .extraction import ExtractedEvent, extract_events
from .geocoding import GeoResolution, PeriodAwareGeocoder
from ..ai.models.protocol import ModelProvider

# A place name we could not locate *in period* carries no coordinate and the
# lowest precision -- honest uncertainty, never a modern-as-historical guess.
_UNLOCATED_PRECISION = LocationPrecision.APPROXIMATE
_UNRESOLVED_POLITY = "Not established (auto-extracted draft; requires research)"


@dataclass(frozen=True)
class Enrichment:
    """The structured records assembled from one extraction pass.

    ``places`` are keyed into by ``events`` via ``placeId``; ``evidence_links``
    are the canonical grounding listed back by each event's ``evidenceLinkIds``;
    ``timeline`` orders the events. Empty when nothing grounded was extracted --
    the corpus then stays an evidence-only draft, exactly as before."""

    places: list[PlaceEntity] = field(default_factory=list)
    events: list[GeneratedEvent] = field(default_factory=list)
    evidence_links: list[GeneratedEvidenceLink] = field(default_factory=list)
    timeline: list[TimelineEntry] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.events


def _period_label(period: HistoricalDate) -> str:
    if period.label:
        return period.label
    return f"{period.earliest.year}-{period.latest.year}"


def _event_time(year: int) -> HistoricalDate:
    """A year-known, day-unknown time: the whole year, honestly bounded."""

    return HistoricalDate(
        precision=DatePrecision.RANGE,
        earliest=date(year, 1, 1),
        latest=date(year, 12, 31),
        label=str(year),
    )


def _place_from_resolution(
    place_id: str,
    place_name: str,
    resolution: GeoResolution | None,
    period_label: str,
) -> PlaceEntity:
    """Build a PlaceEntity, period-accurate when the geocoder placed it, and an
    honest low-precision stub (no coordinates) when it could not."""

    if resolution is not None:
        coordinates: Coordinates | None = resolution.coordinates
        name_at_time = resolution.nameAtTime or place_name
        precision = resolution.precision if coordinates is not None else _UNLOCATED_PRECISION
    else:
        coordinates = None
        name_at_time = place_name
        precision = _UNLOCATED_PRECISION

    return PlaceEntity(
        id=place_id,
        entityType="place",
        canonicalName=place_name,
        periodRecords=[
            PlacePeriodRecord(
                periodLabel=period_label,
                nameAtTime=name_at_time,
                controllingPolity=_UNRESOLVED_POLITY,
                precision=precision,
            )
        ],
        reviewStatus=ReviewStatus.PROPOSED,
        coordinates=coordinates,
    )


def assemble_enrichment(
    passages: list[Passage],
    period: HistoricalDate,
    topic: str,
    *,
    extractor: ModelProvider,
    geocoder: PeriodAwareGeocoder,
) -> Enrichment:
    """Extract grounded events, geolocate their places *for the period*, and
    assemble contract geography + events + evidence links + timeline."""

    extracted = extract_events(passages, period, topic, extractor)
    if not extracted:
        return Enrichment()

    period_label = _period_label(period)

    # One PlaceEntity per distinct place name (first-seen order), geocoded once.
    place_id_by_name: dict[str, str] = {}
    places: list[PlaceEntity] = []
    for event in extracted:
        if event.placeName in place_id_by_name:
            continue
        place_id = f"place-ev-{len(places):04d}"
        place_id_by_name[event.placeName] = place_id
        resolution = geocoder.resolve(event.placeName, period)
        places.append(_place_from_resolution(place_id, event.placeName, resolution, period_label))

    events: list[GeneratedEvent] = []
    evidence_links: list[GeneratedEvidenceLink] = []
    for index, event in enumerate(_ordered(extracted)):
        event_id = f"event-ev-{index:04d}"
        link_ids: list[str] = []
        for link_index, passage_id in enumerate(event.passageIds):
            link_id = f"evidence-ev-{index:04d}-{link_index}"
            link_ids.append(link_id)
            evidence_links.append(
                GeneratedEvidenceLink(
                    id=link_id,
                    targetType=EvidenceTargetType.EVENT,
                    targetId=event_id,
                    passageId=passage_id,
                    role=EvidenceLinkRole.SUPPORTING,
                )
            )
        events.append(
            GeneratedEvent(
                id=event_id,
                title=event.title,
                placeId=place_id_by_name[event.placeName],
                eventTime=_event_time(event.year),
                evidenceLinkIds=link_ids,
                relatedRecordIds=[],
                reviewStatus=ReviewStatus.PROPOSED,
                visibility=Visibility.PUBLIC,
            )
        )

    timeline = [
        TimelineEntry(id=f"timeline-{event.id}", eventId=event.id, order=order)
        for order, event in enumerate(events)
    ]

    return Enrichment(
        places=places,
        events=events,
        evidence_links=evidence_links,
        timeline=timeline,
    )


def _ordered(events: list[ExtractedEvent]) -> list[ExtractedEvent]:
    """Chronological, then by title -- a stable timeline order independent of
    the model's emission order."""

    return sorted(events, key=lambda event: (event.year, event.title))


__all__ = ["Enrichment", "assemble_enrichment"]
