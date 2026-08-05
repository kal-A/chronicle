import { z } from 'zod'
import { HistoricalDateSchema } from './schema'

/**
 * The InvestigationExperiencePlan contract — Phase D (map-first workspace),
 * docs/product/map-first-workspace-instructions.md §18, docs/decisions/
 * ADR-002-map-first-workspace.md. Optional and additive on
 * GeneratedInvestigation: existing packages (blank-cheque, concert-of-europe)
 * remain valid without one. Every ID field here is generated content,
 * cross-reference-validated the same way every other package reference is
 * (see validateExperiencePlanReferences below and its call site in
 * generatedInvestigation.ts) — never client-computed from raw scene data.
 *
 * `InvestigationTimelinePlan` (play/pause/speed UI config) is deliberately
 * NOT part of this D0.2 contract slice — it's UI configuration the D0.3
 * workspace-shell sub-plan will define once the actual timeline component
 * exists to consume it, not something this contract-only slice needs to
 * invent ahead of that. `workspace.initialTimeRange` covers what D0.2 needs.
 */

const CoordinatesSchema = z.object({ lat: z.number(), lng: z.number() })

const GeographicBoundsSchema = z.object({
  topLeft: CoordinatesSchema,
  topRight: CoordinatesSchema,
  bottomRight: CoordinatesSchema,
  bottomLeft: CoordinatesSchema,
})

const ViewportSchema = z.object({
  center: CoordinatesSchema,
  zoom: z.number(),
})

/**
 * Regions are free-standing, generated labels (e.g. "Central Europe"), not
 * yet a canonical package record type — Chronicle has no `Region` entity
 * today (only `person`/`place`, schema.ts's EntitySchema). Not cross-
 * reference validated against anything for that reason; a real Region
 * entity type is a future contract change, not part of this slice.
 */
const HistoricalRegionReferenceSchema = z.object({
  id: z.string().min(1),
  label: z.string().min(1),
})

export const MapScopeSchema = z.object({
  bounds: GeographicBoundsSchema,
  focusRegions: z.array(HistoricalRegionReferenceSchema),
  contextRegions: z.array(HistoricalRegionReferenceSchema),
  initialViewport: ViewportSchema,
  minimumZoom: z.number(),
  maximumZoom: z.number(),
  geographicRationale: z.string().min(1),
  representedPeriod: HistoricalDateSchema,
  unavailableHistoricalBoundaries: z.array(z.string().min(1)),
  geographicLimitations: z.array(z.string().min(1)),
})
export type MapScope = z.infer<typeof MapScopeSchema>

const LegendItemSchema = z.object({
  id: z.string().min(1),
  label: z.string().min(1),
  description: z.string().min(1),
})

export const PanelTabSchema = z.enum(['ask', 'explore', 'evidence', 'sources'])
export type PanelTab = z.infer<typeof PanelTabSchema>

/**
 * Which canvas the workspace renders while this lens is active — the map
 * (Sequence/Positions/Knowledge/Sources/Uncertainty ask "where/when/who,"
 * answered spatially) or the labelled systems graph (Systems asks "how are
 * these connected," answered as a path, per map-first-workspace-
 * instructions.md §13). Required, not inferred from lens id/content, so an
 * authored lens is never ambiguous about how it wants to be shown.
 */
export const LensVisualizationSchema = z.enum(['map', 'graph'])
export type LensVisualization = z.infer<typeof LensVisualizationSchema>

export const InvestigationLensSchema = z.object({
  id: z.string().min(1),
  label: z.string().min(1),
  purpose: z.string().min(1),
  historicalQuestion: z.string().min(1),
  visualizationType: LensVisualizationSchema,
  applicableTimeRange: HistoricalDateSchema,
  visibleLocations: z.array(z.string().min(1)),
  visibleEvents: z.array(z.string().min(1)),
  visibleRelationships: z.array(z.string().min(1)),
  /** See HistoricalRegionReferenceSchema's comment — not cross-referenced. */
  visibleRegions: z.array(z.string().min(1)),
  legend: z.array(LegendItemSchema),
  /** EvidenceLink ids. */
  evidenceReferences: z.array(z.string().min(1)),
  limitations: z.array(z.string().min(1)),
  /**
   * REQUIRED accessible equivalent — map-first-workspace-instructions.md
   * §17.1: "every map lens must have a text representation." An ordered list
   * of what the lens currently shows (e.g. a numbered chronology), not just
   * a visual map/graph state. Mirrors the existing MapView place-list /
   * GraphView claims-list pattern, generalized to every lens.
   */
  textFallback: z.array(z.string().min(1)).min(1),
})
export type InvestigationLens = z.infer<typeof InvestigationLensSchema>

