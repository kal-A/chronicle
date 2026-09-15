import { z } from 'zod'

/**
 * Runtime-validated domain contract for Chronicle's Phase 1 static prototype.
 * Mirrors docs/architecture/domain-model.md, scoped to what Scene 2 needs.
 * Every enum below is required wherever it appears — no schema default may
 * imply certainty the underlying evidence doesn't have (AGENTS.md §3/§12).
 */

// ---------------------------------------------------------------------------
// Shared value types
// ---------------------------------------------------------------------------

export const DatePrecisionSchema = z.enum([
  'exact',
  'approximate',
  'range',
  'disputed',
])
export type DatePrecision = z.infer<typeof DatePrecisionSchema>

const isoDate = z.iso.date()

/**
 * Era-capable date interval (ADR-005). The canonical ordering key is a signed
 * astronomical year (`earliestYear`/`latestYear`: 1 = 1 CE, 0 = 1 BC, -1 = 2 BC,
 * …); the ISO calendar dates are optional CE-only day/month precision and must be
 * omitted for BC. Order/compare with the key helpers below so records that carry
 * only a signed year (BC) still sort correctly against dated CE records.
 */

/** Structural view of a HistoricalDate's bounds — enough for the key helpers. */
type DateBounds = {
  earliest?: string
  latest?: string
  earliestYear?: number
  latestYear?: number
}

/** Cross-era ordering key: [signed year, day-of-year]. */
export type DateKey = readonly [number, number]

function isoYear(iso: string): number {
  return Number(iso.slice(0, iso.indexOf('-', 1)))
}

function isoDayOfYear(iso: string): number {
  const [y, m, d] = iso.split('-').map(Number)
  // setUTCFullYear avoids Date's 0-99 -> 1900s remap and respects leap years.
  const jan1 = new Date(Date.UTC(2000, 0, 1))
  jan1.setUTCFullYear(y)
  const point = new Date(Date.UTC(2000, m - 1, d))
  point.setUTCFullYear(y)
  return Math.floor((point.getTime() - jan1.getTime()) / 86_400_000) + 1
}

export function historicalDateLowerKey(d: DateBounds): DateKey {
  if (d.earliest !== undefined) return [isoYear(d.earliest), isoDayOfYear(d.earliest)]
  return [d.earliestYear as number, 1]
}

export function historicalDateUpperKey(d: DateBounds): DateKey {
  if (d.latest !== undefined) return [isoYear(d.latest), isoDayOfYear(d.latest)]
  return [d.latestYear as number, 366]
}

/** Compare two cross-era keys: negative if a < b, 0 if equal, positive if a > b. */
export function compareKeys(a: DateKey, b: DateKey): number {
  return a[0] - b[0] || a[1] - b[1]
}

function keyLE(a: DateKey, b: DateKey): boolean {
  return compareKeys(a, b) <= 0
}

/** Order two HistoricalDates by their lower bound (BC-safe). */
export function compareHistoricalDates(a: DateBounds, b: DateBounds): number {
  const [ay, ad] = historicalDateLowerKey(a)
  const [by, bd] = historicalDateLowerKey(b)
  return ay - by || ad - bd
}

export const HistoricalDateSchema = z
  .object({
    precision: DatePrecisionSchema,
    earliest: isoDate.optional(),
    latest: isoDate.optional(),
    earliestYear: z.number().int().optional(),
    latestYear: z.number().int().optional(),
    label: z.string().min(1).optional(),
  })
  .refine((d) => d.earliest !== undefined || d.earliestYear !== undefined, {
    message: 'HistoricalDate needs earliest or earliestYear',
    path: ['earliest'],
  })
  .refine((d) => d.latest !== undefined || d.latestYear !== undefined, {
    message: 'HistoricalDate needs latest or latestYear',
    path: ['latest'],
  })
  .refine(
    (d) => d.earliest === undefined || d.earliestYear === undefined || isoYear(d.earliest) === d.earliestYear,
    { message: 'earliest.year must equal earliestYear', path: ['earliestYear'] },
  )
  .refine(
    (d) => d.latest === undefined || d.latestYear === undefined || isoYear(d.latest) === d.latestYear,
    { message: 'latest.year must equal latestYear', path: ['latestYear'] },
  )
  .refine((d) => keyLE(historicalDateLowerKey(d), historicalDateUpperKey(d)), {
    message: 'earliest must not be after latest',
    path: ['earliest'],
  })
  .refine(
    (d) => d.precision !== 'exact' || (d.earliest === d.latest && d.earliestYear === d.latestYear),
    { message: 'an exact HistoricalDate must have earliest === latest', path: ['precision'] },
  )
