import { z } from 'zod'
import { HistoricalDateSchema } from './schema'

/**
 * Shared focus contract from docs/design/map-timeline-graph-sync.md.
 * One value drives every facet (narrative/timeline/map/graph/evidence).
 * `source` tags who caused the update so a facet can skip reacting to a
 * focus change it just caused itself (the feedback-loop rule).
 */

export const FocusSourceSchema = z.enum([
  'narrative',
  'timeline',
  'map',
  'graph',
  'evidence',
  'url',
])
export type FocusSource = z.infer<typeof FocusSourceSchema>

export const FocusValueSchema = z.discriminatedUnion('kind', [
  z.object({ kind: z.literal('scene'), sceneId: z.string().min(1) }),
  z.object({ kind: z.literal('event'), eventId: z.string().min(1) }),
  z.object({ kind: z.literal('claim'), claimId: z.string().min(1) }),
  z.object({
    kind: z.literal('relationship'),
    relationshipId: z.string().min(1),
  }),
  z.object({ kind: z.literal('source'), sourceId: z.string().min(1) }),
  z.object({ kind: z.literal('passage'), passageId: z.string().min(1) }),
  z.object({
    kind: z.literal('entity'),
    entityId: z.string().min(1),
    entityType: z.enum(['person', 'place']),
  }),
  z.object({
    kind: z.literal('timeRange'),
    range: HistoricalDateSchema,
  }),
])
export type FocusValue = z.infer<typeof FocusValueSchema>

export interface FocusUpdate {
  focus: FocusValue
  source: FocusSource
}