export const StorySequenceSchema = z.object({
  id: z.string().min(1),
  title: z.string().min(1),
  summary: z.string().min(1),
  /** Event ids, in sequence order. */
  stepIds: z.array(z.string().min(1)).min(1),
  defaultLensId: z.string().min(1),
  defaultTimeRange: HistoricalDateSchema,
})
export type StorySequence = z.infer<typeof StorySequenceSchema>

export const SystemPathSchema = z.object({
  id: z.string().min(1),
  title: z.string().min(1),
  /** Which (graph-type) lens renders this path — a lens can have zero, one, or several. */
  lensId: z.string().min(1),
  /** Any displayable record id (entity/event/claim/relationship/decision/communication/source/document) — map-first-workspace-instructions.md §13.1's "people, institutions, events, decisions, documents, places." */
  nodeIds: z.array(z.string().min(1)).min(1),
  relationshipIds: z.array(z.string().min(1)),
  summary: z.string().min(1),
  limitations: z.array(z.string().min(1)),
})
export type SystemPath = z.infer<typeof SystemPathSchema>

export const PerspectiveComparisonSchema = z.object({
  id: z.string().min(1),
  title: z.string().min(1),
  entityIds: z.array(z.string().min(1)).min(2),
  claimIds: z.array(z.string().min(1)),
  summary: z.string().min(1),
})
export type PerspectiveComparison = z.infer<typeof PerspectiveComparisonSchema>

const ContextualPromptSchema = z.object({
  id: z.string().min(1),
  text: z.string().min(1),
  targetLensId: z.string().min(1).optional(),
})

export const ContextualPromptSetSchema = z.object({
  id: z.string().min(1),
  /** Free-text description of the selection state these prompts apply to (e.g. "no-selection", or a specific record id) — map-first-workspace-instructions.md §15.3. */
  appliesTo: z.string().min(1),
  prompts: z.array(ContextualPromptSchema).min(1),
})
export type ContextualPromptSet = z.infer<typeof ContextualPromptSetSchema>

export const SelectionTargetSchema = z.object({
  id: z.string().min(1),
  kind: z.enum([
    'scene',
    'event',
    'entity',
    'claim',
    'relationship',
    'source',
    'passage',
    'timeRange',
  ]),
  recordId: z.string().min(1),
  label: z.string().min(1),
})
export type SelectionTarget = z.infer<typeof SelectionTargetSchema>

export const InvestigationLimitationSchema = z.object({
  id: z.string().min(1),
  summary: z.string().min(1),
  affectedLensIds: z.array(z.string().min(1)),
})
export type InvestigationLimitation = z.infer<typeof InvestigationLimitationSchema>

const EvidenceDepthSchema = z.enum(['shallow', 'standard', 'deep'])

export const InvestigationExperiencePlanSchema = z.object({
  opening: z.object({
    question: z.string().min(1),
    scopeSummary: z.string().min(1),
    leadAnswer: z.string().min(1),
    evidenceCoverageSummary: z.string().min(1),
  }),
  workspace: z.object({
    initialMapScope: MapScopeSchema,
    initialLensId: z.string().min(1),
    initialTimeRange: HistoricalDateSchema,
    initialPanelTab: PanelTabSchema,
    defaultPanelWidth: z.number().int().min(320),
  }),
  lenses: z.array(InvestigationLensSchema).min(1),
  storySequences: z.array(StorySequenceSchema),
  systemPaths: z.array(SystemPathSchema),
  perspectiveComparisons: z.array(PerspectiveComparisonSchema),
  contextualPrompts: z.array(ContextualPromptSetSchema),
  recommendedSelections: z.array(SelectionTargetSchema),
  limitations: z.array(InvestigationLimitationSchema),
  inspector: z.object({
    defaultEvidenceDepth: EvidenceDepthSchema,
    exposeGenerationReport: z.boolean(),
    exposeRejectedSources: z.boolean(),
  }),
})
export type InvestigationExperiencePlan = z.infer<
  typeof InvestigationExperiencePlanSchema
>

