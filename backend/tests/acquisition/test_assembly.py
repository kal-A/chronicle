"""Assembly-stage unit tests (stages 7 -> 9/12 glue).

assemble_enrichment runs event extraction over built passages, geolocates each
distinct place *for the period*, and assembles the contract geography + events +
evidence links + timeline. These tests use DeterministicModelProvider (no model)
and a stub geocoder (no network) with neutral placeholder content -- the stage is
subject-agnostic and never branches on which place/event it is.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from chronicle.acquisition.assembly import Enrichment, assemble_enrichment
from chronicle.acquisition.boundaries import BoundaryResolver
from chronicle.acquisition.control_state import ExtractedControlState, ExtractedControlStates
from chronicle.acquisition.extraction import ExtractedEvent, ExtractedEvents
from chronicle.acquisition.geocoding import GeoResolution
from chronicle.ai.models.deterministic import DeterministicModelProvider
from chronicle.contracts.enums import (
    ControlStateKind,
    DatePrecision,
    EvidenceTargetType,
    LocationPrecision,
)
from chronicle.contracts.shared import Coordinates, HistoricalDate, Passage

_BOUNDARIES_FIXTURE = Path(__file__).parent / "fixtures" / "boundaries"


def _period() -> HistoricalDate:
    return HistoricalDate(
        precision=DatePrecision.RANGE,
        earliest=date(1660, 1, 1),
        latest=date(1670, 12, 31),
        label="1660-1670",
    )


def _passages() -> list[Passage]:
    return [
        Passage(id="psg-0000-0000", documentId="doc-0000", excerpt="Placeholder one.", locator="d#1"),
        Passage(id="psg-0000-0001", documentId="doc-0000", excerpt="Placeholder two.", locator="d#2"),
    ]


def _extractor(events: list[ExtractedEvent]) -> DeterministicModelProvider:
    provider = DeterministicModelProvider()
    provider.enqueue_value(ExtractedEvents(events=events))
    return provider


class _StubGeocoder:
    """Returns a canned resolution per place name; None for the rest. Mirrors the
    PeriodAwareGeocoder.resolve() surface assemble_enrichment depends on."""

    def __init__(self, resolutions: dict[str, GeoResolution]) -> None:
        self._resolutions = resolutions
        self.calls: list[str] = []

    def resolve(self, place_name: str, period: HistoricalDate) -> GeoResolution | None:
        self.calls.append(place_name)
        return self._resolutions.get(place_name)


def _resolution(name: str, lat: float, lng: float) -> GeoResolution:
    return GeoResolution(
        canonicalName=name,
        nameAtTime=name,
        coordinates=Coordinates(lat=lat, lng=lng),
        precision=LocationPrecision.CITY,
        providerName="stub",
        provenanceUrl=f"https://example/{name}",
    )


def test_assembles_located_event_with_grounded_evidence_and_timeline():
    events = [ExtractedEvent(title="A fire", placeName="Placeholdertown", year=1666, passageIds=["psg-0000-0000"])]
    geocoder = _StubGeocoder({"Placeholdertown": _resolution("Placeholdertown", 51.5, -0.12)})

    enrichment = assemble_enrichment(_passages(), _period(), "A topic", extractor=_extractor(events), geocoder=geocoder)

    assert not enrichment.is_empty
    # place: located in period with coordinates + city precision
    assert len(enrichment.places) == 1
    place = enrichment.places[0]
    assert place.canonicalName == "Placeholdertown"
    assert place.coordinates is not None and place.coordinates.lat == 51.5
    assert place.periodRecords[0].precision is LocationPrecision.CITY
    assert place.reviewStatus.value == "proposed"
    # event: located at the place, proposed + public
    assert len(enrichment.events) == 1
    event = enrichment.events[0]
    assert event.placeId == place.id
    assert event.visibility.value == "public"
    assert event.reviewStatus.value == "proposed"
    assert event.eventTime.label == "1666"
    # evidence link: canonical + reverse-indexed grounding
    assert len(enrichment.evidence_links) == 1
    link = enrichment.evidence_links[0]
    assert link.targetType.value == "event" and link.targetId == event.id
    assert link.role.value == "supporting" and link.passageId == "psg-0000-0000"
    assert event.evidenceLinkIds == [link.id]
    # timeline: one ordered entry pointing at the event
    assert [(t.eventId, t.order) for t in enrichment.timeline] == [(event.id, 0)]


def test_unlocated_place_keeps_no_coordinates_and_low_precision():
    # Historicity: when the geocoder cannot place it *in period*, we keep the
    # place at the lowest precision with NO coordinate -- never a fabricated one.
    events = [ExtractedEvent(title="An event", placeName="Nowhere", year=1666, passageIds=["psg-0000-0001"])]
    geocoder = _StubGeocoder({})  # resolves nothing

    enrichment = assemble_enrichment(_passages(), _period(), "A topic", extractor=_extractor(events), geocoder=geocoder)

    place = enrichment.places[0]
    assert place.coordinates is None
    assert place.periodRecords[0].precision is LocationPrecision.APPROXIMATE
    # the event still exists and stays grounded -- geography uncertainty never
    # drops a grounded event
    assert enrichment.events[0].placeId == place.id


def test_distinct_place_names_get_one_place_each_and_shared_names_are_reused():
    events = [
        ExtractedEvent(title="First", placeName="Placeholdertown", year=1661, passageIds=["psg-0000-0000"]),
        ExtractedEvent(title="Second", placeName="Placeholdertown", year=1662, passageIds=["psg-0000-0001"]),
        ExtractedEvent(title="Third", placeName="Otherville", year=1663, passageIds=["psg-0000-0000"]),
    ]
    geocoder = _StubGeocoder({"Placeholdertown": _resolution("Placeholdertown", 1.0, 2.0)})

    enrichment = assemble_enrichment(_passages(), _period(), "A topic", extractor=_extractor(events), geocoder=geocoder)

    assert len(enrichment.places) == 2  # two distinct names
    assert geocoder.calls.count("Placeholdertown") == 1  # geocoded once, not per event
    by_title = {e.title: e for e in enrichment.events}
    assert by_title["First"].placeId == by_title["Second"].placeId  # shared place reused
    assert by_title["Third"].placeId != by_title["First"].placeId


def test_timeline_is_chronological_regardless_of_emission_order():
    events = [
        ExtractedEvent(title="Later", placeName="Placeholdertown", year=1668, passageIds=["psg-0000-0000"]),
        ExtractedEvent(title="Earlier", placeName="Placeholdertown", year=1662, passageIds=["psg-0000-0001"]),
    ]
    geocoder = _StubGeocoder({"Placeholdertown": _resolution("Placeholdertown", 1.0, 2.0)})

    enrichment = assemble_enrichment(_passages(), _period(), "A topic", extractor=_extractor(events), geocoder=geocoder)

    ordered_titles = [next(e.title for e in enrichment.events if e.id == t.eventId) for t in enrichment.timeline]
    assert ordered_titles == ["Earlier", "Later"]


def test_no_extracted_events_yields_empty_enrichment_and_no_geocoding():
    geocoder = _StubGeocoder({})
    enrichment = assemble_enrichment(_passages(), _period(), "A topic", extractor=_extractor([]), geocoder=geocoder)

    assert enrichment == Enrichment()
    assert enrichment.is_empty
    assert geocoder.calls == []  # nothing to locate -> no lookups


def _extractor_with_territory(
    events: list[ExtractedEvent], states: list[ExtractedControlState]
) -> DeterministicModelProvider:
    """assemble_enrichment makes two model passes when a resolver is supplied:
    events first, then control states — enqueue both, in order."""

    provider = DeterministicModelProvider()
    provider.enqueue_value(ExtractedEvents(events=events))
    provider.enqueue_value(ExtractedControlStates(controlStates=states))
    return provider


def test_assembles_territory_from_resolved_control_states():
    states = [
        # Alpha is in the boundary fixture -> resolves to a sourced polygon.
        ExtractedControlState(
            polity="Alpha", kind="controlled", basis="sovereign",
            fromYear=1665, toYear=1668, passageIds=["psg-0000-0000"],
        ),
        # Zeta is in no snapshot -> no geometry -> the state is omitted, not faked.
        ExtractedControlState(
            polity="Zeta", kind="influence", fromYear=1665, toYear=1668, passageIds=["psg-0000-0000"],
        ),
    ]
    enrichment = assemble_enrichment(
        _passages(), _period(), "A topic",
        extractor=_extractor_with_territory([], states),
        geocoder=_StubGeocoder({}),
        boundary_resolver=BoundaryResolver(_BOUNDARIES_FIXTURE),
    )

    assert enrichment.has_territory
    assert [cs.polity for cs in enrichment.control_states] == ["Alpha"]  # Zeta omitted
    assert len(enrichment.territory_geometries) == 1

    geometry = enrichment.territory_geometries[0]
    control_state = enrichment.control_states[0]
    assert control_state.geometryRef == geometry.id
    assert geometry.sourceDataset == "historical-basemaps"
    assert control_state.kind is ControlStateKind.CONTROLLED
    assert control_state.precision is LocationPrecision.REGION  # boundary-level, honest

    # a supporting evidence link targets the control state, bidirectionally
    link = next(link for link in enrichment.evidence_links if link.targetId == control_state.id)
    assert link.targetType is EvidenceTargetType.CONTROL_STATE
    assert link.id in control_state.evidenceLinkIds


def test_no_boundary_resolver_yields_no_territory():
    enrichment = assemble_enrichment(
        _passages(), _period(), "A topic",
        extractor=_extractor([]),
        geocoder=_StubGeocoder({}),
    )
    assert not enrichment.has_territory
    assert enrichment.control_states == []
    assert enrichment.territory_geometries == []
