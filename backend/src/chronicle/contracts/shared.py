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
    model_config = ConfigDict(extra="forbid")

    precision: DatePrecision
    earliest: date
    latest: date
    label: str | None = None

    @model_validator(mode="after")
    def _earliest_not_after_latest(self) -> "HistoricalDate":
        if self.earliest > self.latest:
            raise ValueError("earliest must not be after latest")
        return self

    @model_validator(mode="after")
    def _exact_requires_equal_bounds(self) -> "HistoricalDate":
        if self.precision == DatePrecision.EXACT and self.earliest != self.latest:
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
