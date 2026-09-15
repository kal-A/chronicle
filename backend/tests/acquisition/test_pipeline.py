"""Discovery aggregation, fetch cache, and pipeline orchestration.

Uses an in-test FakeConnector (no HTTP) so these exercise the wiring, not the
network. Connector-level HTTP behaviour is covered in connectors/test_*.py.
"""

from __future__ import annotations

from datetime import date

import pytest

from chronicle.acquisition.connectors.base import ConnectorError, SourceConnector
from chronicle.acquisition.contracts import AcquiredSource, DiscoveryQuery, SourceCandidate
from chronicle.acquisition.discovery import discover_sources
from chronicle.acquisition.fetch_cache import FetchCache
from chronicle.acquisition.pipeline import AcquisitionPipeline
from chronicle.contracts.enums import PackageStatus, RightsStatus, SourceType


class FakeConnector(SourceConnector):
    """A network-free connector with canned discovery + fetch, and call counters."""

    def __init__(self, name, candidates, bodies, *, fail_discovery=False, raise_on=None):
        self.name = name  # instance attr shadows the class attr; no client created
        self._candidates = candidates
        self._bodies = bodies
        self._fail_discovery = fail_discovery
        self._raise_on = set(raise_on or ())
        self.fetch_calls: list[str] = []

    def discover(self, query: DiscoveryQuery) -> list[SourceCandidate]:
        if self._fail_discovery:
            raise ConnectorError("boom")
        return list(self._candidates)

    def fetch(self, candidate: SourceCandidate) -> AcquiredSource | None:
        self.fetch_calls.append(candidate.candidateId)
        if candidate.candidateId in self._raise_on:
            raise ConnectorError(f"fetch failed: 403 Forbidden for {candidate.candidateId}")
        body = self._bodies.get(candidate.candidateId)
        if body is None:
            return None
        return AcquiredSource(
            candidate=candidate,
            text=body,
            contentType="text/plain",
            contentSha256=f"h-{candidate.candidateId}",
            charCount=len(body),
        )


def _candidate(candidate_id, connector="fake", full_text=True) -> SourceCandidate:
    return SourceCandidate(
        candidateId=candidate_id,
        connector=connector,
        title=f"Title {candidate_id}",
        sourceType=SourceType.TERTIARY_REFERENCE,
        fullTextAvailable=full_text,
        rightsStatus=RightsStatus.LICENSED,
    )


# --- discovery ---------------------------------------------------------------

def test_discovery_merges_gates_and_dedupes():
    a = FakeConnector("a", [_candidate("x", "a"), _candidate("noft", "a", full_text=False)], {})
    b = FakeConnector("b", [_candidate("x", "a"), _candidate("y", "b")], {})  # "x" duplicate
    result = discover_sources([a, b], DiscoveryQuery(topic="t"))
    assert [c.candidateId for c in result.candidates] == ["x", "y"]  # ingestable, deduped, ordered
    assert [c.candidateId for c in result.references] == ["noft"]  # kept as a reference, not dropped
    assert result.errors == {}


def test_discovery_records_connector_errors_without_aborting():
    good = FakeConnector("good", [_candidate("x", "good")], {})
    broken = FakeConnector("broken", [], {}, fail_discovery=True)
    result = discover_sources([broken, good], DiscoveryQuery(topic="t"))
    assert [c.candidateId for c in result.candidates] == ["x"]
    assert "broken" in result.errors


def test_discovery_respects_max_total():
    a = FakeConnector("a", [_candidate("x", "a"), _candidate("y", "a"), _candidate("z", "a")], {})
    result = discover_sources([a], DiscoveryQuery(topic="t"), max_total=2)
    assert [c.candidateId for c in result.candidates] == ["x", "y"]


# --- fetch cache -------------------------------------------------------------

def test_fetch_cache_avoids_second_network_fetch(tmp_path):
    cand = _candidate("x", "fake")
    connector = FakeConnector("fake", [cand], {"x": "body text"})
    cache = FetchCache(tmp_path)

    first = cache.get_or_fetch(connector, cand)
    second = cache.get_or_fetch(connector, cand)

    assert first is not None and second is not None
    assert first.text == second.text == "body text"
    assert connector.fetch_calls == ["x"]  # fetched once; second served from cache


def test_fetch_cache_does_not_cache_unavailable_sources(tmp_path):
    cand = _candidate("x", "fake")
    connector = FakeConnector("fake", [cand], {})  # no body -> fetch returns None
    cache = FetchCache(tmp_path)

    assert cache.get_or_fetch(connector, cand) is None
    assert cache.get_or_fetch(connector, cand) is None
    assert connector.fetch_calls == ["x", "x"]  # retried, not cached


# --- pipeline ----------------------------------------------------------------

def test_pipeline_builds_a_corpus_end_to_end(tmp_path):
    candidates = [_candidate("x", "fake"), _candidate("y", "fake")]
    bodies = {"x": "Alpha body about signals. " * 30, "y": "Beta body about registries. " * 30}
    connector = FakeConnector("fake", candidates, bodies)
    pipeline = AcquisitionPipeline([connector], FetchCache(tmp_path))

    result = pipeline.run(
        topic="a placeholder subject",
        interpreted_question="What happened?",
        geographic_scope=["Somewhere"],
        date_earliest=date(1800, 1, 1),
        date_latest=date(1850, 12, 31),
        max_sources=8,
    )

    assert result.discovered == 2
    assert result.acquired == 2
    assert result.passages >= 2
    assert result.discovery_errors == {}
    assert result.investigation.status is PackageStatus.PARTIAL
    assert len(result.investigation.sources) == 2
    assert len(result.investigation.passages) == result.passages


