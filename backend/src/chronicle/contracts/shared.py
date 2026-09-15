"""Primitives shared across the package contract.

Mirrors src/features/investigation/model/schema.ts's "Shared value types",
"Entities", and "Source -> Document -> Passage" sections, plus the
HistoricalMapLayer base shape from its "Scene" section (the package-level
HistoricalMapAsset in generated_investigation.py extends this the same way
generatedInvestigation.ts's HistoricalMapAssetSchema extends
HistoricalMapLayerSchema).
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .enums import (
    CurationStatus,
    DatePrecision,
    LocationPrecision,
    ReviewStatus,
    RightsStatus,
    SourceType,
    Visibility,
)


class HistoricalDate(BaseModel):
    """A historically honest date interval, era-capable (ADR-005).

    The canonical, always-derivable ordering key is a *signed astronomical year*
    (``earliestYear``/``latestYear``: 1 = 1 CE, 0 = 1 BC, -1 = 2 BC, …). The
    calendar dates (``earliest``/``latest``) are optional CE-only refinement that
    add day/month precision; they must be omitted for BC. Order and interval math
    use ``lower_key``/``upper_key`` so no consumer re-derives the cross-era key.
    """

    model_config = ConfigDict(extra="forbid")

    precision: DatePrecision
    earliest: date | None = None
    latest: date | None = None
    earliestYear: int | None = None
    latestYear: int | None = None
    label: str | None = None

    @model_validator(mode="after")
    def _bounds_derivable(self) -> "HistoricalDate":
        # ADR-005 invariant 1: each bound must be derivable from a year or a date.
        if self.earliest is None and self.earliestYear is None:
            raise ValueError("HistoricalDate needs earliest or earliestYear")
        if self.latest is None and self.latestYear is None:
            raise ValueError("HistoricalDate needs latest or latestYear")
        return self

    @model_validator(mode="after")
    def _year_and_date_agree(self) -> "HistoricalDate":
        # ADR-005 invariant 2: a calendar date is CE-only and, when a year field
        # is also given, they must name the same year.
        if self.earliest is not None and self.earliestYear is not None:
            if self.earliest.year != self.earliestYear:
                raise ValueError("earliest.year must equal earliestYear")
        if self.latest is not None and self.latestYear is not None:
            if self.latest.year != self.latestYear:
                raise ValueError("latest.year must equal latestYear")
        return self

    @property
    def lower_key(self) -> tuple[int, int]:
        """Total-order key for the lower bound: (signed year, day-of-year)."""

        if self.earliest is not None:
            return (self.earliest.year, self.earliest.timetuple().tm_yday)
        return (self.earliestYear, 1)  # type: ignore[return-value]

    @property
    def upper_key(self) -> tuple[int, int]:
        """Total-order key for the upper bound: (signed year, day-of-year)."""

        if self.latest is not None:
            return (self.latest.year, self.latest.timetuple().tm_yday)
        return (self.latestYear, 366)  # type: ignore[return-value]

    @model_validator(mode="after")
    def _earliest_not_after_latest(self) -> "HistoricalDate":
        if self.lower_key > self.upper_key:
            raise ValueError("earliest must not be after latest")
        return self

    @model_validator(mode="after")
    def _exact_requires_equal_bounds(self) -> "HistoricalDate":
        # Compare the raw bounds, not the day-padded interval keys, so a year-only
        # exact BC date (earliestYear == latestYear, no calendar date) is accepted.
        if self.precision == DatePrecision.EXACT and (
            self.earliest != self.latest or self.earliestYear != self.latestYear
        ):
            raise ValueError("an exact HistoricalDate must have earliest === latest")
        return self


class PlacePeriodRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    periodLabel: str = Field(min_length=1)
    nameAtTime: str = Field(min_length=1)
    controllingPolity: str = Field(min_length=1)
    precision: LocationPrecision


class Coordinates(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lat: float
    lng: float


class PersonEntity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    entityType: Literal["person"]
    canonicalName: str = Field(min_length=1)
    alsoKnownAs: list[str] = Field(default_factory=list)
    description: str = Field(min_length=1)
    reviewStatus: ReviewStatus


class PlaceEntity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    entityType: Literal["place"]
    canonicalName: str = Field(min_length=1)
    periodRecords: list[PlacePeriodRecord] = Field(min_length=1)
    reviewStatus: ReviewStatus
    coordinates: Coordinates | None = None


Entity = Annotated[Union[PersonEntity, PlaceEntity], Field(discriminator="entityType")]


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    sourceType: SourceType
    authorOrOrigin: str = Field(min_length=1)
    dateOfSource: HistoricalDate
    originalLanguage: str = Field(min_length=1)
    rightsStatus: RightsStatus
    curationStatus: CurationStatus
    knownLimitations: str = Field(min_length=1)
    linkOrLocation: str = Field(min_length=1)


class Document(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    sourceId: str = Field(min_length=1)
    editionCitation: str = Field(min_length=1)
    translationCredit: str | None = Field(default=None, min_length=1)
    visibility: Visibility
    knownLimitations: str = Field(min_length=1)


class Passage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    documentId: str = Field(min_length=1)
    excerpt: str = Field(min_length=1)
    locator: str = Field(min_length=1)
    sentTime: HistoricalDate | None = None
    receivedTime: HistoricalDate | None = None
    gapNote: str | None = Field(default=None, min_length=1)


class NarrativeBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    order: int = Field(ge=0)
    text: str = Field(min_length=1)
    isMaterialAssertion: bool
    referencedRecordIds: list[str] = Field(default_factory=list)
    relatedEventId: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _material_assertion_needs_references(self) -> "NarrativeBlock":
        if self.isMaterialAssertion and len(self.referencedRecordIds) == 0:
            raise ValueError(
                "a material NarrativeBlock must reference at least one "
                "Claim/Relationship/KnownAtTime record"
            )
        return self


class MapBounds(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topLeft: Coordinates
    topRight: Coordinates
    bottomRight: Coordinates
    bottomLeft: Coordinates


class MapDefaultView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    center: Coordinates
    zoom: float


class HistoricalMapLayer(BaseModel):
    """Base shape only — generated_investigation.HistoricalMapAsset extends it."""

    model_config = ConfigDict(extra="forbid")

    imagePath: str = Field(min_length=1)
    bounds: MapBounds
    defaultView: MapDefaultView
    periodLabel: str = Field(min_length=1)
    sourceCitation: str = Field(min_length=1)
    attribution: str = Field(min_length=1)
    license: str = Field(min_length=1)
    georeferencingNote: str = Field(min_length=1)
