"""InternetArchiveConnector: advancedsearch discovery + djvu text fetch (mocked)."""

from __future__ import annotations

import httpx

from chronicle.acquisition.connectors.internet_archive import InternetArchiveConnector
from chronicle.acquisition.contracts import DiscoveryQuery, SourceCandidate
from chronicle.contracts.enums import RightsStatus, SourceType


def _connector(handler, **kwargs) -> InternetArchiveConnector:
    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://archive.org")
    return InternetArchiveConnector(client=client, **kwargs)


_DOCS = {
    "response": {
        "docs": [
            {"identifier": "alpha1", "title": "Alpha Text", "creator": "Doe, J.", "year": "1850"},
            {"identifier": "beta2", "title": "Beta Text"},
        ]
    }
}


def test_discover_maps_text_items():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/advancedsearch.php"
        assert "mediatype:texts" in request.url.params.get("q", "")
        return httpx.Response(200, json=_DOCS)

    # topic "text" appears in both titles, so both survive the relevance gate
    candidates = _connector(handler).discover(DiscoveryQuery(topic="text", maxResults=5))
    assert [c.candidateId for c in candidates] == ["internet-archive:alpha1", "internet-archive:beta2"]
    first = candidates[0]
    assert first.title == "Alpha Text"
    assert first.author == "Doe, J."
    assert first.publicationDate == "1850"
    assert first.sourceType is SourceType.SECONDARY_GENERAL
    assert first.rightsStatus is RightsStatus.UNKNOWN
    assert first.identifiers["fullTextUrl"].endswith("alpha1_djvu.txt")


def test_discover_filters_out_low_relevance_titles():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_DOCS)

    # only "Alpha Text" shares a word with the query; "Beta Text" is dropped
    candidates = _connector(handler).discover(DiscoveryQuery(topic="alpha", maxResults=5))
    assert [c.candidateId for c in candidates] == ["internet-archive:alpha1"]


def test_fetch_returns_text_and_handles_missing_rendition():
    def ok_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="Full book text. " * 100, headers={"content-type": "text/plain"})

    def missing_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="Not found")

    candidate = SourceCandidate(
        candidateId="internet-archive:alpha1",
        connector="internet-archive",
        title="Alpha Text",
        sourceType=SourceType.SECONDARY_GENERAL,
        fullTextAvailable=True,
        rightsStatus=RightsStatus.UNKNOWN,
        identifiers={"fullTextUrl": "https://archive.org/download/alpha1/alpha1_djvu.txt"},
    )

    acquired = _connector(ok_handler).fetch(candidate)
    assert acquired is not None
    assert acquired.text.startswith("Full book text.")

    assert _connector(missing_handler).fetch(candidate) is None  # 404 -> unavailable, not an error


def test_fetch_truncates_large_texts():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="x" * 5000, headers={"content-type": "text/plain"})

    candidate = SourceCandidate(
        candidateId="internet-archive:alpha1",
        connector="internet-archive",
        title="Alpha Text",
        sourceType=SourceType.SECONDARY_GENERAL,
        fullTextAvailable=True,
        rightsStatus=RightsStatus.UNKNOWN,
        identifiers={"fullTextUrl": "https://archive.org/download/alpha1/alpha1_djvu.txt"},
    )
    acquired = _connector(handler, max_text_chars=1000).fetch(candidate)
    assert acquired is not None and acquired.charCount == 1000
