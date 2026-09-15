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
    ControlBasis,
    ControlStateKind,
    DatePrecision,
    EvidenceLinkRole,
    EvidenceTargetType,
    GeometryType,
    LocationPrecision,
    ReviewStatus,
    Visibility,
)
from ..contracts.generated_investigation import (
    ControlState,
    GeneratedEvent,
    GeneratedEvidenceLink,
    TerritoryGeometry,
    TimelineEntry,
)
from ..contracts.shared import (
    Coordinates,
    HistoricalDate,
    Passage,
    PlaceEntity,
    PlacePeriodRecord,
)
from .boundaries import BoundaryResolver
from .control_state import extract_control_states
from .extraction import ExtractedEvent, extract_events
from .geocoding import GeoResolution, PeriodAwareGeocoder
from ..ai.models.protocol import ModelProvider

# Control/influence/contested territory is region-level: a boundary polygon, not a
# point, so it never claims building/city precision (contract Rule 22).
_TERRITORY_PRECISION = LocationPrecision.REGION

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
    control_states: list[ControlState] = field(default_factory=list)
    territory_geometries: list[TerritoryGeometry] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.events

    @property
    def has_territory(self) -> bool:
        """True when at least one control state resolved to a sourced polygon."""

        return bool(self.control_states)


def _period_label(period: HistoricalDate) -> str:
    if period.label:
        return period.label
    return f"{_year_label(period.lower_key[0])}-{_year_label(period.upper_key[0])}"


def _year_label(year: int) -> str:
    """Honest display of a signed astronomical year (ADR-005): '1914', '44 BC'."""

    return str(year) if year >= 1 else f"{1 - year} BC"


def _event_time(year: int) -> HistoricalDate:
    """A year-known, day-unknown time: the whole year, honestly bounded.

    Era-capable (ADR-005): the signed year is always carried; the CE-only
    calendar dates are added for year >= 1 (day precision) and omitted for BC.
    """

    ce = year >= 1
    return HistoricalDate(
        precision=DatePrecision.RANGE,
        earliest=date(year, 1, 1) if ce else None,
        latest=date(year, 12, 31) if ce else None,
        earliestYear=year,
        latestYear=year,
        label=_year_label(year),
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
    boundary_resolver: BoundaryResolver | None = None,
) -> Enrichment:
    """Extract grounded events, geolocate their places *for the period*, and
    assemble contract geography + events + evidence links + timeline. When a
    ``boundary_resolver`` is supplied, also extract grounded control states and
    resolve each to a sourced boundary polygon (ADR-004 territory layer)."""

    extracted = extract_events(passages, period, topic, extractor)
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

    control_states, territory_geometries, control_links = _assemble_control_states(
        passages, period, topic, extractor, boundary_resolver
    )

    return Enrichment(
        places=places,
        events=events,
        evidence_links=evidence_links + control_links,
        timeline=timeline,
        control_states=control_states,
        territory_geometries=territory_geometries,
    )


def _ordered(events: list[ExtractedEvent]) -> list[ExtractedEvent]:
    """Chronological, then by title -- a stable timeline order independent of
    the model's emission order."""

    return sorted(events, key=lambda event: (event.year, event.title))


def _assemble_control_states(
    passages: list[Passage],
    period: HistoricalDate,
    topic: str,
    extractor: ModelProvider,
    boundary_resolver: BoundaryResolver | None,
) -> tuple[list[ControlState], list[TerritoryGeometry], list[GeneratedEvidenceLink]]:
    """Extract grounded control states and resolve each to a SOURCED polygon. A
    state whose polity cannot be resolved to a period-appropriate polygon is
    omitted -- never a fabricated frontier. Geometry is deduplicated per resolved
    (polity, attested-year). Owns the ``control-ev-*`` / ``territory-geo-*`` /
    ``evidence-cs-*`` id namespaces so ``corpus_builder`` can merge without clashes."""

    if boundary_resolver is None:
        return [], [], []
    extracted = extract_control_states(passages, period, topic, extractor)
    if not extracted:
        return [], [], []

    control_states: list[ControlState] = []
    geometries: list[TerritoryGeometry] = []
    links: list[GeneratedEvidenceLink] = []
    geometry_id_by_key: dict[tuple[str, int], str] = {}

    for index, state in enumerate(extracted):
        resolved = boundary_resolver.resolve(state.polity, state.fromYear)
        if resolved is None:
            continue  # no sourced polygon for this polity/period -> omitted

        key = (resolved.matched_name, resolved.attested_year)
        geometry_ref = geometry_id_by_key.get(key)
        if geometry_ref is None:
            geometry_ref = f"territory-geo-{len(geometries):04d}"
            geometry_id_by_key[key] = geometry_ref
            geometries.append(
                TerritoryGeometry(
                    id=geometry_ref,
                    type=GeometryType(resolved.geometry_type),
                    coordinates=resolved.coordinates,
                    sourceDataset=resolved.source_dataset,
                    attestedYear=resolved.attested_year,
                    license=resolved.license,
                    polity=resolved.matched_name,
                )
            )

        control_id = f"control-ev-{index:04d}"
        link_ids: list[str] = []
        for link_index, passage_id in enumerate(state.passageIds):
            link_id = f"evidence-cs-{index:04d}-{link_index}"
            link_ids.append(link_id)
            links.append(
                GeneratedEvidenceLink(
                    id=link_id,
                    targetType=EvidenceTargetType.CONTROL_STATE,
                    targetId=control_id,
                    passageId=passage_id,
                    role=EvidenceLinkRole.SUPPORTING,
                )
            )
        control_states.append(
            ControlState(
                id=control_id,
                polity=state.polity,
                kind=ControlStateKind(state.kind),
                basis=ControlBasis(state.basis) if state.basis else None,
                sovereignPolity=state.sovereignPolity,
                validFrom=_event_time(state.fromYear),
                validTo=_event_time(state.toYear),
                geometryRef=geometry_ref,
                precision=_TERRITORY_PRECISION,
                evidenceLinkIds=link_ids,
                reviewStatus=ReviewStatus.PROPOSED,
                visibility=Visibility.PUBLIC,
            )
        )

    return control_states, geometries, links


__all__ = ["Enrichment", "assemble_enrichment"]
