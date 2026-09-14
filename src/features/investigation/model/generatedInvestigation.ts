import { z } from 'zod'
import {
  CurationStatusSchema,
  DirectOrInferredSchema,
  DocumentSchema,
  EntitySchema,
  EvidenceClassificationSchema,
  EvidenceLinkRoleSchema,
  HistoricalDateSchema,
  HistoricalMapLayerSchema,
  LocationPrecisionSchema,
  NarrativeBlockSchema,
  PassageSchema,
  ReviewStatusSchema,
  SourceSchema,
  VisibilitySchema,
  type EvidenceLink,
} from './schema'
import {
  InvestigationExperiencePlanSchema,
  validateExperiencePlanReferences,
} from './experiencePlan'

export const SUPPORTED_GENERATED_INVESTIGATION_VERSION = '1.0.0'

const PackageStatusSchema = z.enum([
  'draft',
  'partial',
  'verified',
  'reviewed',
  'published',
])

const InvestigationRequestSchema = z.object({
  id: z.string().min(1),
  rawInput: z.string().min(1),
  requestType: z.enum([
    'causal-investigation',
    'comparative-investigation',
    'event-reconstruction',
    'actor-investigation',
  ]),
  requestedDepth: z.enum(['focused', 'standard', 'deep']),
  createdAt: z.iso.datetime(),
})

const InvestigationScopeSchema = z.object({
  interpretedQuestion: z.string().min(1),
  dateRange: HistoricalDateSchema,
  geographicScope: z.array(z.string().min(1)).min(1),
  themes: z.array(z.string().min(1)),
  inclusions: z.array(z.string().min(1)),
  exclusions: z.array(z.string().min(1)),
  approvalStatus: z.enum(['proposed', 'approved', 'revised']),
})

export const GeneratedEvidenceLinkSchema = z.object({
  id: z.string().min(1),
  targetType: z.enum(['claim', 'relationship', 'knownAtTime', 'event', 'controlState']),
  targetId: z.string().min(1),
  passageId: z.string().min(1),
  role: EvidenceLinkRoleSchema,
  reviewerNote: z.string().min(1).optional(),
})
export type GeneratedEvidenceLink = z.infer<
  typeof GeneratedEvidenceLinkSchema
>

export const GeneratedClaimSchema = z.object({
  id: z.string().min(1),
  statement: z.string().min(1),
  directOrInferred: DirectOrInferredSchema,
  reviewStatus: ReviewStatusSchema,
  visibility: VisibilitySchema,
  evidenceLinkIds: z.array(z.string().min(1)).min(1),
})
export type GeneratedClaim = z.infer<typeof GeneratedClaimSchema>

export const GeneratedRelationshipSchema = z.object({
  id: z.string().min(1),
  relationshipType: z.string().min(1),
  fromId: z.string().min(1),
  toId: z.string().min(1),
  directOrInferred: DirectOrInferredSchema,
  evidenceClassification: EvidenceClassificationSchema,
  reviewStatus: ReviewStatusSchema,
  visibility: VisibilitySchema,
  evidenceLinkIds: z.array(z.string().min(1)),
})
export type GeneratedRelationship = z.infer<
  typeof GeneratedRelationshipSchema
>

export const GeneratedKnownAtTimeSchema = z.object({
  id: z.string().min(1),
  personOrInstitutionId: z.string().min(1),
  fact: z.string().min(1),
  asOfDate: HistoricalDateSchema,
  awareness: z.enum(['known', 'not-yet-known']),
  reviewStatus: ReviewStatusSchema,
  visibility: VisibilitySchema,
  evidenceLinkIds: z.array(z.string().min(1)).min(1),
})
export type GeneratedKnownAtTime = z.infer<
  typeof GeneratedKnownAtTimeSchema
>

export const GeneratedEventSchema = z.object({
  id: z.string().min(1),
  title: z.string().min(1),
  placeId: z.string().min(1),
  eventTime: HistoricalDateSchema,
  evidenceLinkIds: z.array(z.string().min(1)).min(1),
  relatedRecordIds: z.array(z.string().min(1)),
  reviewStatus: ReviewStatusSchema,
  visibility: VisibilitySchema,
})
export type GeneratedEvent = z.infer<typeof GeneratedEventSchema>

