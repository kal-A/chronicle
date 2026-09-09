"""Wikipedia connector: keyless discovery + plain-text fetch over the public API.

Discovery uses the REST search endpoint (``/w/rest.php/v1/search/page``); fetch
pulls plain-text article bodies via the action API's ``extracts`` prop. Wikipedia
is a tertiary reference (CC BY-SA licensed), useful for orientation and entity
leads — the pipeline should treat it as a starting point that points at primary
and specialist sources, not as a primary source itself.
"""

from __future__ import annotations

import hashlib
import html
import re

import httpx

from ...contracts.enums import RightsStatus, SourceType
from ..contracts import AcquiredSource, DiscoveryQuery, SourceCandidate
from .base import DEFAULT_TIMEOUT_SECONDS, ConnectorError, SourceConnector

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(value: str) -> str:
    return html.unescape(_TAG_RE.sub("", value)).strip()


class WikipediaConnector(SourceConnector):
    name = "wikipedia"

    def __init__(
        self,
        client: httpx.Client | None = None,
        *,
        language: str = "en",
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.language = language
        self.base_url = f"https://{language}.wikipedia.org"
        super().__init__(client, timeout=timeout)

    def discover(self, query: DiscoveryQuery) -> list[SourceCandidate]:
        q = " ".join([query.topic, *query.terms]).strip()
        try:
            response = self._client.get(
                "/w/rest.php/v1/search/page",
                params={"q": q, "limit": query.maxResults},
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise ConnectorError(f"wikipedia discovery failed: {exc}") from exc
        except ValueError as exc:  # malformed JSON
            raise ConnectorError(f"wikipedia discovery returned invalid JSON: {exc}") from exc

        candidates: list[SourceCandidate] = []
        for page in payload.get("pages", []):
            page_id = page.get("id")
            key = page.get("key")
            title = page.get("title")
            if page_id is None or not key or not title:
                continue
            description = page.get("description")
            excerpt = page.get("excerpt")
            candidates.append(
                SourceCandidate(
                    candidateId=f"wikipedia:{self.language}:{page_id}",
                    connector=self.name,
                    title=title,
                    sourceType=SourceType.TERTIARY_REFERENCE,
                    fullTextAvailable=True,
                    rightsStatus=RightsStatus.LICENSED,  # CC BY-SA, not public domain
                    url=f"{self.base_url}/wiki/{key}",
                    language=self.language,
                    identifiers={"wikipediaPageId": str(page_id), "wikipediaKey": key},
                    snippet=_strip_html(excerpt) if excerpt else None,
                    retrievalMetadata={"description": description} if description else {},
                )
            )
        return candidates

    def fetch(self, candidate: SourceCandidate) -> AcquiredSource | None:
        page_id = candidate.identifiers.get("wikipediaPageId")
        if not page_id:
            raise ConnectorError(
                f"candidate {candidate.candidateId!r} is missing a wikipediaPageId identifier"
            )
        try:
            response = self._client.get(
                "/w/api.php",
                params={
                    "action": "query",
                    "format": "json",
                    "prop": "extracts",
                    "explaintext": "1",
                    "redirects": "1",
                    "pageids": page_id,
                },
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise ConnectorError(f"wikipedia fetch failed: {exc}") from exc
        except ValueError as exc:
            raise ConnectorError(f"wikipedia fetch returned invalid JSON: {exc}") from exc

        pages = payload.get("query", {}).get("pages", {})
        page = pages.get(str(page_id)) or pages.get(page_id)
        if not page:
            return None
        extract = (page.get("extract") or "").strip()
        if not extract:
            return None

        content_hash = hashlib.sha256(extract.encode("utf-8")).hexdigest()
        return AcquiredSource(
            candidate=candidate,
            text=extract,
            contentType="text/plain",
            contentSha256=content_hash,
            charCount=len(extract),
        )
