import { FocusValueSchema, type FocusValue } from '../model/focus'

/**
 * Deterministic Focus <-> URL search-parameter serialization
 * (docs/design/map-timeline-graph-sync.md). Encoding is pure and total.
 * Decoding is defensive: any structurally invalid or unparseable value
 * resolves to `null` rather than throwing, so an unknown/garbled URL falls
 * back to the caller's default focus instead of crashing the app.
 */

const FOCUS_PARAM = 'focus'

export function encodeFocus(focus: FocusValue): URLSearchParams {
  const params = new URLSearchParams()
  params.set(FOCUS_PARAM, focus.kind)

  switch (focus.kind) {
    case 'scene':
      params.set('sceneId', focus.sceneId)
      break
    case 'event':
      params.set('eventId', focus.eventId)
      break
    case 'claim':
      params.set('claimId', focus.claimId)
      break
    case 'relationship':
      params.set('relationshipId', focus.relationshipId)
      break
    case 'source':
      params.set('sourceId', focus.sourceId)
      break
    case 'passage':
      params.set('passageId', focus.passageId)
      break
    case 'entity':
      params.set('entityId', focus.entityId)
      params.set('entityType', focus.entityType)
      break
    case 'timeRange':
      params.set('rangePrecision', focus.range.precision)
      params.set('rangeEarliest', focus.range.earliest)
      params.set('rangeLatest', focus.range.latest)
      if (focus.range.label) params.set('rangeLabel', focus.range.label)
      break
  }

  return params
}

export function decodeFocus(
  params: URLSearchParams,
): FocusValue | null {
  const kind = params.get(FOCUS_PARAM)
  if (!kind) return null

  let candidate: unknown
  switch (kind) {
    case 'scene': {
      const sceneId = params.get('sceneId')
      if (!sceneId) return null
      candidate = { kind: 'scene', sceneId }
      break
    }
    case 'event': {
      const eventId = params.get('eventId')
      if (!eventId) return null
      candidate = { kind: 'event', eventId }
      break
    }
    case 'claim': {
      const claimId = params.get('claimId')
      if (!claimId) return null
      candidate = { kind: 'claim', claimId }
      break
    }
    case 'relationship': {
      const relationshipId = params.get('relationshipId')
      if (!relationshipId) return null
      candidate = { kind: 'relationship', relationshipId }
      break
    }
    case 'source': {
      const sourceId = params.get('sourceId')
      if (!sourceId) return null
      candidate = { kind: 'source', sourceId }
      break
    }
    case 'passage': {
      const passageId = params.get('passageId')
      if (!passageId) return null
      candidate = { kind: 'passage', passageId }
      break
    }
    case 'entity': {
      const entityId = params.get('entityId')
      const entityType = params.get('entityType')
      if (!entityId || !entityType) return null
      candidate = { kind: 'entity', entityId, entityType }
      break
    }
    case 'timeRange': {
      const precision = params.get('rangePrecision')
      const earliest = params.get('rangeEarliest')
      const latest = params.get('rangeLatest')
      const label = params.get('rangeLabel') ?? undefined
      if (!precision || !earliest || !latest) return null
      candidate = {
        kind: 'timeRange',
        range: { precision, earliest, latest, label },
      }
      break
    }
    default:
      return null
  }

  const result = FocusValueSchema.safeParse(candidate)
  return result.success ? result.data : null
}