const FindingReferenceSchema = z.object({
  id: z.string().min(1),
  recordType: z.enum(['claim', 'relationship', 'knowledge-state']),
  recordId: z.string().min(1),
  label: z.string().min(1),
  importance: z.enum(['major', 'supporting']),
})

const ClaimEvidenceLedgerSchema = z.object({
  id: z.string().min(1),
  claimId: z.string().min(1),
  evidenceLinkIds: z.array(z.string().min(1)).min(1),
  conclusion: z.enum([
    'supported',
    'qualified',
    'disputed',
    'insufficient-evidence',
  ]),
  limitations: z.array(z.string().min(1)),
})

const TimelineEntrySchema = z.object({
  id: z.string().min(1),
  eventId: z.string().min(1),
  order: z.number().int().nonnegative(),
})

export const HistoricalMapAssetSchema = HistoricalMapLayerSchema.extend({
  id: z.string().min(1),
  rightsStatus: z.enum([
    'public-domain',
    'licensed',
    'needs-permission',
    'unknown',
  ]),
  periodFitDecision: z.enum(['approved', 'conditional', 'rejected', 'unknown']),
  georeferencingPrecision: z.enum(['region', 'approximate']),
})
export type HistoricalMapAsset = z.infer<typeof HistoricalMapAssetSchema>

const MapMarkerSchema = z.object({
  placeId: z.string().min(1),
  precision: LocationPrecisionSchema,
})

export const MapSceneSchema = z.object({
  id: z.string().min(1),
  sceneId: z.string().min(1),
  mapAssetId: z.string().min(1),
  markers: z.array(MapMarkerSchema),
})
export type MapScene = z.infer<typeof MapSceneSchema>

// --- Time-indexed territory layer (ADR-004 addendum) ---------------------
// A passage-grounded, time-valid control/influence/contested assertion that
// carries NO geometry — only a `geometryRef` into `territoryGeometries` — so the
// map's polygons only ever come from a sourced dataset, never the LLM. Additive:
// existing packages omit both collections.
export const ControlStateKindSchema = z.enum(['controlled', 'influence', 'contested'])
// The de jure ↔ de facto nature of `controlled` territory: a polity's own
// recognized homeland (sovereign), another's land held by force (occupied), or
// land governed without homeland sovereignty — colony / protectorate / mandate /
// client (administered).
export const ControlBasisSchema = z.enum(['sovereign', 'occupied', 'administered'])

export const ControlStateSchema = z.object({
  id: z.string().min(1),
  polity: z.string().min(1),
  kind: ControlStateKindSchema,
  // Optional refinement of `controlled` territory. When control is not sovereign,
  // `sovereignPolity` names the de jure owner (e.g. occupied France under German
  // control), so the map can show held-not-owned land as the controller textured
  // over the sovereign rather than simply recolored.
  basis: ControlBasisSchema.optional(),
  sovereignPolity: z.string().min(1).optional(),
  validFrom: HistoricalDateSchema,
  validTo: HistoricalDateSchema,
  geometryRef: z.string().min(1),
  precision: LocationPrecisionSchema,
  evidenceLinkIds: z.array(z.string().min(1)).min(1),
  reviewStatus: ReviewStatusSchema,
  visibility: VisibilitySchema,
})
export type ControlState = z.infer<typeof ControlStateSchema>

// A boundary polygon resolved from a sourced historical-boundary dataset,
// referenced by ControlState.geometryRef. `attestedYear` is the snapshot year the
// polygon actually came from (BC = negative), so rendering can say "as of ~Y";
// `sourceDataset`/`license` keep it auditable. Coordinates are a GeoJSON
// coordinate array whose deep shape the resolver guarantees, not re-checked here.
export const TerritoryGeometrySchema = z.object({
  id: z.string().min(1),
  type: z.enum(['Polygon', 'MultiPolygon']),
  coordinates: z.array(z.unknown()).min(1),
  sourceDataset: z.string().min(1),
  attestedYear: z.number().int(),
  license: z.string().min(1),
  polity: z.string().min(1).optional(),
})
export type TerritoryGeometry = z.infer<typeof TerritoryGeometrySchema>

