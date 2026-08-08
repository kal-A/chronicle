"""Bounded projection of stored map context without inferred geography."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ...contracts.shared import Coordinates, HistoricalDate, MapBounds, MapDefaultView
from ...corpus.bounds import CollectionBudget
from ...corpus.errors import UnknownRecordError
from ...corpus.protocol import InvestigationCorpus
from .contracts import ToolExecutionContext
from .registry import ToolDefinition

MAX_MAP_FILTER_IDS = 20
MAX_MAP_RESULTS = 20


class GetMapContextInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpusId: str = Field(min_length=1)
    placeIds: list[str] = Field(default_factory=list, max_length=MAX_MAP_FILTER_IDS)
    eventIds: list[str] = Field(default_factory=list, max_length=MAX_MAP_FILTER_IDS)
    sceneIds: list[str] = Field(default_factory=list, max_length=MAX_MAP_FILTER_IDS)
    maxResults: int | None = Field(default=None, ge=1, le=MAX_MAP_RESULTS)


class MapPlacePeriodEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    periodLabel: str
    nameAtTime: str
    controllingPolity: str
    precision: str


class MapPlaceEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    placeId: str
    canonicalName: str
    coordinates: Coordinates | None
    periodRecords: list[MapPlacePeriodEntry]
    periodRecordTotalCount: int = Field(ge=0)
    periodRecordReturnedCount: int = Field(ge=0)
    periodRecordsTruncated: bool
    linkedEventIds: list[str]
    linkedEventTotalCount: int = Field(ge=0)
    linkedEventReturnedCount: int = Field(ge=0)
    linkedEventsTruncated: bool


class MapMarkerEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    placeId: str
    precision: str


class MapSceneEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mapSceneId: str
    sceneId: str
    mapAssetId: str
    periodLabel: str
    rightsStatus: str
    periodFitDecision: str
    georeferencingPrecision: str
    georeferencingNote: str
    imagePath: str
    sourceCitation: str
    attribution: str
    license: str
    bounds: MapBounds
    defaultView: MapDefaultView
    markers: list[MapMarkerEntry]
    markerTotalCount: int = Field(ge=0)
    markerReturnedCount: int = Field(ge=0)
    markersTruncated: bool


class GetMapContextOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpusId: str
    places: list[MapPlaceEntry]
    mapScenes: list[MapSceneEntry]
    representedPeriod: HistoricalDate | None
    representedPeriodLabel: str | None
    geographicLimitations: list[str]
    geographicLimitationTotalCount: int = Field(ge=0)
    geographicLimitationReturnedCount: int = Field(ge=0)
    geographicLimitationsTruncated: bool
    unavailableHistoricalBoundaries: list[str]
    unavailableBoundaryTotalCount: int = Field(ge=0)
    unavailableBoundaryReturnedCount: int = Field(ge=0)
    unavailableHistoricalBoundariesTruncated: bool
    totalCount: int = Field(ge=0)
    returnedCount: int = Field(ge=0)
    truncated: bool


def _get_map_context(
    tool_input: GetMapContextInput,
    context: ToolExecutionContext,
    corpus: InvestigationCorpus,
) -> GetMapContextOutput:
    investigation = corpus.get_investigation()
    scene_ids_all = {s.id for s in investigation.scenes}
    for scene_id in tool_input.sceneIds:
        if scene_id not in scene_ids_all:
            raise UnknownRecordError(f'Corpus "{corpus.corpus_id}" has no Scene "{scene_id}"')

    no_filters = not (tool_input.placeIds or tool_input.eventIds or tool_input.sceneIds)

    if no_filters:
        target_place_ids = {e.id for e in investigation.entities if e.entityType == "place"}
    else:
        target_place_ids = set()
        for place_id in tool_input.placeIds:
            place = corpus.get_place(place_id)
            target_place_ids.add(place.id)
        for event_id in tool_input.eventIds:
            target_place_ids.add(corpus.get_event(event_id).placeId)
        for scene in investigation.scenes:
            if scene.id in tool_input.sceneIds:
                target_place_ids.update(scene.placeIds)

    places_by_id = {e.id: e for e in investigation.entities if e.entityType == "place"}
    place_entries: list[MapPlaceEntry] = []
    for place_id in sorted(target_place_ids):
        place = places_by_id.get(place_id)
        if place is None:
            continue
        linked_event_ids = sorted(e.id for e in corpus.get_events_at_place(place_id))
        place_entries.append(
            MapPlaceEntry(
                placeId=place.id,
                canonicalName=place.canonicalName,
                coordinates=place.coordinates,
                periodRecords=[
                    MapPlacePeriodEntry(
                        periodLabel=pr.periodLabel,
                        nameAtTime=pr.nameAtTime,
                        controllingPolity=pr.controllingPolity,
                        precision=pr.precision.value,
                    )
                    for pr in place.periodRecords
                ],
                periodRecordTotalCount=len(place.periodRecords),
                periodRecordReturnedCount=len(place.periodRecords),
                periodRecordsTruncated=False,
                linkedEventIds=linked_event_ids,
                linkedEventTotalCount=len(linked_event_ids),
                linkedEventReturnedCount=len(linked_event_ids),
                linkedEventsTruncated=False,
            )
        )

    if tool_input.sceneIds:
        relevant_scenes = [s for s in investigation.mapScenes if s.sceneId in tool_input.sceneIds]
    elif no_filters:
        relevant_scenes = list(investigation.mapScenes)
    else:
        relevant_scenes = [
            s for s in investigation.mapScenes if any(m.placeId in target_place_ids for m in s.markers)
        ]

    map_assets_by_id = {a.id: a for a in investigation.mapAssets}
    scene_entries: list[MapSceneEntry] = []
    for scene in sorted(relevant_scenes, key=lambda item: (item.sceneId, item.id)):
        asset = map_assets_by_id.get(scene.mapAssetId)
        if asset is None:
            continue
        scene_entries.append(
            MapSceneEntry(
                mapSceneId=scene.id,
                sceneId=scene.sceneId,
                mapAssetId=scene.mapAssetId,
                periodLabel=asset.periodLabel,
                rightsStatus=asset.rightsStatus.value,
                periodFitDecision=asset.periodFitDecision.value,
                georeferencingPrecision=asset.georeferencingPrecision.value,
                georeferencingNote=asset.georeferencingNote,
                imagePath=asset.imagePath,
                sourceCitation=asset.sourceCitation,
                attribution=asset.attribution,
                license=asset.license,
                bounds=asset.bounds,
                defaultView=asset.defaultView,
                markers=[
                    MapMarkerEntry(placeId=marker.placeId, precision=marker.precision.value)
                    for marker in scene.markers
                ],
                markerTotalCount=len(scene.markers),
                markerReturnedCount=len(scene.markers),
                markersTruncated=False,
            )
        )

    represented_period: HistoricalDate | None = None
    represented_period_label: str | None = None
    geographic_limitations: list[str] = []
    unavailable_boundaries: list[str] = []
    if investigation.experiencePlan is not None:
        scope = investigation.experiencePlan.workspace.initialMapScope
        represented_period = scope.representedPeriod
        represented_period_label = scope.representedPeriod.label
        geographic_limitations = list(scope.geographicLimitations)
        unavailable_boundaries = list(scope.unavailableHistoricalBoundaries)

    place_candidates: list[tuple[str, MapPlaceEntry | MapSceneEntry]] = [
        ("place", entry) for entry in place_entries
    ]
    scene_candidates: list[tuple[str, MapPlaceEntry | MapSceneEntry]] = [
        ("scene", entry) for entry in scene_entries
    ]
    candidates = (
        scene_candidates + place_candidates
        if tool_input.sceneIds
        else place_candidates + scene_candidates
    )
    requested_limit = tool_input.maxResults or context.maximumResults
    effective_limit = min(requested_limit, context.maximumResults, MAX_MAP_RESULTS)
    returned_candidates = candidates[:effective_limit]
    nested_budget = CollectionBudget(effective_limit)
    # Safety limitations are more important than convenience lists: reserve
    # budget for them first so a bounded response never hides known caveats.
    returned_geographic_limitations = nested_budget.take(geographic_limitations)
    returned_unavailable_boundaries = nested_budget.take(unavailable_boundaries)
    returned_places: list[MapPlaceEntry] = []
    returned_scenes: list[MapSceneEntry] = []
    for kind, entry in returned_candidates:
        if kind == "place":
            period_records = nested_budget.take(entry.periodRecords)
            linked_event_ids = nested_budget.take(entry.linkedEventIds)
            returned_places.append(
                entry.model_copy(
                    update={
                        "periodRecords": period_records,
                        "periodRecordReturnedCount": len(period_records),
                        "periodRecordsTruncated": len(period_records)
                        < entry.periodRecordTotalCount,
                        "linkedEventIds": linked_event_ids,
                        "linkedEventReturnedCount": len(linked_event_ids),
                        "linkedEventsTruncated": len(linked_event_ids)
                        < entry.linkedEventTotalCount,
                    }
                )
            )
        else:
            markers = nested_budget.take(entry.markers)
            returned_scenes.append(
                entry.model_copy(
                    update={
                        "markers": markers,
                        "markerReturnedCount": len(markers),
                        "markersTruncated": len(markers) < entry.markerTotalCount,
                    }
                )
            )

    return GetMapContextOutput(
        corpusId=tool_input.corpusId,
        places=returned_places,
        mapScenes=returned_scenes,
        representedPeriod=represented_period,
        representedPeriodLabel=represented_period_label,
        geographicLimitations=returned_geographic_limitations,
        geographicLimitationTotalCount=len(geographic_limitations),
        geographicLimitationReturnedCount=len(returned_geographic_limitations),
        geographicLimitationsTruncated=(
            len(returned_geographic_limitations) < len(geographic_limitations)
        ),
        unavailableHistoricalBoundaries=returned_unavailable_boundaries,
        unavailableBoundaryTotalCount=len(unavailable_boundaries),
        unavailableBoundaryReturnedCount=len(returned_unavailable_boundaries),
        unavailableHistoricalBoundariesTruncated=(
            len(returned_unavailable_boundaries) < len(unavailable_boundaries)
        ),
        totalCount=len(candidates),
        returnedCount=len(returned_candidates),
        truncated=len(returned_candidates) < len(candidates),
    )


GET_MAP_CONTEXT_TOOL = ToolDefinition(
    name="get_map_context",
    version="e2-get-map-context-v2",
    description=(
        "Return a bounded projection of stored places and map scenes, preserving exact coordinates, "
        "period records, marker precision, georeferencing notes, and represented-period limitations. "
        "It never invents coordinates, routes, borders, regions, or precision."
    ),
    input_model=GetMapContextInput,
    output_model=GetMapContextOutput,
    required_capabilities=frozenset(),
    max_result_limit=MAX_MAP_RESULTS,
    execute=_get_map_context,
    use_when=(
        "Use to retrieve stored places, event locations, or historical-map scene context for "
        "the current corpus."
    ),
    avoid_when=(
        "Avoid when you would need to infer missing coordinates, routes, borders, political "
        "control, or finer location precision."
    ),
    output_summary=(
        "Bounded place and scene projections with exact stored coordinates, marker precision, "
        "period validity, and limitations."
    ),
)