/**
 * Cross-reference validation for an InvestigationExperiencePlan against the
 * id sets already resolved by validateGeneratedInvestigation() — called
 * from there, after the base package's own rules pass, exactly like every
 * other cross-record check in that function (map-first-workspace-
 * instructions.md §18.4). `fail`/`requireReference`/`idsOf` are the same
 * helpers generatedInvestigation.ts's own checks use, imported rather than
 * duplicated.
 */
export function validateExperiencePlanReferences(
  plan: InvestigationExperiencePlan,
  ids: {
    placeIds: Set<string>
    eventIds: Set<string>
    claimIds: Set<string>
    relationshipIds: Set<string>
    entityIds: Set<string>
    sourceIds: Set<string>
    passageIds: Set<string>
    sceneIds: Set<string>
    evidenceLinkIds: Set<string>
    anyRecordIds: Set<string>
  },
  helpers: {
    requireReference: (
      ids: Set<string>,
      id: string,
      owner: string,
      target: string,
    ) => void
  },
) {
  const { requireReference } = helpers
  const lensIds = new Set(plan.lenses.map((lens) => lens.id))

  for (const lens of plan.lenses) {
    for (const id of lens.visibleLocations) {
      requireReference(ids.placeIds, id, `Lens "${lens.id}"`, 'Place')
    }
    for (const id of lens.visibleEvents) {
      requireReference(ids.eventIds, id, `Lens "${lens.id}"`, 'Event')
    }
    for (const id of lens.visibleRelationships) {
      requireReference(
        ids.relationshipIds,
        id,
        `Lens "${lens.id}"`,
        'Relationship',
      )
    }
    for (const id of lens.evidenceReferences) {
      requireReference(
        ids.evidenceLinkIds,
        id,
        `Lens "${lens.id}"`,
        'EvidenceLink',
      )
    }
  }

  requireReference(
    lensIds,
    plan.workspace.initialLensId,
    'InvestigationExperiencePlan.workspace',
    'InvestigationLens',
  )

  for (const sequence of plan.storySequences) {
    for (const stepId of sequence.stepIds) {
      requireReference(
        ids.eventIds,
        stepId,
        `StorySequence "${sequence.id}"`,
        'Event',
      )
    }
    requireReference(
      lensIds,
      sequence.defaultLensId,
      `StorySequence "${sequence.id}"`,
      'InvestigationLens',
    )
  }

  for (const path of plan.systemPaths) {
    requireReference(lensIds, path.lensId, `SystemPath "${path.id}"`, 'InvestigationLens')
    for (const nodeId of path.nodeIds) {
      requireReference(
        ids.anyRecordIds,
        nodeId,
        `SystemPath "${path.id}"`,
        'record',
      )
    }
    for (const relationshipId of path.relationshipIds) {
      requireReference(
        ids.relationshipIds,
        relationshipId,
        `SystemPath "${path.id}"`,
        'Relationship',
      )
    }
  }

  for (const comparison of plan.perspectiveComparisons) {
    for (const entityId of comparison.entityIds) {
      requireReference(
        ids.entityIds,
        entityId,
        `PerspectiveComparison "${comparison.id}"`,
        'Entity',
      )
    }
    for (const claimId of comparison.claimIds) {
      requireReference(
        ids.claimIds,
        claimId,
        `PerspectiveComparison "${comparison.id}"`,
        'Claim',
      )
    }
  }

  for (const promptSet of plan.contextualPrompts) {
    for (const prompt of promptSet.prompts) {
      if (prompt.targetLensId) {
        requireReference(
          lensIds,
          prompt.targetLensId,
          `ContextualPromptSet "${promptSet.id}" prompt "${prompt.id}"`,
          'InvestigationLens',
        )
      }
    }
  }

  for (const selection of plan.recommendedSelections) {
    if (selection.kind === 'timeRange') continue
    const targets: Record<string, Set<string>> = {
      scene: ids.sceneIds,
      event: ids.eventIds,
      entity: ids.entityIds,
      claim: ids.claimIds,
      relationship: ids.relationshipIds,
      source: ids.sourceIds,
      passage: ids.passageIds,
    }
    requireReference(
      targets[selection.kind],
      selection.recordId,
      `SelectionTarget "${selection.id}"`,
      selection.kind,
    )
  }

  for (const limitation of plan.limitations) {
    for (const lensId of limitation.affectedLensIds) {
      requireReference(
        lensIds,
        lensId,
        `InvestigationLimitation "${limitation.id}"`,
        'InvestigationLens',
      )
    }
  }
}