export const InvestigationSceneSchema = z.object({
  id: z.string().min(1),
  title: z.string().min(1),
  curationStatus: CurationStatusSchema,
  dateRange: HistoricalDateSchema,
  placeIds: z.array(z.string().min(1)).min(1),
  entityIds: z.array(z.string().min(1)),
  sourceIds: z.array(z.string().min(1)),
  documentIds: z.array(z.string().min(1)),
  passageIds: z.array(z.string().min(1)),
  eventIds: z.array(z.string().min(1)),
  claimIds: z.array(z.string().min(1)),
  relationshipIds: z.array(z.string().min(1)),
  knowledgeStateIds: z.array(z.string().min(1)),
  narrativeBlockIds: z.array(z.string().min(1)).min(1),
  mapSceneId: z.string().min(1).optional(),
})
export type InvestigationScene = z.infer<typeof InvestigationSceneSchema>

export const InteractionSpecificationSchema = z.object({
  defaultSceneId: z.string().min(1),
  focusKinds: z
    .array(
      z.enum([
        'scene',
        'event',
        'entity',
        'claim',
        'relationship',
        'source',
        'passage',
        'timeRange',
      ]),
    )
    .min(1),
  enabledFacets: z.array(
    z.enum(['narrative', 'timeline', 'map', 'graph', 'evidence', 'territory']),
  ),
  omittedCapabilities: z.array(z.string().min(1)),
})

const GenerationReportSchema = z.object({
  outcome: z.enum(['complete', 'partial', 'failed', 'abstained']),
  stages: z.array(
    z.object({
      id: z.string().min(1),
      status: z.enum(['passed', 'partial', 'failed', 'abstained', 'skipped']),
    }),
  ),
  omissions: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  verificationChecks: z.array(
    z.object({
      id: z.string().min(1),
      status: z.enum(['passed', 'failed', 'abstained']),
      message: z.string().min(1),
    }),
  ),
})

const ExtensionRecordSchema = z.object({ id: z.string().min(1) }).passthrough()

export const GeneratedInvestigationSchema = z.object({
  schemaVersion: z.string().min(1),
  packageId: z.string().min(1),
  packageRevision: z.number().int().positive(),
  generatedAt: z.iso.datetime(),
  request: InvestigationRequestSchema,
  scope: InvestigationScopeSchema,
  status: PackageStatusSchema,
  presentation: z.object({
    title: z.string().min(1),
    synthesis: z.array(NarrativeBlockSchema).min(1),
    findings: z.array(FindingReferenceSchema),
    sceneIds: z.array(z.string().min(1)).min(1),
    perspectiveIds: z.array(z.string().min(1)),
  }),
  entities: z.array(EntitySchema),
  events: z.array(GeneratedEventSchema),
  decisions: z.array(ExtensionRecordSchema),
  communications: z.array(ExtensionRecordSchema),
  knowledgeStates: z.array(GeneratedKnownAtTimeSchema),
  claims: z.array(GeneratedClaimSchema),
  relationships: z.array(GeneratedRelationshipSchema),
  perspectives: z.array(ExtensionRecordSchema),
  conflicts: z.array(ExtensionRecordSchema),
  uncertainties: z.array(ExtensionRecordSchema),
  researchGaps: z.array(ExtensionRecordSchema),
  sources: z.array(SourceSchema),
  documents: z.array(DocumentSchema),
  passages: z.array(PassageSchema),
  evidenceLinks: z.array(GeneratedEvidenceLinkSchema),
  claimLedgers: z.array(ClaimEvidenceLedgerSchema),
  timeline: z.array(TimelineEntrySchema),
  mapAssets: z.array(HistoricalMapAssetSchema),
  mapScenes: z.array(MapSceneSchema),
  // ADR-004 addendum, optional/additive — the time-indexed territory layer.
  // Existing packages remain valid without these; when present they get
  // cross-reference-validated below, same discipline as every other field.
  controlStates: z.array(ControlStateSchema).optional(),
  territoryGeometries: z.array(TerritoryGeometrySchema).optional(),
  scenes: z.array(InvestigationSceneSchema).min(1),
  interactionSpec: InteractionSpecificationSchema,
  generationReport: GenerationReportSchema,
  /**
   * Phase D, optional/additive (docs/decisions/ADR-002-map-first-workspace.md)
   * — existing packages remain valid without one; a package that has one
   * gets it cross-reference-validated below, same discipline as every other
   * field.
   */
  experiencePlan: InvestigationExperiencePlanSchema.optional(),
})
export type GeneratedInvestigation = z.infer<
  typeof GeneratedInvestigationSchema