export type HistoricalDate = z.infer<typeof HistoricalDateSchema>

export const LocationPrecisionSchema = z.enum([
  'building',
  'city',
  'region',
  'approximate',
])
export type LocationPrecision = z.infer<typeof LocationPrecisionSchema>

export const ReviewStatusSchema = z.enum([
  'proposed',
  'reviewed',
  'disputed',
  'rejected',
])
export type ReviewStatus = z.infer<typeof ReviewStatusSchema>

/**
 * Phase 1 does not yet run the full docs/research/review-standard.md process.
 * `prototype-curated` is the honest label for content that passed the Plan 0
 * content gate and owner review only — see docs/research/validation-status.md.
 * It is intentionally distinct from `ReviewStatus` (which governs the eventual
 * Phase 2+ domain model) so Phase 1 never has to lie about a record being
 * `reviewed` to make it displayable.
 */
export const CurationStatusSchema = z.enum([
  'identified',
  'acquired',
  'passages-extracted',
  'prototype-curated',
  'reviewed',
])
export type CurationStatus = z.infer<typeof CurationStatusSchema>

/** Statuses eligible to back a NarrativeBlock's material assertions in Phase 1. */
const DISPLAYABLE_CURATION_STATUSES: CurationStatus[] = [
  'prototype-curated',
  'reviewed',
]

export const VisibilitySchema = z.enum(['public', 'private-workspace'])
export type Visibility = z.infer<typeof VisibilitySchema>

export const DirectOrInferredSchema = z.enum(['direct', 'inferred'])
export type DirectOrInferred = z.infer<typeof DirectOrInferredSchema>

/** The seven values from docs/research/historical-methodology.md. Required, never defaulted. */
export const EvidenceClassificationSchema = z.enum([
  'directly_supported',
  'indirectly_supported',
  'contextual',
  'correlational',
  'disputed',
  'speculative',
  'insufficient_evidence',
])
export type EvidenceClassification = z.infer<
  typeof EvidenceClassificationSchema
>

export const EvidenceLinkRoleSchema = z.enum([
  'supporting',
  'counterevidence',
  'context',
])
export type EvidenceLinkRole = z.infer<typeof EvidenceLinkRoleSchema>

// ---------------------------------------------------------------------------
// Entities
// ---------------------------------------------------------------------------

export const PersonEntitySchema = z.object({
  id: z.string().min(1),
  entityType: z.literal('person'),
  canonicalName: z.string().min(1),
  alsoKnownAs: z.array(z.string().min(1)).default([]),
  description: z.string().min(1),
  reviewStatus: ReviewStatusSchema,
})
export type PersonEntity = z.infer<typeof PersonEntitySchema>

export const PlacePeriodRecordSchema = z.object({
  periodLabel: z.string().min(1),
  nameAtTime: z.string().min(1),
  controllingPolity: z.string().min(1),
  precision: LocationPrecisionSchema,
})
export type PlacePeriodRecord = z.infer<typeof PlacePeriodRecordSchema>

export const PlaceEntitySchema = z.object({
  id: z.string().min(1),
  entityType: z.literal('place'),
  canonicalName: z.string().min(1),
  periodRecords: z.array(PlacePeriodRecordSchema).min(1),
  reviewStatus: ReviewStatusSchema,
  /** No building-level pin may be implied from city-level evidence (AGENTS.md §12). */
  coordinates: z
    .object({ lat: z.number(), lng: z.number() })
    .optional(),
})
export type PlaceEntity = z.infer<typeof PlaceEntitySchema>

export const EntitySchema = z.discriminatedUnion('entityType', [
  PersonEntitySchema,
  PlaceEntitySchema,
])
export type Entity = z.infer<typeof EntitySchema>

// ---------------------------------------------------------------------------
// Source -> Document -> Passage
// ---------------------------------------------------------------------------

export const SourceTypeSchema = z.enum([
  'primary-official-diplomatic',
  'primary-personal',
  'primary-press',
  'secondary-specialist',
  'secondary-general',
  'tertiary-reference',
])
export type SourceType = z.infer<typeof SourceTypeSchema>

