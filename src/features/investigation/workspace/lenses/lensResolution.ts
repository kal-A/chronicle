import type { GeneratedInvestigation } from '../../model/generatedInvestigation'
import type { InvestigationLens } from '../../model/experiencePlan'
import type { Scene } from '../../model/schema'

/**
 * Packages without an experiencePlan (the empty-content fixture, and any
 * future package that hasn't been given one yet) still need a working
 * workspace — this synthesizes a single "show everything in this scene"
 * lens from the Scene's own data, the same content MapView/TimelineView
 * already show today. It is never persisted or treated as generated
 * content; it exists only so the workspace degrades gracefully.
 */
export const OVERVIEW_LENS_ID = 'lens-overview'

export function resolveLenses(
  investigation: GeneratedInvestigation,
  scene: Scene,
): InvestigationLens[] {
  if (investigation.experiencePlan) {
    return investigation.experiencePlan.lenses
  }
  return [synthesizeOverviewLens(scene)]
}

function synthesizeOverviewLens(scene: Scene): InvestigationLens {
  const sortedEvents = [...scene.events].sort((a, b) =>
    a.eventTime.earliest.localeCompare(b.eventTime.earliest),
  )
  return {
    id: OVERVIEW_LENS_ID,
    label: 'Overview',
    purpose: 'Show everything curated for this scene.',
    historicalQuestion: 'What is in this scene?',
    visualizationType: 'map',
    applicableTimeRange: scene.dateRange,
    visibleLocations: scene.placeIds,
    visibleEvents: sortedEvents.map((event) => event.id),
    visibleRelationships: scene.relationships.map((relationship) => relationship.id),
    visibleRegions: [],
    legend: [],
    evidenceReferences: [],
    limitations: [],
    textFallback:
      sortedEvents.length > 0
        ? sortedEvents.map((event, index) => `${index + 1}. ${event.title}`)
        : ['No events are curated for this scene yet.'],
  }
}

/** Intersects a lens's package-level visible-id lists with what the CURRENT
 * scene actually contains — a lens is investigation-wide, but the workspace
 * only ever renders one scene at a time. */
export interface SceneScopedLens {
  placeIds: Set<string>
  eventIds: Set<string>
  relationshipIds: Set<string>
}

export function sceneScopeLens(lens: InvestigationLens, scene: Scene): SceneScopedLens {
  const scenePlaceIds = new Set(scene.placeIds)
  const sceneEventIds = new Set(scene.events.map((event) => event.id))
  const sceneRelationshipIds = new Set(scene.relationships.map((relationship) => relationship.id))

  return {
    placeIds: new Set(lens.visibleLocations.filter((id) => scenePlaceIds.has(id))),
    eventIds: new Set(lens.visibleEvents.filter((id) => sceneEventIds.has(id))),
    relationshipIds: new Set(
      lens.visibleRelationships.filter((id) => sceneRelationshipIds.has(id)),
    ),
  }
}