>

export class GeneratedInvestigationValidationError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'GeneratedInvestigationValidationError'
  }
}

export function fail(message: string): never {
  throw new GeneratedInvestigationValidationError(message)
}

function idsOf(records: { id: string }[]) {
  return new Set(records.map((record) => record.id))
}

export function requireReference(
  ids: Set<string>,
  id: string,
  owner: string,
  target: string,
) {
  if (!ids.has(id)) fail(`${owner} references unknown ${target} "${id}"`)
}

function ensureUniqueIds(
  collections: Array<{ name: string; records: { id: string }[] }>,
) {
  const owners = new Map<string, string>()
  for (const collection of collections) {
    for (const record of collection.records) {
      const priorOwner = owners.get(record.id)
      if (priorOwner) {
        fail(
          `ID "${record.id}" is not unique; it appears in ${priorOwner} and ${collection.name}`,
        )
      }
      owners.set(record.id, collection.name)
    }
  }
}

function evidenceFor(
  record: { id: string; evidenceLinkIds: string[] },
  expectedType: GeneratedEvidenceLink['targetType'],
  linksById: Map<string, GeneratedEvidenceLink>,
) {
  return record.evidenceLinkIds.map((linkId) => {
    const link = linksById.get(linkId)
    if (!link) fail(`Record "${record.id}" references unknown EvidenceLink "${linkId}"`)
    if (link.targetType !== expectedType || link.targetId !== record.id) {
      fail(
        `EvidenceLink "${linkId}" does not target ${expectedType} "${record.id}"`,
      )
    }
    return link
  })
}

const PRECISION_RANK = {
  approximate: 0,
  region: 1,
  city: 2,
  building: 3,
} as const

/**
 * Validates both the JSON shape and its cross-record historical-integrity
 * invariants. The renderer calls this before normalizing any package.
 */
