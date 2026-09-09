"""Doc-registry-seed connector: mine the in-repo source registers as trusted seeds.

The project already hand-curates bibliographies in ``docs/research/*source*.md``
(markdown tables of primary/secondary sources, each with a link, type, and rights).
This connector parses those tables into candidates, gated by keyword overlap with the
query so it only surfaces register entries relevant to the topic — the user's existing
references become high-trust discovery input. Fetch downloads and extracts the linked
document via the shared extractor.

Deterministic and topic-agnostic: it parses whatever registers exist and matches on
the query's own words; it hard-codes no subject.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import httpx

from ...contracts.enums import RightsStatus, SourceType
from ..contracts import AcquiredSource, DiscoveryQuery, SourceCandidate
from ..extract import fetch_url_text
from .base import DEFAULT_TIMEOUT_SECONDS, ConnectorError, SourceConnector

_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_SEPARATOR_RE = re.compile(r"^\s*\|?[\s:-]*\|[\s:|-]*$")
_TOKEN_RE = re.compile(r"[a-z0-9]{4,}")


def _row_cells(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return []
    parts = [cell.strip() for cell in stripped.strip("|").split("|")]
    return parts


def _source_type(cell: str) -> SourceType:
    text = cell.lower()
    if "primary" in text:
        if "personal" in text:
            return SourceType.PRIMARY_PERSONAL
        if "press" in text:
            return SourceType.PRIMARY_PRESS
        return SourceType.PRIMARY_OFFICIAL_DIPLOMATIC
    if "secondary" in text:
        return SourceType.SECONDARY_GENERAL if "general" in text else SourceType.SECONDARY_SPECIALIST
    return SourceType.TERTIARY_REFERENCE


def _rights(cell: str) -> RightsStatus:
    text = cell.lower()
    if "public domain" in text or "public-domain" in text:
        return RightsStatus.PUBLIC_DOMAIN
    if "needs permission" in text or "needs acquisition" in text:
        return RightsStatus.NEEDS_PERMISSION
    if "licensed" in text:
        return RightsStatus.LICENSED
    return RightsStatus.UNKNOWN


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


class DocRegistrySeedConnector(SourceConnector):
    name = "doc-registry-seed"

    def __init__(
        self,
        repo_root: str | Path,
        client: httpx.Client | None = None,
        *,
        register_glob: str = "docs/research/*source*.md",
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._repo_root = Path(repo_root)
        self._register_glob = register_glob
        self.base_url = ""
        super().__init__(client, timeout=timeout)

    def _parse_register(self, path: Path) -> list[dict[str, str]]:
        entries: list[dict[str, str]] = []
        header: list[str] | None = None
        lines = path.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines):
            cells = _row_cells(line)
            if not cells:
                header = None
                continue
            if _SEPARATOR_RE.match(line):
                continue
            # a header row is a table row immediately followed by a separator row
            if header is None:
                nxt = lines[idx + 1] if idx + 1 < len(lines) else ""
                if _SEPARATOR_RE.match(nxt):
                    header = [cell.lower() for cell in cells]
                continue
            row = {header[i]: cells[i] for i in range(min(len(header), len(cells)))}
            entries.append(row)
        return entries

    def _entry_to_candidate(self, row: dict[str, str]) -> SourceCandidate | None:
        source_cell = next((row[key] for key in row if "source" in key), "")
        if not source_cell:
            return None
        links = _LINK_RE.findall(source_cell)
        url = links[0][1] if links else None
        title = _LINK_RE.sub("", source_cell).replace("()", "").strip(" ,;")
        if not title:
            title = links[0][0] if links else "Untitled register entry"
        identifier = next(
            (row[key] for key in row if key in {"id", "id "}), title
        ).strip("` ")
        type_cell = next((row[key] for key in row if "type" in key), "")
        rights_cell = next((row[key] for key in row if "right" in key or "access" in key), "")
        covers_cell = next((row[key] for key in row if "cover" in key), "")

        return SourceCandidate(
            candidateId=f"doc-registry:{identifier}",
            connector=self.name,
            title=title[:300],
            sourceType=_source_type(type_cell),
            fullTextAvailable=bool(url),
            rightsStatus=_rights(rights_cell),
            url=url,
            identifiers={"registerId": identifier},
            snippet=covers_cell or None,
            retrievalMetadata={"covers": covers_cell} if covers_cell else {},
        )

    def discover(self, query: DiscoveryQuery) -> list[SourceCandidate]:
        query_tokens = _tokens(" ".join([query.topic, *query.terms]))
        candidates: list[SourceCandidate] = []
        for path in sorted(self._repo_root.glob(self._register_glob)):
            for row in self._parse_register(path):
                candidate = self._entry_to_candidate(row)
                if candidate is None:
                    continue
                # relevance gate: require overlap with the query's significant words,
                # unless the query has none (then pass everything through)
                haystack = _tokens(f"{candidate.title} {candidate.snippet or ''}")
                if query_tokens and query_tokens.isdisjoint(haystack):
                    continue
                candidates.append(candidate)
        return candidates

    def fetch(self, candidate: SourceCandidate) -> AcquiredSource | None:
        if not candidate.url:
            return None
        try:
            text, content_type = fetch_url_text(self._client, candidate.url)
        except httpx.HTTPError as exc:
            raise ConnectorError(f"doc-registry fetch failed: {exc}") from exc
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
