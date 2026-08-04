import type { Scene } from './schema'
import type { FocusValue } from './focus'
import { formatHistoricalDate } from './formatHistoricalDate'

/** Human-readable label for the current Focus, used by the live-status region. */
export function describeFocus(focus: FocusValue, scene: Scene): string {
  switch (focus.kind) {
    case 'scene':
      return `Showing the whole scene: ${scene.title}`
    case 'event': {
      const event = scene.events.find((e) => e.id === focus.eventId)
      return event
        ? `Showing: ${event.title} (${formatHistoricalDate(event.eventTime)})`
        : 'Showing: an unknown event'
    }
    case 'claim': {
      const claim = scene.claims.find((candidate) => candidate.id === focus.claimId)
      return claim ? `Showing claim: ${claim.statement}` : 'Showing: an unknown claim'
    }
    case 'relationship': {
      const relationship = scene.relationships.find(
        (candidate) => candidate.id === focus.relationshipId,
      )
      return relationship
        ? `Showing relationship: ${relationship.relationshipType}`
        : 'Showing: an unknown relationship'
    }
    case 'source': {
      const source = scene.sources.find((candidate) => candidate.id === focus.sourceId)
      return source ? `Showing source: ${source.title}` : 'Showing: an unknown source'
    }
    case 'passage': {
      const passage = scene.passages.find(
        (candidate) => candidate.id === focus.passageId,
      )
      return passage
        ? `Showing passage: ${passage.locator}`
        : 'Showing: an unknown passage'
    }
    case 'entity': {
      const entity = scene.entities.find((e) => e.id === focus.entityId)
      return entity
        ? `Showing: ${entity.canonicalName}`
        : 'Showing: an unknown selection'
    }
    case 'timeRange':
      return `Showing time range: ${formatHistoricalDate(focus.range)}`
  }
}