export function validateGeneratedInvestigation(
  input: unknown,
): GeneratedInvestigation {
  let investigation: GeneratedInvestigation
  try {
    investigation = GeneratedInvestigationSchema.parse(input)
  } catch (error) {
    if (error instanceof z.ZodError) {
      throw new GeneratedInvestigationValidationError(
        `GeneratedInvestigation schema validation failed: ${error.issues
          .map((issue) => `${issue.path.join('.')}: ${issue.message}`)
          .join('; ')}`,
      )
    }
    throw error
  }

  if (investigation.schemaVersion !== SUPPORTED_GENERATED_INVESTIGATION_VERSION) {
    fail(
      `Unsupported GeneratedInvestigation schema version "${investigation.schemaVersion}"; ` +
        `this renderer supports "${SUPPORTED_GENERATED_INVESTIGATION_VERSION}"`,
    )
  }

  ensureUniqueIds([
    { name: 'entities', records: investigation.entities },
    { name: 'events', records: investigation.events },
    { name: 'decisions', records: investigation.decisions },
    { name: 'communications', records: investigation.communications },
    { name: 'knowledgeStates', records: investigation.knowledgeStates },
    { name: 'claims', records: investigation.claims },
    { name: 'relationships', records: investigation.relationships },
    { name: 'perspectives', records: investigation.perspectives },
    { name: 'conflicts', records: investigation.conflicts },
    { name: 'uncertainties', records: investigation.uncertainties },
    { name: 'researchGaps', records: investigation.researchGaps },
    { name: 'sources', records: investigation.sources },
    { name: 'documents', records: investigation.documents },
    { name: 'passages', records: investigation.passages },
    { name: 'evidenceLinks', records: investigation.evidenceLinks },
    { name: 'claimLedgers', records: investigation.claimLedgers },
    { name: 'timeline', records: investigation.timeline },
    { name: 'mapAssets', records: investigation.mapAssets },
    { name: 'mapScenes', records: investigation.mapScenes },
    { name: 'controlStates', records: investigation.controlStates ?? [] },
    { name: 'territoryGeometries', records: investigation.territoryGeometries ?? [] },
    { name: 'scenes', records: investigation.scenes },
    { name: 'synthesis', records: investigation.presentation.synthesis },
    { name: 'findings', records: investigation.presentation.findings },
    ...(investigation.experiencePlan
      ? [
          { name: 'lenses', records: investigation.experiencePlan.lenses },
          {
            name: 'storySequences',
            records: investigation.experiencePlan.storySequences,
          },
          {
            name: 'systemPaths',
            records: investigation.experiencePlan.systemPaths,
          },
          {
            name: 'perspectiveComparisons',
            records: investigation.experiencePlan.perspectiveComparisons,
          },
          {
            name: 'contextualPrompts',
            records: investigation.experiencePlan.contextualPrompts,
          },
          {
            name: 'recommendedSelections',
            records: investigation.experiencePlan.recommendedSelections,
          },
          {
            name: 'limitations',
            records: investigation.experiencePlan.limitations,
          },
        ]
      : []),
  ])

  const entityIds = idsOf(investigation.entities)
  const placeIds = new Set(
    investigation.entities
      .filter((entity) => entity.entityType === 'place')
      .map((entity) => entity.id),
  )
  const sourceIds = idsOf(investigation.sources)
  const documentIds = idsOf(investigation.documents)
  const passageIds = idsOf(investigation.passages)
  const eventIds = idsOf(investigation.events)
  const claimIds = idsOf(investigation.claims)
  const relationshipIds = idsOf(investigation.relationships)
  const knowledgeStateIds = idsOf(investigation.knowledgeStates)
  const sceneIds = idsOf(investigation.scenes)
  const narrativeIds = idsOf(investigation.presentation.synthesis)
  const perspectiveIds = idsOf(investigation.perspectives)
  const mapAssetIds = idsOf(investigation.mapAssets)
  const mapSceneIds = idsOf(investigation.mapScenes)
  const controlStateIds = idsOf(investigation.controlStates ?? [])
  const territoryGeometryIds = idsOf(investigation.territoryGeometries ?? [])
  const recordIds = new Set([
    ...claimIds,
    ...relationshipIds,
    ...knowledgeStateIds,
  ])
  const linksById = new Map(
    investigation.evidenceLinks.map((link) => [link.id, link]),
  )
  const targetEvidenceLinkIds = new Map<string, Set<string>>()
  for (const [targetType, records] of [
    ['claim', investigation.claims],
    ['relationship', investigation.relationships],
    ['knownAtTime', investigation.knowledgeStates],
    ['event', investigation.events],
    ['controlState', investigation.controlStates ?? []],
  ] as const) {
    for (const record of records) {
      if (new Set(record.evidenceLinkIds).size !== record.evidenceLinkIds.length) {
        fail(`Target record "${record.id}" contains a duplicate EvidenceLink id`)
      }
      targetEvidenceLinkIds.set(
        `${targetType}:${record.id}`,
        new Set(record.evidenceLinkIds),
      )
    }
  }

  for (const document of investigation.documents) {
    requireReference(
      sourceIds,
      document.sourceId,
      `Document "${document.id}"`,
      'Source',
    )
  }
  for (const passage of investigation.passages) {
    requireReference(
      documentIds,
      passage.documentId,
      `Passage "${passage.id}"`,
      'Document',
    )
  }
  for (const link of investigation.evidenceLinks) {
    requireReference(
      passageIds,
      link.passageId,
      `EvidenceLink "${link.id}"`,
      'Passage',
    )
    const targets =
      link.targetType === 'claim'
        ? claimIds
        : link.targetType === 'relationship'
          ? relationshipIds
          : link.targetType === 'knownAtTime'
            ? knowledgeStateIds
            : link.targetType === 'event'
              ? eventIds
              : controlStateIds
    requireReference(
      targets,
      link.targetId,
      `EvidenceLink "${link.id}"`,
      link.targetType,
    )
    if (!targetEvidenceLinkIds.get(`${link.targetType}:${link.targetId}`)?.has(link.id)) {
      fail(
        `EvidenceLink "${link.id}" is not listed by its target record ` +
          `"${link.targetId}"`,
      )
    }
  }

  for (const claim of investigation.claims) {
    const links = evidenceFor(claim, 'claim', linksById)
    if (!links.some((link) => link.role === 'supporting')) {
      fail(`Claim "${claim.id}" requires a supporting EvidenceLink`)
    }
  }
  for (const relationship of investigation.relationships) {
    requireReference(
      recordIds,
      relationship.fromId,
      `Relationship "${relationship.id}"`,
      'record',
    )
    requireReference(
      recordIds,
      relationship.toId,
      `Relationship "${relationship.id}"`,
      'record',
    )
    const links = evidenceFor(relationship, 'relationship', linksById)
    const hasSupporting = links.some((link) => link.role === 'supporting')
    const hasCounterevidence = links.some(
      (link) => link.role === 'counterevidence',
    )
    if (
      ['directly_supported', 'indirectly_supported'].includes(
        relationship.evidenceClassification,
      ) &&
      !hasSupporting
    ) {
      fail(
        `Relationship "${relationship.id}" requires a supporting EvidenceLink`,
      )
    }
    if (
      relationship.evidenceClassification === 'disputed' &&
      (!hasSupporting || !hasCounterevidence)
    ) {
      fail(
        `Disputed Relationship "${relationship.id}" requires supporting and counterevidence links`,
      )
    }
  }
  for (const knowledgeState of investigation.knowledgeStates) {
    requireReference(
      entityIds,
      knowledgeState.personOrInstitutionId,
      `KnownAtTime "${knowledgeState.id}"`,
      'Entity',
    )
    evidenceFor(knowledgeState, 'knownAtTime', linksById)
  }
  for (const event of investigation.events) {
    requireReference(
      placeIds,
      event.placeId,
      `Event "${event.id}"`,
      'Place',
    )
    evidenceFor(event, 'event', linksById)
    for (const recordId of event.relatedRecordIds) {
      requireReference(
        recordIds,
        recordId,
        `Event "${event.id}"`,
        'displayable record',
      )
    }
  }

  const ledgersByClaimId = new Map(
    investigation.claimLedgers.map((ledger) => [ledger.claimId, ledger]),
  )
  for (const ledger of investigation.claimLedgers) {
    requireReference(
      claimIds,
      ledger.claimId,
      `ClaimEvidenceLedger "${ledger.id}"`,
      'Claim',
    )
    for (const linkId of ledger.evidenceLinkIds) {
      const link = linksById.get(linkId)
      if (!link) {
        fail(
          `ClaimEvidenceLedger "${ledger.id}" references unknown EvidenceLink "${linkId}"`,
        )
      }
      if (link.targetType !== 'claim' || link.targetId !== ledger.claimId) {
        fail(
          `ClaimEvidenceLedger "${ledger.id}" includes evidence for another record`,
        )
      }
    }
  }

  for (const block of investigation.presentation.synthesis) {
    if (block.relatedEventId) {
      requireReference(
        eventIds,
        block.relatedEventId,
        `NarrativeBlock "${block.id}"`,
        'Event',
      )
    }
    for (const recordId of block.referencedRecordIds) {
      requireReference(
        recordIds,
        recordId,
        `NarrativeBlock "${block.id}"`,
        'Claim, Relationship, or KnownAtTime record',
      )
    }
  }
  for (const finding of investigation.presentation.findings) {
    const ids =
      finding.recordType === 'claim'
        ? claimIds
        : finding.recordType === 'relationship'
          ? relationshipIds
          : knowledgeStateIds
    requireReference(
      ids,
      finding.recordId,
      `Finding "${finding.id}"`,
      finding.recordType,
    )
    if (finding.recordType === 'claim' && finding.importance === 'major') {
      const ledger = ledgersByClaimId.get(finding.recordId)
      if (!ledger) {
        fail(
          `Major finding "${finding.id}" requires a ClaimEvidenceLedger for claim "${finding.recordId}"`,
        )
      }
      const hasSupportingPassage = ledger.evidenceLinkIds.some(
        (linkId) => linksById.get(linkId)?.role === 'supporting',
      )
      if (!hasSupportingPassage) {
        fail(
          `Major finding "${finding.id}" lacks a supporting Passage through its claim ledger`,
        )
      }
    }
  }

  for (const sceneId of investigation.presentation.sceneIds) {
    requireReference(sceneIds, sceneId, 'Presentation', 'Scene')
  }
  for (const perspectiveId of investigation.presentation.perspectiveIds) {
    requireReference(perspectiveIds, perspectiveId, 'Presentation', 'Perspective')
  }

  for (const scene of investigation.scenes) {
    const references: Array<[string[], Set<string>, string]> = [
      [scene.placeIds, placeIds, 'Place'],
      [scene.entityIds, entityIds, 'Entity'],
      [scene.sourceIds, sourceIds, 'Source'],
      [scene.documentIds, documentIds, 'Document'],
      [scene.passageIds, passageIds, 'Passage'],
      [scene.eventIds, eventIds, 'Event'],
      [scene.claimIds, claimIds, 'Claim'],
      [scene.relationshipIds, relationshipIds, 'Relationship'],
      [scene.knowledgeStateIds, knowledgeStateIds, 'KnownAtTime'],
      [scene.narrativeBlockIds, narrativeIds, 'NarrativeBlock'],
    ]
    for (const [ids, knownIds, type] of references) {
      for (const id of ids) {
        requireReference(knownIds, id, `Scene "${scene.id}"`, type)
      }
    }
    if (scene.mapSceneId) {
      requireReference(
        mapSceneIds,
        scene.mapSceneId,
        `Scene "${scene.id}"`,
        'MapScene',
      )
    }
  }

  const placesById = new Map(
    investigation.entities
      .filter((entity) => entity.entityType === 'place')
      .map((place) => [place.id, place]),
  )
  const mapAssetsById = new Map(
    investigation.mapAssets.map((asset) => [asset.id, asset]),
  )
  for (const mapScene of investigation.mapScenes) {
    requireReference(
      sceneIds,
      mapScene.sceneId,
      `MapScene "${mapScene.id}"`,
      'Scene',
    )
    requireReference(
      mapAssetIds,
      mapScene.mapAssetId,
      `MapScene "${mapScene.id}"`,
      'MapAsset',
    )
    const asset = mapAssetsById.get(mapScene.mapAssetId)!
    if (!['public-domain', 'licensed'].includes(asset.rightsStatus)) {
      fail(
        `Map asset "${asset.id}" cannot be displayed because its rights status is "${asset.rightsStatus}"`,
      )
    }
    if (!['approved', 'conditional'].includes(asset.periodFitDecision)) {
      fail(
        `Map asset "${asset.id}" cannot be displayed without an approved period-fit decision`,
      )
    }
    for (const marker of mapScene.markers) {
      const place = placesById.get(marker.placeId)
      if (!place) {
        fail(
          `Map marker references unknown Place "${marker.placeId}" in MapScene "${mapScene.id}"`,
        )
      }
      const supportedRank = Math.max(
        ...place.periodRecords.map(
          (period) => PRECISION_RANK[period.precision],
        ),
      )
      if (PRECISION_RANK[marker.precision] > supportedRank) {
        fail(
          `Map marker precision "${marker.precision}" exceeds Place "${place.id}" evidence precision`,
        )
      }
    }
  }

  for (const entry of investigation.timeline) {
    requireReference(
      eventIds,
      entry.eventId,
      `TimelineEntry "${entry.id}"`,
      'Event',
    )
  }
  requireReference(
    sceneIds,
    investigation.interactionSpec.defaultSceneId,
    'InteractionSpecification',
    'Scene',
  )

  if (
    investigation.generationReport.verificationChecks.some(
      (check) => check.status === 'failed',
    )
  ) {
    fail('GenerationReport contains a failed required verification check')
  }
  if (
    investigation.status === 'partial' &&
    investigation.generationReport.outcome !== 'partial'
  ) {
    fail('A partial package must carry a partial GenerationReport outcome')
  }

  if (investigation.status === 'published') {
    const publicRecords = [
      ...investigation.claims,
      ...investigation.relationships,
      ...investigation.knowledgeStates,
      ...investigation.events,
    ]
    for (const record of publicRecords) {
      if (!['reviewed', 'disputed'].includes(record.reviewStatus)) {
        fail(
          `Published package record "${record.id}" must be reviewed or disputed`,
        )
      }
      if (record.visibility !== 'public') {
        fail(`Published package record "${record.id}" must be public`)
      }
    }
    for (const document of investigation.documents) {
      if (document.visibility !== 'public') {
        fail(`Published package Document "${document.id}" must be public`)
      }
    }
  }

  if (investigation.experiencePlan) {
    const anyRecordIds = new Set([
      ...entityIds,
      ...eventIds,
      ...claimIds,
      ...relationshipIds,
      ...knowledgeStateIds,
      ...idsOf(investigation.decisions),
      ...idsOf(investigation.communications),
      ...sourceIds,
      ...documentIds,
    ])
    validateExperiencePlanReferences(
      investigation.experiencePlan,
      {
        placeIds,
        eventIds,
        claimIds,
        relationshipIds,
        entityIds,
        sourceIds,
        passageIds,
        sceneIds,
        evidenceLinkIds: new Set(linksById.keys()),
        anyRecordIds,
      },
      { requireReference },
    )
  }

  // Rule 22: the time-indexed territory layer (ADR-004 addendum). Each
  // ControlState is grounded like any claim (>=1 supporting EvidenceLink,
  // bidirectionally targeted via Rule 5/5b), references a sourced geometry, is
  // time-ordered, and is honest about precision; a declared 'territory' facet
  // must have data behind it.
  const controlStates = investigation.controlStates ?? []
  for (const controlState of controlStates) {
    const links = evidenceFor(controlState, 'controlState', linksById)
    if (!links.some((link) => link.role === 'supporting')) {
      fail(`ControlState "${controlState.id}" requires a supporting EvidenceLink`)
    }
    requireReference(
      territoryGeometryIds,
      controlState.geometryRef,
      `ControlState "${controlState.id}"`,
      'TerritoryGeometry',
    )
    if (controlState.validFrom.earliest > controlState.validTo.latest) {
      fail(`ControlState "${controlState.id}" has validFrom after validTo`)
    }
    // Influence and contested reaches had no crisp frontier — they may not claim
    // building/city precision, only region/approximate ("rendering cannot exceed
    // the evidence's precision", extended to fuzzy territory).
    if (
      (controlState.kind === 'influence' || controlState.kind === 'contested') &&
      PRECISION_RANK[controlState.precision] > PRECISION_RANK['region']
    ) {
      fail(
        `${controlState.kind} ControlState "${controlState.id}" cannot claim ` +
          `"${controlState.precision}" precision; use region or approximate`,
      )
    }
    // A control basis (de jure vs de facto) describes controlled territory only.
    if (controlState.basis && controlState.kind !== 'controlled') {
      fail(
        `ControlState "${controlState.id}" sets a control basis but its kind is ` +
          `"${controlState.kind}"; basis applies only to controlled territory`,
      )
    }
    // A named de jure owner is meaningful only when control is not sovereign, and
    // the sovereign differs from the controller (that is what occupation is).
    if (controlState.sovereignPolity) {
      if (!controlState.basis || controlState.basis === 'sovereign') {
        fail(
          `ControlState "${controlState.id}" names a sovereignPolity but is not held on ` +
            `a non-sovereign basis (occupied/administered)`,
        )
      }
      if (controlState.sovereignPolity === controlState.polity) {
        fail(
          `ControlState "${controlState.id}" names its own polity as sovereignPolity; ` +
            `the sovereign must differ from the controller`,
        )
      }
    }
  }
  if (investigation.interactionSpec.enabledFacets.includes('territory') && controlStates.length === 0) {
    fail("The 'territory' facet is enabled but no ControlState records back it")
  }

  return investigation
}

/** Rehydrates the existing Scene-facing evidence shape without duplicating it in JSON. */
export function toSceneEvidenceLinks(
  evidenceLinkIds: string[],
  linksById: Map<string, GeneratedEvidenceLink>,
): EvidenceLink[] {
  return evidenceLinkIds.map((id) => {
    const link = linksById.get(id)
    if (!link) fail(`Unknown EvidenceLink "${id}" while normalizing Scene`)
    return {
      passageId: link.passageId,
      role: link.role,
      reviewerNote: link.reviewerNote,
    }
  })
}
