"""Project Gutenberg connector (via the keyless Gutendex API): classic full texts.

Discovery queries Gutendex; fetch pulls the plain-text edition directly. Gutenberg
holds public-domain classic and period books — useful primary/secondary reading —
so candidates are marked public-domain. Full texts can be very large, so fetch caps
the retrieved length; the cap is recorded as a known limitation on the source.
"""

from __future__ import annotations

import hashlib

import httpx

from ...contracts.enums import RightsStatus, SourceType
from ..contracts import AcquiredSource, DiscoveryQuery, SourceCandidate
from .base import ConnectorError, SourceConnector

DEFAULT_MAX_TEXT_CHARS = 400_000
_PLAINTEXT_KEYS = ("text/plain; charset=utf-8", "text/plain; charset=us-ascii", "text/plain")


def _plaintext_url(formats: dict) -> str | None:
    for key in _PLAINTEXT_KEYS:
        url = formats.get(key)
        if url and not url.endswith(".zip"):
            return url
    for key, url in formats.items():
        if key.startswith("text/plain") and isinstance(url, str) and not url.endswith(".zip"):
            return url
    return None


class GutenbergConnector(SourceConnector):
    name = "gutenberg"
    base_url = "https://gutendex.com"

    def __init__(
        self,
        client: httpx.Client | None = None,
        *,
        max_text_chars: int = DEFAULT_MAX_TEXT_CHARS,
        timeout: float = 60.0,  # gutendex can be slow; give it more room than the default
    ) -> None:
        self._max_text_chars = max_text_chars
        super().__init__(client, timeout=timeout)

    def discover(self, query: DiscoveryQuery) -> list[SourceCandidate]:
        search = " ".join([query.topic, *query.terms]).strip()
        try:
            response = self._client.get(
                "/books",
                params={"search": search, "languages": ",".join(query.languages)},
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise ConnectorError(f"gutenberg discovery failed: {exc}") from exc
        except ValueError as exc:
            raise ConnectorError(f"gutenberg discovery returned invalid JSON: {exc}") from exc

        candidates: list[SourceCandidate] = []
        for book in payload.get("results", [])[: query.maxResults]:
            book_id = book.get("id")
            title = book.get("title")
            if book_id is None or not title:
                continue
            plaintext = _plaintext_url(book.get("formats", {}) or {})
            authors = book.get("authors") or []
            author = authors[0].get("name") if authors and isinstance(authors[0], dict) else None
            languages = book.get("languages") or []
            candidates.append(
                SourceCandidate(
                    candidateId=f"gutenberg:{book_id}",
                    connector=self.name,
                    title=title,
                    sourceType=SourceType.SECONDARY_GENERAL,
                    fullTextAvailable=plaintext is not None,
                    rightsStatus=RightsStatus.PUBLIC_DOMAIN,
                    url=plaintext or f"https://www.gutenberg.org/ebooks/{book_id}",
                    author=author,
                    language=languages[0] if languages else None,
                    identifiers={"gutenbergId": str(book_id), **({"plainTextUrl": plaintext} if plaintext else {})},
                )
            )
        return candidates

    def fetch(self, candidate: SourceCandidate) -> AcquiredSource | None:
        url = candidate.identifiers.get("plainTextUrl") or candidate.url
        if not url:
            return None
        try:
            response = self._client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ConnectorError(f"gutenberg fetch failed: {exc}") from exc

        text = response.text.strip()
        if not text:
            return None
        if len(text) > self._max_text_chars:
            text = text[: self._max_text_chars]
        return AcquiredSource(
            candidate=candidate,
            text=text,
            contentType="text/plain",
            contentSha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            charCount=len(text),
        )