def test_pipeline_accepts_a_bc_scope_via_signed_years(tmp_path):
    # ADR-005: a BC investigation is initiated through the pipeline with signed
    # years instead of CE calendar dates; the built scope is BC and it still builds.
    candidates = [_candidate("x", "fake")]
    bodies = {"x": "Alpha body about the siege. " * 30}
    connector = FakeConnector("fake", candidates, bodies)
    pipeline = AcquisitionPipeline([connector], FetchCache(tmp_path))

    result = pipeline.run(
        topic="a placeholder subject",
        interpreted_question="What happened?",
        geographic_scope=["Somewhere"],
        year_earliest=-218,  # 219 BC
        year_latest=-201,  # 202 BC
        max_sources=8,
    )

    date_range = result.investigation.scope.dateRange
    assert date_range.earliestYear == -218 and date_range.latestYear == -201
    assert date_range.earliest is None and date_range.latest is None
    assert result.investigation.status is PackageStatus.PARTIAL


def test_pipeline_skips_a_source_that_fails_to_fetch(tmp_path):
    # A single flaky/forbidden source (e.g. Internet Archive returning 403) must
    # not fail the whole acquisition: the pipeline skips it, records the error,
    # and builds a corpus from the sources that did succeed. Reproduces the live
    # walkthrough bug where one 403 turned the build endpoint into a 500.
    candidates = [_candidate("good", "fake"), _candidate("bad", "fake")]
    bodies = {"good": "Reliable body about the event. " * 30}
    connector = FakeConnector("fake", candidates, bodies, raise_on={"bad"})
    pipeline = AcquisitionPipeline([connector], FetchCache(tmp_path))

    result = pipeline.run(
        topic="a placeholder subject",
        interpreted_question="What happened?",
        geographic_scope=["Somewhere"],
        date_earliest=date(1800, 1, 1),
        date_latest=date(1850, 12, 31),
        max_sources=8,
    )

    assert result.discovered == 2
    assert result.acquired == 1  # the good source survived; the bad one was skipped
    assert result.passages >= 1
    assert "bad" in result.fetch_errors  # the failure is recorded, not raised
    assert len(result.investigation.sources) == 1


def test_pipeline_requires_at_least_one_connector(tmp_path):
    with pytest.raises(ValueError):
        AcquisitionPipeline([], FetchCache(tmp_path))


def test_pipeline_enriches_with_events_when_extractor_and_geocoder_injected(tmp_path):
    # Opt-in enrichment: inject an event extractor + a period-aware geocoder and
    # the same topic-agnostic path now yields located events + a timeline, while
    # the default pipeline (no enrichment) stays evidence-only.
    from chronicle.acquisition.assembly import assemble_enrichment
    from chronicle.acquisition.extraction import ExtractedEvent, ExtractedEvents
    from chronicle.acquisition.geocoding import GeoResolution
    from chronicle.ai.models.deterministic import DeterministicModelProvider
    from chronicle.contracts.enums import LocationPrecision
    from chronicle.contracts.shared import Coordinates

    class _StubGeocoder:
        def resolve(self, name, period):
            return GeoResolution(
                canonicalName=name, nameAtTime=name,
                coordinates=Coordinates(lat=51.5, lng=-0.12),
                precision=LocationPrecision.CITY, providerName="stub",
                provenanceUrl="https://example/x",
            )

    class _StubExtractor(DeterministicModelProvider):
        """Cites the first built passage so the event is grounded in a real id."""
        def generate_structured(self, *args, **kwargs):
            # the user_prompt carries the built passages; grab the first id from it
            import json, re
            prompt = kwargs.get("user_prompt") or args[1]
            first_id = re.search(r'"id":"(psg-[^"]+)"', prompt).group(1)
            self.enqueue_value(ExtractedEvents(events=[
                ExtractedEvent(title="An event", placeName="Placeholdertown", year=1820, passageIds=[first_id]),
            ]))
            return super().generate_structured(*args, **kwargs)

    candidates = [_candidate("x", "fake")]
    bodies = {"x": "Alpha body about the placeholder event. " * 30}
    connector = FakeConnector("fake", candidates, bodies)
    pipeline = AcquisitionPipeline(
        [connector], FetchCache(tmp_path),
        extractor=_StubExtractor(), geocoder=_StubGeocoder(),
    )

    result = pipeline.run(
        topic="a placeholder subject",
        interpreted_question="What happened?",
        geographic_scope=["Somewhere"],
        date_earliest=date(1800, 1, 1),
        date_latest=date(1850, 12, 31),
        max_sources=8,
    )

    assert result.events == 1
    assert result.located_places == 1
    assert len(result.investigation.events) == 1
    assert "timeline" not in result.investigation.interactionSpec.omittedCapabilities
