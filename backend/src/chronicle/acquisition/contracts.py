"""Acquisition-layer data contracts (P1).

These are the intermediate, pipeline-internal shapes passed between acquisition
stages: a ``DiscoveryQuery`` in, ``SourceCandidate`` list out of discovery,
``AcquiredSource`` out of fetching, ``ExtractedPassage`` list out of chunking.
They are deliberately distinct from ``contracts/generated_investigation.py``'s
``Source``/``Passage`` (the finished, review-bearing package contract);
``corpus_builder`` maps these into that contract at the end of the pipeline.

They reuse the existing ``SourceType``/``RightsStatus``/``CurationStatus`` enums so
the acquisition lifecycle lines up with the human source-register lifecycle in
``docs/research/*source-register*.md`` (identified -> acquired -> passages-extracted).

Topic-agnostic by contract (see ``tests/ai/tools/test_no_topic_branching_guard.py``):
nothing here names or branches on a subject; every field is data carried through.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..contracts.enums import RightsStatus, SourceType

MAX_TOPIC_LENGTH = 500
MAX_TERMS = 20
DEFAULT_MAX_RESULTS = 5
MAX_RESULTS_CEILING = 50


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DiscoveryQuery(BaseModel):
    """A scope-resolved request handed to every connector's ``discover``.

    ``terms`` are additional keywords the scope stage extracted; connectors may
    combine them with ``topic`` however their API allows. Year bounds are plain
    inclusive filters (not asserted historical dates) and are advisory — a
    connector without date filtering simply ignores them.
    """

    model_config = ConfigDict(extra="forbid")

    topic: str = Field(min_length=1, max_length=MAX_TOPIC_LENGTH)
    terms: list[str] = Field(default_factory=list, max_length=MAX_TERMS)
    maxResults: int = Field(default=DEFAULT_MAX_RESULTS, ge=1, le=MAX_RESULTS_CEILING)
    languages: list[str] = Field(default_factory=lambda: ["en"], min_length=1, max_length=5)
    earliestYear: int | None = None
    latestYear: int | None = None


class SourceCandidate(BaseModel):
    """One discovered-but-not-yet-fetched source.

    ``fullTextAvailable`` is the deterministic evidence gate: a candidate whose
    full text cannot be retrieved is metadata only, and metadata/snippets are
    never evidence (AGENTS.md). ``snippet`` exists for ranking/display only and
    must never be treated as evidence text.
    """

    model_config = ConfigDict(extra="forbid")

    candidateId: str = Field(min_length=1)
    connector: str = Field(min_length=1)
    title: str = Field(min_length=1)
    sourceType: SourceType
    fullTextAvailable: bool
    rightsStatus: RightsStatus = RightsStatus.UNKNOWN
    url: str | None = None
    author: str | None = None
    publicationDate: str | None = None
    language: str | None = None
    identifiers: dict[str, str] = Field(default_factory=dict)
    relevance: float | None = None
    snippet: str | None = None
    retrievalMetadata: dict[str, Any] = Field(default_factory=dict)


class AcquiredSource(BaseModel):
    """A candidate whose full text has been fetched and extracted to plain text.

    ``contentSha256`` is the content-addressed cache key over ``text`` — identical
    text acquired twice hashes identically, so re-runs are cheap and reproducible.
    """

    model_config = ConfigDict(extra="forbid")

    candidate: SourceCandidate
    text: str = Field(min_length=1)
    contentType: str = Field(min_length=1)
    contentSha256: str = Field(min_length=1)
    charCount: int = Field(ge=1)
    retrievedAt: datetime = Field(default_factory=_utcnow)


class ExtractedPassage(BaseModel):
    """One chunk of an acquired source, with an honest character-offset locator.

    Locators are exact and verifiable (character offsets into the acquired text),
    not invented page/edition citations — edition-level citation remains a later,
    human-review concern per the source-register discipline.
    """

    model_config = ConfigDict(extra="forbid")

    passageId: str = Field(min_length=1)
    sourceCandidateId: str = Field(min_length=1)
    ordinal: int = Field(ge=0)
    text: str = Field(min_length=1)
    charStart: int = Field(ge=0)
    charEnd: int = Field(ge=0)
    locator: str = Field(min_length=1)
