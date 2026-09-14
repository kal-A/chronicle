"""The GeneratedInvestigation package contract.

Mirrors src/features/investigation/model/generatedInvestigation.ts field for
field, in the same order. Cross-record invariants are NOT expressed here as
Pydantic validators (the TS side doesn't either — Zod's per-object .refine()
can't see across collections) — see validation.py for the ported
validate_generated_investigation(), which runs after a successful parse here,
exactly like the TS validateGeneratedInvestigation() runs after
GeneratedInvestigationSchema.parse().
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .enums import (
    ApprovalStatus,
    Awareness,
    ControlStateKind,
    CurationStatus,
    DirectOrInferred,
    EvidenceClassification,
    EvidenceLinkRole,
    EvidenceTargetType,
    Facet,
    FindingImportance,
    FindingRecordType,
    FocusKind,
    GenerationOutcome,
    GeometryType,
    GeoreferencingPrecision,
    LedgerConclusion,
    LocationPrecision,
    MapAssetPeriodFitDecision,
    PackageStatus,
    RequestedDepth,
    RequestType,
    ReviewStatus,
    RightsStatus,
    StageStatus,
    VerificationCheckStatus,
    Visibility,
)
from .experience_plan import InvestigationExperiencePlan
from .shared import (
    Document,
    Entity,
    HistoricalDate,
    HistoricalMapLayer,
    NarrativeBlock,
    Passage,
    Source,
)

SUPPORTED_GENERATED_INVESTIGATION_VERSION = "1.0.0"


class InvestigationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    rawInput: str = Field(min_length=1)
    requestType: RequestType
    requestedDepth: RequestedDepth
    createdAt: datetime


class InvestigationScope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    interpretedQuestion: str = Field(min_length=1)
    dateRange: HistoricalDate
    geographicScope: list[str] = Field(min_length=1)
    themes: list[str] = Field(default_factory=list)
    inclusions: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    approvalStatus: ApprovalStatus


class GeneratedEvidenceLink(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    targetType: EvidenceTargetType
    targetId: str = Field(min_length=1)
    passageId: str = Field(min_length=1)
    role: EvidenceLinkRole
    reviewerNote: str | None = Field(default=None, min_length=1)


class GeneratedClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    directOrInferred: DirectOrInferred
    reviewStatus: ReviewStatus
    visibility: Visibility
    evidenceLinkIds: list[str] = Field(min_length=1)


class GeneratedRelationship(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    relationshipType: str = Field(min_length=1)
    fromId: str = Field(min_length=1)
    toId: str = Field(min_length=1)
    directOrInferred: DirectOrInferred
    evidenceClassification: EvidenceClassification
    reviewStatus: ReviewStatus
    visibility: Visibility
    evidenceLinkIds: list[str] = Field(default_factory=list)


class GeneratedKnownAtTime(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    personOrInstitutionId: str = Field(min_length=1)
    fact: str = Field(min_length=1)
    asOfDate: HistoricalDate
    awareness: Awareness
    reviewStatus: ReviewStatus
    visibility: Visibility
    evidenceLinkIds: list[str] = Field(min_length=1)


class GeneratedEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    placeId: str = Field(min_length=1)
    eventTime: HistoricalDate
    evidenceLinkIds: list[str] = Field(min_length=1)
    relatedRecordIds: list[str]
    reviewStatus: ReviewStatus
    visibility: Visibility


class FindingReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    recordType: FindingRecordType
    recordId: str = Field(min_length=1)
    label: str = Field(min_length=1)
    importance: FindingImportance


class ClaimEvidenceLedger(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    claimId: str = Field(min_length=1)
    evidenceLinkIds: list[str] = Field(min_length=1)
    conclusion: LedgerConclusion
    limitations: list[str] = Field(default_factory=list)


class TimelineEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    eventId: str = Field(min_length=1)
    order: int = Field(ge=0)


class HistoricalMapAsset(HistoricalMapLayer):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    rightsStatus: RightsStatus
    periodFitDecision: MapAssetPeriodFitDecision
    georeferencingPrecision: GeoreferencingPrecision


class MapMarker(BaseModel):
    model_config = ConfigDict(extra="forbid")

    placeId: str = Field(min_length=1)
    precision: LocationPrecision


class MapScene(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    sceneId: str = Field(min_length=1)
    mapAssetId: str = Field(min_length=1)
    markers: list[MapMarker] = Field(default_factory=list)


class ControlState(BaseModel):
    """A passage-grounded, time-valid assertion that a polity controlled /
    influenced / contested a region over an interval (ADR-004 addendum). Carries
    NO geometry — only a ``geometryRef`` into ``territoryGeometries`` — so the
    map's polygons only ever come from a sourced dataset, never the LLM. Additive
    and reviewable like every other generated record; existing packages omit it."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    polity: str = Field(min_length=1)
    kind: ControlStateKind
    validFrom: HistoricalDate
    validTo: HistoricalDate
    geometryRef: str = Field(min_length=1)
    precision: LocationPrecision
    evidenceLinkIds: list[str] = Field(min_length=1)
    reviewStatus: ReviewStatus
    visibility: Visibility


