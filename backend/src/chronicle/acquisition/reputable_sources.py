"""Curated registry of reputable research resources.

A data-driven, extensible list of trusted resources the system knows about. Two
kinds live here:

- **Free, retrievable** resources (``fullTextFree=True``, optionally with a
  ``search_url_template``) — surfaced as real acquisition candidates the pipeline
  fetches and ingests as evidence.
- **Reference-only** pointers (``fullTextFree=False``) — reputable places a
  researcher should consult, but whose content is paywalled/licensed/for-sale and
  therefore must NOT be ingested as free evidence. They are surfaced as references,
  not corpus sources, honouring the free-source and rights rules.

Adding "similar reputable websites" means appending entries here — no code change.
Topic-agnostic: entries are matched to a query by their own keywords, never by any
branch on a subject.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..contracts.enums import RightsStatus, SourceType

_TOKEN_RE = re.compile(r"[a-z0-9]{3,}")


def tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


@dataclass(frozen=True)
class ReputableSource:
    id: str
    name: str
    homepage: str
    description: str
    keywords: tuple[str, ...]
    sourceType: SourceType
    rights: RightsStatus
    fullTextFree: bool
    #: e.g. "https://example.org/search?q={query}"; None => surface the homepage
    search_url_template: str | None = None

    def match_text(self) -> str:
        return " ".join([self.name, self.description, *self.keywords])


DEFAULT_REPUTABLE_SOURCES: list[ReputableSource] = [
    ReputableSource(
        id="civil-war-digital",
        name="Civil War Digital",
        homepage="https://civilwardigital.com",
        description=(
            "Commercial compiler of digitized U.S. Civil War materials — the Official Records "
            "of the War of the Rebellion (Army and Navy), the Photographic History of the Civil "
            "War, the Report of the Joint Committee on the Conduct of the War, and campaign "
            "collections. Content is sold, not freely downloadable, so it is a reference/pointer "
            "only. The underlying Official Records are public domain and freely acquirable via "
            "Internet Archive and Wikisource."
        ),
        keywords=(
            "civil war",
            "american civil war",
            "war of the rebellion",
            "official records",
            "union army",
            "confederate",
            "naval records",
            "reconstruction",
        ),
        sourceType=SourceType.TERTIARY_REFERENCE,
        rights=RightsStatus.NEEDS_PERMISSION,
        fullTextFree=False,
    ),
]


def relevant_sources(
    query_tokens: set[str],
    sources: list[ReputableSource] | None = None,
) -> list[ReputableSource]:
    """Registry entries whose keywords/name/description overlap the query."""
    catalog = sources if sources is not None else DEFAULT_REPUTABLE_SOURCES
    if not query_tokens:
        return []
    return [source for source in catalog if query_tokens & tokens(source.match_text())]
