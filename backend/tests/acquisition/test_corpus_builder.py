"""corpus_builder tests, including the round-trip through the real
PackageBackedCorpus the four agents use — proving an acquired corpus is
loadable and searchable exactly like a curated fixture."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest

from chronicle.acquisition.chunking import chunk_source
from chronicle.acquisition.contracts import AcquiredSource, SourceCandidate
from chronicle.acquisition.corpus_builder import build_corpus, deterministic_package_id
from chronicle.contracts.enums import PackageStatus, RightsStatus, SourceType
from chronicle.corpus.contracts import PassageSearchRequest
from chronicle.corpus.package_corpus import (
    CAPABILITY_PASSAGES,
    CAPABILITY_SOURCE_COMPARISON,
    PackageBackedCorpus,
)


def _acquired(candidate_id: str, title: str, body: str, connector: str = "wikipedia") -> AcquiredSource:
    candidate = SourceCandidate(
        candidateId=candidate_id,
        connector=connector,
        title=title,
        sourceType=SourceType.TERTIARY_REFERENCE,
        fullTextAvailable=True,
        rightsStatus=RightsStatus.LICENSED,
        url=f"https://example.org/{candidate_id}",
        language="en",
    )
    return AcquiredSource(
        candidate=candidate,
        text=body,
        contentType="text/plain",
        contentSha256=f"hash-{candidate_id}",
        charCount=len(body),
        retrievedAt=datetime(2026, 9, 9, tzinfo=timezone.utc),
    )


def _sample_inputs():
    src_a = _acquired("wikipedia:en:1", "Alpha Overview", "Alpha describes the zeppelin registry in detail. " * 20)
    src_b = _acquired("wikipedia:en:2", "Beta Overview", "Beta covers maritime signalling conventions. " * 20)
    passages = chunk_source(src_a) + chunk_source(src_b)
    return [src_a, src_b], passages


def test_build_corpus_produces_a_valid_partial_evidence_package():
    acquired, passages = _sample_inputs()
    investigation = build_corpus(
        topic="a placeholder subject",
        interpreted_question="What happened in the placeholder subject?",
        geographic_scope=["Somewhere"],
        date_earliest=date(1800, 1, 1),
        date_latest=date(1850, 12, 31),
        acquired=acquired,
        passages=passages,
    )

    assert investigation.status is PackageStatus.PARTIAL
    assert investigation.generationReport.outcome.value == "partial"
    assert len(investigation.sources) == 2
    assert len(investigation.documents) == 2
    assert len(investigation.passages) == len(passages)
    # no fabricated historical records
    assert investigation.claims == []
    assert investigation.relationships == []
    assert investigation.events == []
    assert investigation.knowledgeStates == []
    # one scope placeholder place, clearly proposed/unreviewed
    assert len(investigation.entities) == 1
    place = investigation.entities[0]
    assert place.entityType == "place"
    assert place.reviewStatus.value == "proposed"
    # every scene reference resolves (validator already enforced this on build)
    assert investigation.scenes[0].placeIds == [place.id]


def test_build_corpus_accepts_a_bc_scope_via_signed_years():
    # ADR-005: a BC investigation enters the pipeline as signed years (no calendar
    # date, which is CE-only). The scope date range carries the signed years and
    # the package still validates.
    acquired, passages = _sample_inputs()
    investigation = build_corpus(
        topic="a placeholder subject",
        interpreted_question="What happened in the placeholder subject?",
        geographic_scope=["Somewhere"],
        year_earliest=-218,  # 219 BC
        year_latest=-201,  # 202 BC
        acquired=acquired,
        passages=passages,
    )

    date_range = investigation.scenes[0].dateRange
    assert date_range.earliestYear == -218 and date_range.latestYear == -201
    assert date_range.earliest is None and date_range.latest is None
    assert investigation.scope.dateRange.earliestYear == -218
    assert investigation.status is PackageStatus.PARTIAL


def test_acquired_corpus_loads_and_searches_through_package_backed_corpus(tmp_path):
    acquired, passages = _sample_inputs()
    investigation = build_corpus(
        topic="a placeholder subject",
        interpreted_question="What happened?",
        geographic_scope=["Somewhere"],
        date_earliest=date(1800, 1, 1),
        date_latest=date(1850, 12, 31),
        acquired=acquired,
        passages=passages,
    )

    package_path = tmp_path / "acquired.json"
    package_path.write_text(json.dumps(investigation.model_dump(mode="json")), encoding="utf-8")

    corpus = PackageBackedCorpus.load(
        corpus_id="acquired-test",
        package_path=package_path,
        title="Acquired Test Corpus",
        benchmark_role="acquisition round-trip test",
    )

    manifest = corpus.get_manifest()
    assert CAPABILITY_PASSAGES in manifest.supportedCapabilities
    assert CAPABILITY_SOURCE_COMPARISON in manifest.supportedCapabilities  # two sources

    result = corpus.search_passages(
        PassageSearchRequest(corpusId="acquired-test", query="zeppelin")
    )
    assert result.totalMatched >= 1
    assert any("zeppelin" in hit.excerpt.lower() for hit in result.hits)


def test_package_id_is_deterministic_for_same_topic_and_content():
    acquired, _ = _sample_inputs()
    first = deterministic_package_id("a placeholder subject", acquired)
    second = deterministic_package_id("a placeholder subject", acquired)
    assert first == second
    assert first.startswith("acq-")


def _period(earliest, latest, label):
    from chronicle.contracts.enums import DatePrecision
    from chronicle.contracts.shared import HistoricalDate

    return HistoricalDate(precision=DatePrecision.RANGE, earliest=earliest, latest=latest, label=label)


def _enricher(place_name, year, *, located):
    """An enrich() closure that cites the first *built* passage id, so its event
    is grounded in a real passage. ``located`` toggles whether the geocoder can
    place the name (coordinates) or not (honest low precision)."""
    from chronicle.acquisition.assembly import assemble_enrichment
    from chronicle.acquisition.extraction import ExtractedEvent, ExtractedEvents
    from chronicle.acquisition.geocoding import GeoResolution
    from chronicle.ai.models.deterministic import DeterministicModelProvider
    from chronicle.contracts.enums import LocationPrecision
    from chronicle.contracts.shared import Coordinates

    class _StubGeocoder:
        def resolve(self, name, period):
            if located and name == place_name:
                return GeoResolution(
                    canonicalName=name, nameAtTime=name,
                    coordinates=Coordinates(lat=51.5, lng=-0.12),
                    precision=LocationPrecision.CITY, providerName="stub",
                    provenanceUrl="https://example/x",
                )
            return None

    def enrich(passages):
        provider = DeterministicModelProvider()
        provider.enqueue_value(
            ExtractedEvents(events=[
                ExtractedEvent(title="An event", placeName=place_name, year=year, passageIds=[passages[0].id]),
            ])
        )
        return assemble_enrichment(
            passages, _period(date(1660, 1, 1), date(1670, 12, 31), "1660-1670"),
            "a placeholder subject", extractor=provider, geocoder=_StubGeocoder(),
        )

    return enrich


def _enriched_inputs():
    src = _acquired("wikipedia:en:1", "Alpha", "Alpha body about the placeholder event. " * 30)
    return [src], chunk_source(src)


def test_enrichment_populates_events_timeline_and_flips_timeline_capability():
    acquired, passages = _enriched_inputs()
    investigation = build_corpus(
        topic="a placeholder subject",
        interpreted_question="What happened?",
        geographic_scope=["London"],
        date_earliest=date(1660, 1, 1),
        date_latest=date(1670, 12, 31),
        acquired=acquired,
        passages=passages,
        date_label="1660-1670",
        enrich=_enricher("Placeholdertown", 1666, located=True),
    )

    # events + timeline + evidence links are now present and validated on build
    assert len(investigation.events) == 1
    assert len(investigation.timeline) == 1
    assert len(investigation.evidenceLinks) == 1
    # geography carries a located place with coordinates
    located = [e for e in investigation.entities if e.entityType == "place" and e.coordinates is not None]
    assert len(located) == 1 and located[0].canonicalName == "Placeholdertown"
    # timeline + map both light up (map because a place was located with coordinates)
    assert "timeline" not in investigation.interactionSpec.omittedCapabilities
    assert "map" not in investigation.interactionSpec.omittedCapabilities
    facet_values = {f.value for f in investigation.interactionSpec.enabledFacets}
    assert "timeline" in facet_values
    assert "map" in facet_values
    # the scene surfaces the events
    assert investigation.scenes[0].eventIds == [investigation.events[0].id]


def test_enrichment_drops_duplicate_scope_stub_when_name_matches_located_place():
    acquired, passages = _enriched_inputs()
    investigation = build_corpus(
        topic="a placeholder subject",
        interpreted_question="What happened?",
        geographic_scope=["London"],  # same name the enricher locates
        date_earliest=date(1660, 1, 1),
        date_latest=date(1670, 12, 31),
        acquired=acquired,
        passages=passages,
        date_label="1660-1670",
        enrich=_enricher("London", 1666, located=True),
    )

    londons = [e for e in investigation.entities if e.canonicalName == "London"]
    assert len(londons) == 1  # the richer located place won; the stub was dropped
    assert londons[0].coordinates is not None


def test_unlocated_enrichment_keeps_event_without_coordinates():
    acquired, passages = _enriched_inputs()
    investigation = build_corpus(
        topic="a placeholder subject",
        interpreted_question="What happened?",
        geographic_scope=["Somewhere"],
        date_earliest=date(1660, 1, 1),
        date_latest=date(1670, 12, 31),
        acquired=acquired,
        passages=passages,
        date_label="1660-1670",
        enrich=_enricher("Placeholdertown", 1666, located=False),
    )

    assert len(investigation.events) == 1  # grounded event survives
    assert all(e.coordinates is None for e in investigation.entities if e.entityType == "place")
    assert "timeline" not in investigation.interactionSpec.omittedCapabilities  # events exist
    # no place was located -> the generated map has nothing to draw, so map stays omitted
    assert "map" in investigation.interactionSpec.omittedCapabilities


def test_empty_enrichment_leaves_corpus_evidence_only():
    acquired, passages = _enriched_inputs()

    def enrich_nothing(passages):
        from chronicle.acquisition.assembly import Enrichment
        return Enrichment()

    investigation = build_corpus(
        topic="a placeholder subject",
        interpreted_question="What happened?",
        geographic_scope=["Somewhere"],
        date_earliest=date(1660, 1, 1),
        date_latest=date(1670, 12, 31),
        acquired=acquired,
        passages=passages,
        enrich=enrich_nothing,
    )

    assert investigation.events == []
    assert investigation.timeline == []
    assert "timeline" in investigation.interactionSpec.omittedCapabilities  # unchanged


def test_empty_geographic_scope_is_rejected():
    acquired, passages = _sample_inputs()
    with pytest.raises(ValueError):
        build_corpus(
            topic="x",
            interpreted_question="x?",
            geographic_scope=[],
            date_earliest=date(1800, 1, 1),
            date_latest=date(1850, 12, 31),
            acquired=acquired,
            passages=passages,
        )


def _territory_enricher():
    """An enrich() closure that extracts one grounded control state and resolves
    it against the boundary fixture — proving the territory layer builds and
    validates (Rule 22) end to end."""
    from pathlib import Path

    from chronicle.acquisition.assembly import assemble_enrichment
    from chronicle.acquisition.boundaries import BoundaryResolver
    from chronicle.acquisition.control_state import ExtractedControlState, ExtractedControlStates
    from chronicle.acquisition.extraction import ExtractedEvents
    from chronicle.ai.models.deterministic import DeterministicModelProvider

    class _StubGeocoder:
        def resolve(self, name, period):
            return None

    fixture = Path(__file__).parent / "fixtures" / "boundaries"

    def enrich(passages):
        from chronicle.contracts.enums import DatePrecision
        from chronicle.contracts.shared import HistoricalDate

        # The boundary fixture holds only BC snapshots, so the control period must
        # be BC — both for grounding and the resolver's era-distance guard.
        bc_period = HistoricalDate(
            precision=DatePrecision.RANGE, earliestYear=-300, latestYear=-200, label="300–200 BC"
        )
        provider = DeterministicModelProvider()
        provider.enqueue_value(ExtractedEvents(events=[]))
        provider.enqueue_value(
            ExtractedControlStates(controlStates=[
                ExtractedControlState(
                    polity="Alpha", kind="controlled", basis="sovereign",
                    fromYear=-280, toYear=-220, passageIds=[passages[0].id],
                ),
            ])
        )
        return assemble_enrichment(
            passages, bc_period,
            "a placeholder subject", extractor=provider, geocoder=_StubGeocoder(),
            boundary_resolver=BoundaryResolver(fixture),
        )

    return enrich


def test_enrichment_populates_territory_and_flips_territory_capability():
    acquired, passages = _enriched_inputs()
    investigation = build_corpus(
        topic="a placeholder subject",
        interpreted_question="Who held what?",
        geographic_scope=["London"],
        date_earliest=date(1660, 1, 1),
        date_latest=date(1670, 12, 31),
        acquired=acquired,
        passages=passages,
        date_label="1660-1670",
        enrich=_territory_enricher(),
    )

    # control states + sourced geometry are present and validated on build (Rule 22)
    assert len(investigation.controlStates) == 1
    assert len(investigation.territoryGeometries) == 1
    assert investigation.controlStates[0].geometryRef == investigation.territoryGeometries[0].id
    # the territory capability lights up
    facet_values = {f.value for f in investigation.interactionSpec.enabledFacets}
    assert "territory" in facet_values
    assert "territory" not in investigation.interactionSpec.omittedCapabilities


def test_search_projects_control_state_evidence_links(tmp_path):
    # Regression (ADR-004 T5, surfaced by the BC live verify): a passage whose
    # evidence link targets a controlState must project through passage search,
    # not raise KeyError('controlState'). The corpus read layer now resolves
    # control-state targets like every other evidence target.
    acquired, passages = _enriched_inputs()
    investigation = build_corpus(
        topic="a placeholder subject",
        interpreted_question="Who held what?",
        geographic_scope=["London"],
        date_earliest=date(1660, 1, 1),
        date_latest=date(1670, 12, 31),
        acquired=acquired,
        passages=passages,
        date_label="1660-1670",
        enrich=_territory_enricher(),
    )
    package_path = tmp_path / "territory.json"
    package_path.write_text(json.dumps(investigation.model_dump(mode="json")), encoding="utf-8")

    corpus = PackageBackedCorpus.load(
        corpus_id="territory-test",
        package_path=package_path,
        title="Territory Test Corpus",
        benchmark_role="control-state search regression",
    )

    # the corpus can resolve the control state directly ...
    control_state = investigation.controlStates[0]
    assert corpus.get_control_state(control_state.id).polity == control_state.polity
    # ... and passage search projects its evidence link instead of crashing
    result = corpus.search_passages(
        PassageSearchRequest(corpusId="territory-test", query="placeholder")
    )
    projected = [link for hit in result.hits for link in hit.evidenceLinks]
    assert any(link.targetType == "controlState" for link in projected)
