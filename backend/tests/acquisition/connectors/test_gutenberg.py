"""GutenbergConnector: Gutendex discovery + plain-text fetch (mocked HTTP)."""

from __future__ import annotations

import httpx

from chronicle.acquisition.connectors.gutenberg import GutenbergConnector
from chronicle.acquisition.contracts import DiscoveryQuery, SourceCandidate
from chronicle.contracts.enums import RightsStatus, SourceType

_RESULTS = {
    "results": [
        {
            "id": 11,
            "title": "Alpha Book",
            "authors": [{"name": "Doe, Jane"}],
            "languages": ["en"],
            "formats": {
                "text/plain; charset=utf-8": "https://www.gutenberg.org/files/11/11-0.txt",
                "text/html": "https://www.gutenberg.org/ebooks/11",
            },
        },
        {
            "id": 12,
            "title": "Beta Book",
            "authors": [],
            "languages": ["en"],
            "formats": {"application/epub+zip": "https://www.gutenberg.org/ebooks/12.epub"},
        },
    ]
}


def _connector(handler, **kwargs) -> GutenbergConnector:
    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://gutendex.com")
    return GutenbergConnector(client=client, **kwargs)


def test_discover_maps_books_and_flags_missing_full_text():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/books"
        return httpx.Response(200, json=_RESULTS)

    candidates = _connector(handler).discover(DiscoveryQuery(topic="alpha", maxResults=5))
    assert [c.candidateId for c in candidates] == ["gutenberg:11", "gutenberg:12"]

    first = candidates[0]
    assert first.title == "Alpha Book"
    assert first.author == "Doe, Jane"
    assert first.sourceType is SourceType.SECONDARY_GENERAL
    assert first.rightsStatus is RightsStatus.PUBLIC_DOMAIN
    assert first.fullTextAvailable is True
    assert first.identifiers["plainTextUrl"].endswith("11-0.txt")

    assert candidates[1].fullTextAvailable is False  # only an epub format


def test_discover_respects_max_results():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_RESULTS)

    candidates = _connector(handler).discover(DiscoveryQuery(topic="alpha", maxResults=1))
    assert [c.candidateId for c in candidates] == ["gutenberg:11"]


def test_fetch_returns_plain_text_and_truncates():
    body = "word " * 1000  # 5000 chars

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("11-0.txt")
        return httpx.Response(200, text=body, headers={"content-type": "text/plain"})

    candidate = SourceCandidate(
        candidateId="gutenberg:11",
        connector="gutenberg",
        title="Alpha Book",
        sourceType=SourceType.SECONDARY_GENERAL,
        fullTextAvailable=True,
        rightsStatus=RightsStatus.PUBLIC_DOMAIN,
        identifiers={"plainTextUrl": "https://www.gutenberg.org/files/11/11-0.txt"},
    )
    acquired = _connector(handler, max_text_chars=1000).fetch(candidate)
    assert acquired is not None
    assert acquired.charCount == 1000  # truncated
    assert acquired.contentType == "text/plain"
