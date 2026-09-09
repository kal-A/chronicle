"""CuratedResourceConnector + reputable-source registry."""

from __future__ import annotations

import httpx

from chronicle.acquisition.connectors.curated_resource import CuratedResourceConnector
from chronicle.acquisition.contracts import DiscoveryQuery
from chronicle.acquisition.reputable_sources import (
    DEFAULT_REPUTABLE_SOURCES,
    ReputableSource,
    relevant_sources,
)
from chronicle.contracts.enums import RightsStatus, SourceType


def test_civil_war_digital_is_registered_as_reference_only():
    entry = next(s for s in DEFAULT_REPUTABLE_SOURCES if s.id == "civil-war-digital")
    assert entry.homepage == "https://civilwardigital.com"
    assert entry.fullTextFree is False  # commercial: pointer only, never ingested
    assert entry.rights is RightsStatus.NEEDS_PERMISSION


def test_relevant_sources_matches_on_keywords():
    matched = relevant_sources({"civil", "war"})
    assert any(s.id == "civil-war-digital" for s in matched)
    assert relevant_sources({"photosynthesis"}) == []


def test_discover_surfaces_reference_only_resource_as_non_ingestable():
    connector = CuratedResourceConnector()
    candidates = connector.discover(DiscoveryQuery(topic="American Civil War official records"))
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.candidateId == "curated-resource:civil-war-digital"
    assert candidate.fullTextAvailable is False  # gate keeps it out of evidence
    assert candidate.rightsStatus is RightsStatus.NEEDS_PERMISSION
    assert candidate.url == "https://civilwardigital.com"
    assert candidate.retrievalMetadata["referenceOnly"] is True


def test_discover_returns_nothing_for_unrelated_topics():
    connector = CuratedResourceConnector()
    assert connector.discover(DiscoveryQuery(topic="congress of vienna diplomacy")) == []


def test_fetch_refuses_reference_only_resources():
    connector = CuratedResourceConnector()
    candidate = connector.discover(DiscoveryQuery(topic="civil war"))[0]
    assert connector.fetch(candidate) is None  # never ingest licensed/paid content


def test_free_registry_entry_is_ingestable_and_fetchable():
    free = ReputableSource(
        id="free-archive",
        name="Free Archive",
        homepage="https://free.example.org",
        description="An open archive about alpha topics.",
        keywords=("alpha", "open archive"),
        sourceType=SourceType.SECONDARY_GENERAL,
        rights=RightsStatus.PUBLIC_DOMAIN,
        fullTextFree=True,
        search_url_template="https://free.example.org/search?q={query}",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<p>Alpha open archive body.</p>", headers={"content-type": "text/html"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    connector = CuratedResourceConnector(client=client, sources=[free])

    candidates = connector.discover(DiscoveryQuery(topic="alpha"))
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.fullTextAvailable is True
    assert candidate.url == "https://free.example.org/search?q=alpha"

    acquired = connector.fetch(candidate)
    assert acquired is not None
    assert "Alpha open archive body." in acquired.text
