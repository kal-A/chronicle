"""The InvestigationExperiencePlan contract — Phase D (map-first workspace),
mirrors src/features/investigation/model/experiencePlan.ts field for field,
in the same order. Optional and additive on GeneratedInvestigation: existing
packages remain valid without one. See docs/decisions/ADR-002-map-first-
workspace.md.

`InvestigationTimelinePlan` is deliberately NOT part of this D0.2 contract
slice — see experiencePlan.ts's module docstring for why.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .enums import EvidenceDepth, FocusKind, LensVisualization, PanelTab
from .shared import Coordinates, HistoricalDate


class GeographicBounds(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topLeft: Coordinates
    topRight: Coordinates
    bottomRight: Coordinates
    bottomLeft: Coordinates


class Viewport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    center: Coordinates
    zoom: float


class HistoricalRegionReference(BaseModel):
    """Free-standing generated label — Chronicle has no Region entity type
    yet (only person/place), so this is not cross-reference validated."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)


class MapScope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bounds: GeographicBounds
    focusRegions: list[HistoricalRegionReference] = Field(default_factory=list)
    contextRegions: list[HistoricalRegionReference] = Field(default_factory=list)
    initialViewport: Viewport
    minimumZoom: float
    maximumZoom: float
    geographicRationale: str = Field(min_length=1)
    representedPeriod: HistoricalDate
    unavailableHistoricalBoundaries: list[str] = Field(default_factory=list)
    geographicLimitations: list[str] = Field(default_factory=list)


class LegendItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    description: str = Field(min_length=1)


class InvestigationLens(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    historicalQuestion: str = Field(min_length=1)
    visualizationType: LensVisualization
    applicableTimeRange: HistoricalDate
    visibleLocations: list[str] = Field(default_factory=list)
    visibleEvents: list[str] = Field(default_factory=list)
    visibleRelationships: list[str] = Field(default_factory=list)
    visibleRegions: list[str] = Field(default_factory=list)
    legend: list[LegendItem] = Field(default_factory=list)
    evidenceReferences: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    # REQUIRED accessible equivalent — map-first-workspace-instructions.md §17.1.
    textFallback: list[str] = Field(min_length=1)


class StorySequence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    stepIds: list[str] = Field(min_length=1)
    defaultLensId: str = Field(min_length=1)
    defaultTimeRange: HistoricalDate


class SystemPath(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    lensId: str = Field(min_length=1)
    nodeIds: list[str] = Field(min_length=1)
    relationshipIds: list[str] = Field(default_factory=list)
    summary: str = Field(min_length=1)
    limitations: list[str] = Field(default_factory=list)


class PerspectiveComparison(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    entityIds: list[str] = Field(min_length=2)
    claimIds: list[str] = Field(default_factory=list)
    summary: str = Field(min_length=1)


class ContextualPrompt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    targetLensId: str | None = Field(default=None, min_length=1)


class ContextualPromptSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    appliesTo: str = Field(min_length=1)
    prompts: list[ContextualPrompt] = Field(min_length=1)


class SelectionTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    kind: FocusKind
    recordId: str = Field(min_length=1)
    label: str = Field(min_length=1)


class InvestigationLimitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    affectedLensIds: list[str] = Field(default_factory=list)


class _Workspace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    initialMapScope: MapScope
    initialLensId: str = Field(min_length=1)
    initialTimeRange: HistoricalDate
    initialPanelTab: PanelTab
    defaultPanelWidth: int = Field(ge=320)


class _Opening(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)
    scopeSummary: str = Field(min_length=1)
    leadAnswer: str = Field(min_length=1)
    evidenceCoverageSummary: str = Field(min_length=1)


class _Inspector(BaseModel):
    model_config = ConfigDict(extra="forbid")

    defaultEvidenceDepth: EvidenceDepth
    exposeGenerationReport: bool
    exposeRejectedSources: bool


class InvestigationExperiencePlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    opening: _Opening
    workspace: _Workspace
    lenses: list[InvestigationLens] = Field(min_length=1)
    storySequences: list[StorySequence] = Field(default_factory=list)
    systemPaths: list[SystemPath] = Field(default_factory=list)
    perspectiveComparisons: list[PerspectiveComparison] = Field(default_factory=list)
    contextualPrompts: list[ContextualPromptSet] = Field(default_factory=list)
    recommendedSelections: list[SelectionTarget] = Field(default_factory=list)
    limitations: list[InvestigationLimitation] = Field(default_factory=list)
    inspector: _Inspector