class TerritoryGeometry(BaseModel):
    """A boundary polygon resolved from a sourced historical-boundary dataset,
    referenced by ``ControlState.geometryRef``. ``attestedYear`` records the
    snapshot year the polygon actually came from (BC = negative) so rendering can
    say "as of ~Y"; ``sourceDataset``/``license`` keep it auditable. Coordinates
    are a GeoJSON coordinate array — its deep shape is guaranteed by the
    deterministic resolver that emits it, not re-validated here."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    type: GeometryType
    coordinates: list = Field(min_length=1)
    sourceDataset: str = Field(min_length=1)
    attestedYear: int
    license: str = Field(min_length=1)
    polity: str | None = Field(default=None, min_length=1)


class InvestigationScene(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    curationStatus: CurationStatus
    dateRange: HistoricalDate
    placeIds: list[str] = Field(min_length=1)
    entityIds: list[str] = Field(default_factory=list)
    sourceIds: list[str] = Field(default_factory=list)
    documentIds: list[str] = Field(default_factory=list)
    passageIds: list[str] = Field(default_factory=list)
    eventIds: list[str] = Field(default_factory=list)
    claimIds: list[str] = Field(default_factory=list)
    relationshipIds: list[str] = Field(default_factory=list)
    knowledgeStateIds: list[str] = Field(default_factory=list)
    narrativeBlockIds: list[str] = Field(min_length=1)
    mapSceneId: str | None = Field(default=None, min_length=1)


class InteractionSpecification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    defaultSceneId: str = Field(min_length=1)
    focusKinds: list[FocusKind] = Field(min_length=1)
    enabledFacets: list[Facet] = Field(default_factory=list)
    omittedCapabilities: list[str] = Field(default_factory=list)


class StageOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    status: StageStatus


class VerificationCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    status: VerificationCheckStatus
    message: str = Field(min_length=1)


class GenerationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: GenerationOutcome
    stages: list[StageOutcome] = Field(default_factory=list)
    omissions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    verificationChecks: list[VerificationCheck] = Field(default_factory=list)


class ExtensionRecord(BaseModel):
    """Open-shape placeholder for decisions/communications/perspectives/
    conflicts/uncertainties/researchGaps — mirrors ExtensionRecordSchema's
    z.object({id}).passthrough()."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(min_length=1)


class Presentation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    synthesis: list[NarrativeBlock] = Field(min_length=1)
    findings: list[FindingReference] = Field(default_factory=list)
    sceneIds: list[str] = Field(min_length=1)
    perspectiveIds: list[str] = Field(default_factory=list)


class GeneratedInvestigation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schemaVersion: str = Field(min_length=1)
    packageId: str = Field(min_length=1)
    packageRevision: int = Field(gt=0)
    generatedAt: datetime
    request: InvestigationRequest
    scope: InvestigationScope
    status: PackageStatus
    presentation: Presentation
    entities: list[Entity] = Field(default_factory=list)
    events: list[GeneratedEvent] = Field(default_factory=list)
    decisions: list[ExtensionRecord] = Field(default_factory=list)
    communications: list[ExtensionRecord] = Field(default_factory=list)
    knowledgeStates: list[GeneratedKnownAtTime] = Field(default_factory=list)
    claims: list[GeneratedClaim] = Field(default_factory=list)
    relationships: list[GeneratedRelationship] = Field(default_factory=list)
    perspectives: list[ExtensionRecord] = Field(default_factory=list)
    conflicts: list[ExtensionRecord] = Field(default_factory=list)
    uncertainties: list[ExtensionRecord] = Field(default_factory=list)
    researchGaps: list[ExtensionRecord] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    documents: list[Document] = Field(default_factory=list)
    passages: list[Passage] = Field(default_factory=list)
    evidenceLinks: list[GeneratedEvidenceLink] = Field(default_factory=list)
    claimLedgers: list[ClaimEvidenceLedger] = Field(default_factory=list)
    timeline: list[TimelineEntry] = Field(default_factory=list)
    mapAssets: list[HistoricalMapAsset] = Field(default_factory=list)
    mapScenes: list[MapScene] = Field(default_factory=list)
    # ADR-004 addendum, optional/additive — the time-indexed territory layer.
    # Existing packages remain valid without these (both default to empty).
    controlStates: list[ControlState] = Field(default_factory=list)
    territoryGeometries: list[TerritoryGeometry] = Field(default_factory=list)
    scenes: list[InvestigationScene] = Field(min_length=1)
    interactionSpec: InteractionSpecification
    generationReport: GenerationReport
    # Phase D, optional/additive (docs/decisions/ADR-002-map-first-workspace.md)
    # -- existing packages remain valid without one.
    experiencePlan: InvestigationExperiencePlan | None = None
