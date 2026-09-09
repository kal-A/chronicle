"""Curated-resource connector: surface reputable registry resources for a query.

Reads ``reputable_sources.DEFAULT_REPUTABLE_SOURCES`` (or an injected catalog) and
turns query-relevant entries into candidates. Free entries (``fullTextFree=True``)
are real acquisition candidates (``fullTextAvailable=True``), fetched via the shared
extractor; reference-only entries are emitted with ``fullTextAvailable=False`` so the
discovery gate preserves them as references rather than ingesting paid/licensed
content as evidence.
"""

from __future__ import annotations

import hashlib
from urllib.parse import quote_plus

import httpx

from ..contracts import AcquiredSource, DiscoveryQuery, SourceCandidate
from ..extract import fetch_url_text
from ..reputable_sources import DEFAULT_REPUTABLE_SOURCES, ReputableSource, relevant_sources, tokens
from .base import DEFAULT_TIMEOUT_SECONDS, ConnectorError, SourceConnector


class CuratedResourceConnector(SourceConnector):
    name = "curated-resource"

    def __init__(
        self,
        client: httpx.Client | None = None,
        *,
        sources: list[ReputableSource] | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._sources = sources if sources is not None else DEFAULT_REPUTABLE_SOURCES
        self.base_url = ""
        super().__init__(client, timeout=timeout)

    def discover(self, query: DiscoveryQuery) -> list[SourceCandidate]:
        query_tokens = tokens(" ".join([query.topic, *query.terms]))
        candidates: list[SourceCandidate] = []
        for source in relevant_sources(query_tokens, self._sources):
            if source.search_url_template and source.fullTextFree:
                url = source.search_url_template.format(query=quote_plus(query.topic))
            else:
                url = source.homepage
            candidates.append(
                SourceCandidate(
                    candidateId=f"curated-resource:{source.id}",
                    connector=self.name,
                    title=source.name,
                    sourceType=source.sourceType,
                    fullTextAvailable=source.fullTextFree,
                    rightsStatus=source.rights,
                    url=url,
                    snippet=source.description[:300],
                    identifiers={"resourceId": source.id, "homepage": source.homepage},
                    retrievalMetadata={"referenceOnly": not source.fullTextFree},
                )
            )
        return candidates

    def fetch(self, candidate: SourceCandidate) -> AcquiredSource | None:
        # Reference-only resources are never ingested (licensed/paid content).
        if not candidate.fullTextAvailable or not candidate.url:
            return None
        try:
            text, content_type = fetch_url_text(self._client, candidate.url)
        except httpx.HTTPError as exc:
            raise ConnectorError(f"curated-resource fetch failed: {exc}") from exc
        text = text.strip()
        if not text:
            return None
        return AcquiredSource(
            candidate=candidate,
            text=text,
            contentType=content_type or "text/plain",
            contentSha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            charCount=len(text),
        )
