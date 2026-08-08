"""Corpus-layer data contracts (Phase E2): the manifest shape describing a
registered corpus, and the search request/result shapes for
search_passages. All Pydantic, extra="forbid" -- these are read-only
retrieval contracts, mirroring the existing GeneratedInvestigation
contract's strictness discipline.
"""

from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..contracts.enums import EvidenceLinkRole, SourceType
from ..contracts.shared import HistoricalDate

# Bounds enforced on every search request/response -- see search.py for
# where these are actually checked. Named constants, not magic numbers,
# so a future tuning pass has one place to look.
MAX_QUERY_LENGTH = 500
DEFAULT_RESULT_COUNT = 8
MAX_RESULT_COUNT = 20
MAX_EXCERPT_LENGTH = 500
MAX_FILTER_IDS = 20


class PassageDateRole(str, Enum):
    SENT_TIME = "sent_time"
    RECEIVED_TIME = "received_time"
    SOURCE_DATE = "source_date"
    LINKED_EVENT_TIME = "linked_event_time"
    LINKED_ACTOR_AWARENESS_TIME = "linked_actor_awareness_time"


class CorpusManifest(BaseModel):
    """Describes one registered corpus. package_hash and schema_version
    are only known once the package has actually been loaded and
    validated -- see corpus/manifest.py's CorpusRegistry, which computes
    this lazily rather than at import time."""

    model_config = ConfigDict(extra="forbid")

    corpusId: str = Field(min_length=1)
    packagePath: str = Field(min_length=1)
    title: str = Field(min_length=1)
    benchmarkRole: str = Field(min_length=1)
    packageHash: str = Field(min_length=1)
    schemaVersion: str = Field(min_length=1)
    supportedCapabilities: set[str] = Field(default_factory=set)
    knownOmissions: list[str] = Field(default_factory=list)


class DateRangeFilter(BaseModel):
    """A search filter bound, distinct from HistoricalDate (an asserted
    historical fact with precision) -- this is a plain inclusive
    earliest/latest bound on whatever date field a result is being
    matched against. At least one of earliest/latest must be set."""

    model_config = ConfigDict(extra="forbid")

    earliest: date | None = None
    latest: date | None = None

    @model_validator(mode="after")
    def _validate_bounds(self) -> "DateRangeFilter":
        if self.earliest is None and self.latest is None:
            raise ValueError("at least one of earliest/latest must be set")
        if self.earliest is not None and self.latest is not None and self.earliest > self.latest:
            raise ValueError("earliest must not be after latest")
        return self


class PassageSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpusId: str = Field(min_length=1)
    query: str = Field(min_length=1, max_length=MAX_QUERY_LENGTH)
    maxResults: int = Field(default=DEFAULT_RESULT_COUNT, ge=1, le=MAX_RESULT_COUNT)

    sourceIds: list[str] = Field(default_factory=list, max_length=MAX_FILTER_IDS)
    documentIds: list[str] = Field(default_factory=list, max_length=MAX_FILTER_IDS)
    claimIds: list[str] = Field(default_factory=list, max_length=MAX_FILTER_IDS)
    relationshipIds: list[str] = Field(default_factory=list, max_length=MAX_FILTER_IDS)
    entityIds: list[str] = Field(default_factory=list, max_length=MAX_FILTER_IDS)
    eventIds: list[str] = Field(default_factory=list, max_length=MAX_FILTER_IDS)
    dateRange: DateRangeFilter | None = None
    dateRoles: list[PassageDateRole] = Field(default_factory=list, max_length=5)
    evidenceRoles: list[EvidenceLinkRole] = Field(default_factory=list, max_length=3)
    sourceClassifications: list[SourceType] = Field(default_factory=list, max_length=6)

    @field_validator("query")
    @classmethod
    def _query_must_contain_searchable_text(cls, value: str) -> str:
        if not any(character.isalnum() for character in value):
            raise ValueError("query must contain at least one word or number")
        return value

    @model_validator(mode="after")
    def _date_filter_requires_explicit_roles(self) -> "PassageSearchRequest":
        if self.dateRange is not None and not self.dateRoles:
            raise ValueError("dateRoles must be provided when dateRange is set")
        if self.dateRange is None and self.dateRoles:
            raise ValueError("dateRoles require dateRange")
        return self


class EvidenceLinkProjection(BaseModel):
    """Lossless compact mapping from EvidenceLink to its scoped target."""

    model_config = ConfigDict(extra="forbid")

    evidenceLinkId: str = Field(min_length=1)
    targetType: str = Field(min_length=1)
    targetId: str = Field(min_length=1)
    role: str = Field(min_length=1)
    reviewerNote: str | None = None
    reviewStatus: str = Field(min_length=1)
    visibility: str = Field(min_length=1)
    passageId: str = Field(min_length=1)
    documentId: str = Field(min_length=1)
    sourceId: str = Field(min_length=1)


class SearchScoreFactor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    factor: str = Field(min_length=1)
    contribution: float = Field(gt=0)
    matchedTerms: list[str] = Field(default_factory=list)
    matchedTermTotalCount: int = Field(ge=0)
    matchedTermReturnedCount: int = Field(ge=0)
    matchedTermsTruncated: bool
    matchedRecordIds: list[str] = Field(default_factory=list)
    matchedRecordTotalCount: int = Field(ge=0)
    matchedRecordReturnedCount: int = Field(ge=0)
    matchedRecordIdsTruncated: bool


class PassageDateMatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: PassageDateRole
    historicalDate: HistoricalDate
    linkedTargetId: str | None = None


class PassageSearchHit(BaseModel):
    """One ranked result with role-linked dates, evidence, and score factors."""

    model_config = ConfigDict(extra="forbid")

    passageId: str
    documentId: str
    sourceId: str
    excerpt: str
    locator: str
    gapNote: str | None = None
    score: float
    scoreFactors: list[SearchScoreFactor]
    matchedDates: list[PassageDateMatch]
    matchedDateTotalCount: int = Field(ge=0)
    matchedDateReturnedCount: int = Field(ge=0)
    matchedDatesTruncated: bool
    evidenceLinks: list[EvidenceLinkProjection]
    evidenceLinkTotalCount: int = Field(ge=0)
    evidenceLinkReturnedCount: int = Field(ge=0)
    evidenceLinksTruncated: bool
    sourceTitle: str
    sourceType: str
    sourceCurationStatus: str
    documentVisibility: str
    sourceLimitations: str
    documentLimitations: str


class PassageSearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpusId: str
    query: str
    totalMatched: int
    returnedCount: int
    hits: list[PassageSearchHit]
    truncated: bool
