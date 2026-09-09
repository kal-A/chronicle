"""Internet Archive connector: full-text books and documents (keyless JSON API).

Discovery uses advancedsearch (restricted to ``mediatype:texts``); fetch pulls the
item's plain-text (``*_djvu.txt``) rendition. Rights on the Archive vary widely, so
candidates are marked ``unknown`` rights (honest; human review decides) rather than
assumed public domain. Large texts are length-capped like the Gutenberg connector.
"""

from __future__ import annotations

import hashlib
import re

import httpx

from ...contracts.enums import RightsStatus, SourceType
from ..contracts import AcquiredSource, DiscoveryQuery, SourceCandidate
from .base import DEFAULT_TIMEOUT_SECONDS, ConnectorError, SourceConnector

DEFAULT_MAX_TEXT_CHARS = 400_000
_TOKEN_RE = re.compile(r"[a-z0-9]{4,}")
_VOLUME_RE = re.compile(
    r"\b(vol(?:ume)?|part|pt|no|book)\.?\s*[0-9ivxlc]+\b", re.IGNORECASE
)
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def _significant_tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _work_key(title: str) -> str:
    """Volume-insensitive key so multi-volume editions of one work collapse to one."""
    stripped = _VOLUME_RE.sub(" ", title.lower())
    return _NON_ALNUM_RE.sub(" ", stripped).strip()


class InternetArchiveConnector(SourceConnector):
    name = "internet-archive"
    base_url = "https://archive.org"

    def __init__(
        self,
        client: httpx.Client | None = None,
        *,
        max_text_chars: int = DEFAULT_MAX_TEXT_CHARS,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._max_text_chars = max_text_chars
        super().__init__(client, timeout=timeout)

    def discover(self, query: DiscoveryQuery) -> list[SourceCandidate]:
        # Quote the topic as a phrase (advancedsearch otherwise matches its words
        # loosely across all of full text, returning unrelated newspapers etc.).
        phrase = f'"{query.topic}"'
        extra = " ".join(query.terms).strip()
        search = f"({phrase}{(' ' + extra) if extra else ''}) AND mediatype:texts"
        params = [
            ("q", search),
            ("fl[]", "identifier"),
            ("fl[]", "title"),
            ("fl[]", "creator"),
            ("fl[]", "year"),
            ("rows", str(query.maxResults)),
            ("page", "1"),
            ("output", "json"),
        ]
        try:
            response = self._client.get("/advancedsearch.php", params=params)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise ConnectorError(f"internet archive discovery failed: {exc}") from exc
        except ValueError as exc:
            raise ConnectorError(f"internet archive discovery returned invalid JSON: {exc}") from exc

        docs = (payload.get("response", {}) or {}).get("docs", []) or []
        candidates: list[SourceCandidate] = []
        for doc in docs:
            identifier = doc.get("identifier")
            title = doc.get("title")
            if not identifier or not title:
                continue
            if isinstance(title, list):
                title = title[0] if title else identifier
            creator = doc.get("creator")
            if isinstance(creator, list):
                creator = creator[0] if creator else None
            year = doc.get("year")
            full_text_url = f"{self.base_url}/download/{identifier}/{identifier}_djvu.txt"
            candidates.append(
                SourceCandidate(
                    candidateId=f"internet-archive:{identifier}",
                    connector=self.name,
                    title=str(title),
                    sourceType=SourceType.SECONDARY_GENERAL,
                    fullTextAvailable=True,  # confirmed at fetch; djvu text may still be absent
                    rightsStatus=RightsStatus.UNKNOWN,
                    url=f"{self.base_url}/details/{identifier}",
                    author=str(creator) if creator else None,
                    publicationDate=str(year) if year else None,
                    identifiers={"archiveId": identifier, "fullTextUrl": full_text_url},
                )
            )

        # Relevance gate: keep items whose title shares a significant word with the
        # query. IA's full-text search is broad, so this drops off-topic matches
        # (e.g. unrelated newspapers). If nothing passes, keep the raw results
        # rather than returning an empty set from an otherwise-successful search.
        query_tokens = _significant_tokens(" ".join([query.topic, *query.terms]))
        if query_tokens:
            filtered = [c for c in candidates if _significant_tokens(c.title) & query_tokens]
            candidates = filtered or candidates

        # collapse multi-volume editions of the same work to their first volume
        deduped: list[SourceCandidate] = []
        seen_works: set[str] = set()
        for candidate in candidates:
            key = _work_key(candidate.title)
            if key in seen_works:
                continue
            seen_works.add(key)
            deduped.append(candidate)
        return deduped

    def fetch(self, candidate: SourceCandidate) -> AcquiredSource | None:
        url = candidate.identifiers.get("fullTextUrl")
        if not url:
            return None
        try:
            response = self._client.get(url)
            if response.status_code == 404:
                return None  # no plain-text rendition for this item
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ConnectorError(f"internet archive fetch failed: {exc}") from exc

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