/**
 * A Source is global and reusable across investigations — it never carries an
 * investigationId. See docs/product/shared-evidence-network.md and
 * docs/architecture/domain-model.md.
 */
export const SourceSchema = z.object({
  id: z.string().min(1),
  title: z.string().min(1),
  sourceType: SourceTypeSchema,
  authorOrOrigin: z.string().min(1),
  dateOfSource: HistoricalDateSchema,
  originalLanguage: z.string().min(1),
  rightsStatus: z.enum([
    'public-domain',
    'licensed',
    'needs-permission',
    'unknown',
  ]),
  curationStatus: CurationStatusSchema,
  knownLimitations: z.string().min(1),
  linkOrLocation: z.string().min(1),
})
export type Source = z.infer<typeof SourceSchema>

export const DocumentSchema = z.object({
  id: z.string().min(1),
  sourceId: z.string().min(1),
  editionCitation: z.string().min(1),
  translationCredit: z.string().min(1).optional(),
  visibility: VisibilitySchema,
  knownLimitations: z.string().min(1),
})
export type Document = z.infer<typeof DocumentSchema>

export const PassageSchema = z.object({
  id: z.string().min(1),
  documentId: z.string().min(1),
  /** Short, attributed excerpt only — never a full reproduction of the source text. */
  excerpt: z.string().min(1),
  locator: z.string().min(1),
  sentTime: HistoricalDateSchema.optional(),
  receivedTime: HistoricalDateSchema.optional(),
  gapNote: z.string().min(1).optional(),
})
export type Passage = z.infer<typeof PassageSchema>

// ---------------------------------------------------------------------------
// EvidenceLink -> Claim / Relationship / KnownAtTime
// ---------------------------------------------------------------------------

export const EvidenceLinkSchema = z.object({
  passageId: z.string().min(1),
  role: EvidenceLinkRoleSchema,
  reviewerNote: z.string().min(1).optional(),
})
export type EvidenceLink = z.infer<typeof EvidenceLinkSchema>

function hasRole(links: EvidenceLink[], role: EvidenceLinkRole) {
  return links.some((l) => l.role === role)
}

export const ClaimSchema = z
  .object({
    id: z.string().min(1),
    statement: z.string().min(1),
    directOrInferred: DirectOrInferredSchema,
    reviewStatus: ReviewStatusSchema,
    evidenceLinks: z.array(EvidenceLinkSchema).min(1),
  })
  .refine((c) => hasRole(c.evidenceLinks, 'supporting'), {
    message: 'a Claim requires at least one supporting EvidenceLink',
    path: ['evidenceLinks'],
  })
export type Claim = z.infer<typeof ClaimSchema>

export const RelationshipSchema = z
  .object({
    id: z.string().min(1),
    relationshipType: z.string().min(1),
    fromId: z.string().min(1),
    toId: z.string().min(1),
    directOrInferred: DirectOrInferredSchema,
    evidenceClassification: EvidenceClassificationSchema,
    evidenceLinks: z.array(EvidenceLinkSchema),
  })
  .refine(
    (r) =>
      !['directly_supported', 'indirectly_supported'].includes(
        r.evidenceClassification,
      ) || hasRole(r.evidenceLinks, 'supporting'),
    {
      message:
        'directly_supported/indirectly_supported relationships require a supporting EvidenceLink',
      path: ['evidenceLinks'],
    },
  )
  .refine(
    (r) =>
      r.evidenceClassification !== 'disputed' ||
      (hasRole(r.evidenceLinks, 'supporting') &&
        hasRole(r.evidenceLinks, 'counterevidence')),
    {
      message:
        'a disputed relationship must retain both a supporting and a counterevidence EvidenceLink',
      path: ['evidenceLinks'],
    },
  )
export type Relationship = z.infer<typeof RelationshipSchema>

export const KnownAtTimeSchema = z.object({
  id: z.string().min(1),
  personOrInstitutionId: z.string().min(1),
  fact: z.string().min(1),
  asOfDate: HistoricalDateSchema,
  awareness: z.enum(['known', 'not-yet-known']),
  evidenceLinks: z.array(EvidenceLinkSchema).min(1),
})
export type KnownAtTime = z.infer<typeof KnownAtTimeSchema>

