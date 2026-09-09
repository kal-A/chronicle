"""WikipediaConnector unit tests.

Every request is served by httpx.MockTransport, so this suite makes zero real
network requests. Test data uses neutral placeholder titles — the connector is
subject-agnostic and never branches on content.
"""

from __future__ import annotations

import hashlib

import httpx
import pytest

from chronicle.acquisition.connectors.base import ConnectorError
from chronicle.acquisition.connectors.wikipedia import WikipediaConnector
from chronicle.acquisition.contracts import DiscoveryQuery, SourceCandidate
from chronicle.contracts.enums import RightsStatus, SourceType


def _connector(handler, **kwargs) -> WikipediaConnector:
    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="https://en.wikipedia.org",
    )
    return WikipediaConnector(client=client, **kwargs)


def _candidate(page_id: str = "42") -> SourceCandidate:
    return SourceCandidate(
        candidateId=f"wikipedia:en:{page_id}",
        connector="wikipedia",
        title="Alpha Article",
        sourceType=SourceType.TERTIARY_REFERENCE,
        fullTextAvailable=True,
        rightsStatus=RightsStatus.LICENSED,
        identifiers={"wikipediaPageId": page_id, "wikipediaKey": "Alpha_Article"},
    )


def test_discover_parses_pages_into_candidates():
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(
            200,
            json={
                "pages": [
                    {
                        "id": 42,
                        "key": "Alpha_Article",
                        "title": "Alpha Article",
                        "excerpt": 'the <span class="searchmatch">Alpha</span> article',
                        "description": "a placeholder subject",
                    },
                    {
                        "id": 77,
                        "key": "Beta_Article",
                        "title": "Beta Article",
                        "excerpt": "beta",
                        "description": None,
                    },
                ]
            },
        )

    connector = _connector(handler)
    candidates = connector.discover(DiscoveryQuery(topic="alpha", terms=["beta"], maxResults=5))

    assert [c.candidateId for c in candidates] == ["wikipedia:en:42", "wikipedia:en:77"]
    first = candidates[0]
    assert first.connector == "wikipedia"
    assert first.title == "Alpha Article"
    assert first.sourceType is SourceType.TERTIARY_REFERENCE
    assert first.rightsStatus is RightsStatus.LICENSED
    assert first.fullTextAvailable is True
    assert first.url == "https://en.wikipedia.org/wiki/Alpha_Article"
    assert first.identifiers == {"wikipediaPageId": "42", "wikipediaKey": "Alpha_Article"}
    assert first.snippet == "the Alpha article"  # HTML stripped
    assert first.retrievalMetadata == {"description": "a placeholder subject"}
    assert candidates[1].snippet == "beta"
    assert candidates[1].retrievalMetadata == {}

    # discovery combined topic + terms and honoured maxResults
    request = captured[0]
    assert request.url.path == "/w/rest.php/v1/search/page"
    assert request.url.params.get("q") == "alpha beta"
    assert request.url.params.get("limit") == "5"


def test_discover_skips_pages_missing_key_or_title():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "pages": [
                    {"id": 1, "key": "", "title": "No Key"},
                    {"id": 2, "title": "No Key Field"},
                    {"id": 3, "key": "Good", "title": "Good Page"},
                ]
            },
        )

    candidates = _connector(handler).discover(DiscoveryQuery(topic="alpha"))
    assert [c.candidateId for c in candidates] == ["wikipedia:en:3"]


def test_discover_empty_results_returns_empty_list():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"pages": []})

    assert _connector(handler).discover(DiscoveryQuery(topic="alpha")) == []


def test_fetch_returns_acquired_source_with_content_hash():
    extract = "Alpha Article is a placeholder used in tests.\n\nIt has two paragraphs."

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/w/api.php"
        assert request.url.params.get("pageids") == "42"
        assert request.url.params.get("explaintext") == "1"
        return httpx.Response(
            200,
            json={"query": {"pages": {"42": {"pageid": 42, "title": "Alpha Article", "extract": extract}}}},
        )

    acquired = _connector(handler).fetch(_candidate("42"))
    assert acquired is not None
    assert acquired.text == extract
    assert acquired.contentType == "text/plain"
    assert acquired.contentSha256 == hashlib.sha256(extract.encode("utf-8")).hexdigest()
    assert acquired.charCount == len(extract)
    assert acquired.candidate.candidateId == "wikipedia:en:42"


def test_fetch_returns_none_when_extract_missing_or_blank():
    def blank_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"query": {"pages": {"42": {"pageid": 42, "extract": "   "}}}})

    def missing_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"query": {"pages": {"42": {"pageid": 42}}}})

    assert _connector(blank_handler).fetch(_candidate("42")) is None
    assert _connector(missing_handler).fetch(_candidate("42")) is None


def test_fetch_requires_a_page_id_identifier():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    bad = SourceCandidate(
        candidateId="wikipedia:en:x",
        connector="wikipedia",
        title="No Id",
        sourceType=SourceType.TERTIARY_REFERENCE,
        fullTextAvailable=True,
        identifiers={},
    )
    with pytest.raises(ConnectorError):
        _connector(handler).fetch(bad)


def test_discover_http_error_becomes_connector_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    with pytest.raises(ConnectorError):
        _connector(handler).discover(DiscoveryQuery(topic="alpha"))