/**
 * A timeline-facing occurrence, distinct from a Claim (an assertion) or a
 * Relationship (a link between assertions). Added at Plan 4, when the
 * timeline facet first needed it — see docs/architecture/domain-model.md's
 * "introduced only when a phase's requirements show it's needed" principle.
 */
export const EventRecordSchema = z.object({
  id: z.string().min(1),
  title: z.string().min(1),
  placeId: z.string().min(1),
  eventTime: HistoricalDateSchema,
  evidenceLinks: z.array(EvidenceLinkSchema).min(1),
  /** Claim/Relationship/KnownAtTime ids the evidence panel should surface when this event is focused. */
  relatedRecordIds: z.array(z.string().min(1)).default([]),
})
export type EventRecord = z.infer<typeof EventRecordSchema>

// ---------------------------------------------------------------------------
// Narrative
// ---------------------------------------------------------------------------

export const NarrativeBlockSchema = z
  .object({
    id: z.string().min(1),
    order: z.number().int().nonnegative(),
    text: z.string().min(1),
    /** True if this block asserts a specific historical fact, not just scene-setting prose. */
    isMaterialAssertion: z.boolean(),
    /** IDs of Claim/Relationship/KnownAtTime records this block's assertions rest on. */
    referencedRecordIds: z.array(z.string().min(1)).default([]),
    /** Optional: the Event this block is "about," for narrative-to-timeline focus interaction. */
    relatedEventId: z.string().min(1).optional(),
  })
  .refine(
    (b) => !b.isMaterialAssertion || b.referencedRecordIds.length > 0,
    {
      message:
        'a material NarrativeBlock must reference at least one Claim/Relationship/KnownAtTime record',
      path: ['referencedRecordIds'],
    },
  )
export type NarrativeBlock = z.infer<typeof NarrativeBlockSchema>

// ---------------------------------------------------------------------------
// Scene
// ---------------------------------------------------------------------------

/**
 * A period-accurate basemap image for a scene's theatre, bound to real
 * geographic corner coordinates so it can be placed under MapLibre markers.
 * Never a live modern-tile basemap (docs/architecture/spatial-architecture.md
 * — political borders must not be implied from present-day geography). The
 * image itself carries the period's political boundaries, so it is honest by
 * construction rather than relying on a "border-suppressed" style choice.
 *
 * `bounds` corners are read from the source plate's own printed graticule
 * (where available) or from identifiable reference points, not measured to
 * survey-grade precision — `georeferencingNote` discloses the method. This is
 * adequate for scene-level orientation, matching the honest-imprecision
 * pattern used throughout Scene 2's content fixture.
 */
export const HistoricalMapLayerSchema = z.object({
  imagePath: z.string().min(1),
  bounds: z.object({
    topLeft: z.object({ lat: z.number(), lng: z.number() }),
    topRight: z.object({ lat: z.number(), lng: z.number() }),
    bottomRight: z.object({ lat: z.number(), lng: z.number() }),
    bottomLeft: z.object({ lat: z.number(), lng: z.number() }),
  }),
  defaultView: z.object({
    center: z.object({ lat: z.number(), lng: z.number() }),
    zoom: z.number(),
  }),
  periodLabel: z.string().min(1),
  sourceCitation: z.string().min(1),
  attribution: z.string().min(1),
  license: z.string().min(1),
  georeferencingNote: z.string().min(1),
})
export type HistoricalMapLayer = z.infer<typeof HistoricalMapLayerSchema>

export const SceneSchema = z.object({
  id: z.string().min(1),
  title: z.string().min(1),
  curationStatus: CurationStatusSchema,
  dateRange: HistoricalDateSchema,
  placeIds: z.array(z.string().min(1)).min(1),
  entities: z.array(EntitySchema),
  sources: z.array(SourceSchema),
  documents: z.array(DocumentSchema),
  passages: z.array(PassageSchema),
  events: z.array(EventRecordSchema),
  claims: z.array(ClaimSchema),
  relationships: z.array(RelationshipSchema),
  knownAtTimes: z.array(KnownAtTimeSchema),
  narrativeBlocks: z.array(NarrativeBlockSchema).min(1),
  mapLayer: HistoricalMapLayerSchema.optional(),
})
export type Scene = z.infer<typeof SceneSchema>

export { DISPLAYABLE_CURATION_STATUSES }
