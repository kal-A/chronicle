import type { Scene } from '../model/schema'
import type { FocusValue } from '../model/focus'
import { formatHistoricalDate } from '../model/formatHistoricalDate'

/**
 * Keyboard-navigable, ordered list of Events (docs/design/accessibility.md —
 * every marker has an accessible name including date and title, not a bare
 * visual dot). Selecting an event sets Focus with source: 'timeline'.
 */
export function TimelineView({
  scene,
  focus,
  onSelectFocus,
  eventIds,
}: {
  scene: Scene
  focus: FocusValue
  onSelectFocus: (focus: FocusValue) => void
  /** Phase D workspace: restrict to the active lens's visible events. Omitted (Inspector) shows every event in the scene, unchanged. */
  eventIds?: Set<string>
}) {
  const events = [...scene.events]
    .filter((event) => !eventIds || eventIds.has(event.id))
    .sort((a, b) => (a.eventTime.earliest < b.eventTime.earliest ? -1 : 1))

  if (events.length === 0) {
    return (
      <p className="chronicle-timeline-empty">
        No events are available for this scene yet.
      </p>
    )
  }

  return (
    <nav aria-label="Timeline of events in this scene">
      <ol className="chronicle-timeline-list">
        {events.map((event) => {
          const isFocused = focus.kind === 'event' && focus.eventId === event.id
          return (
            <li key={event.id}>
              <button
                type="button"
                aria-current={isFocused ? 'true' : undefined}
                className={`chronicle-timeline-event ${isFocused ? 'is-focused' : ''}`}
                onClick={() => onSelectFocus({ kind: 'event', eventId: event.id })}
              >
                <span className="chronicle-timeline-date">
                  {formatHistoricalDate(event.eventTime)}
                </span>
                <span>{event.title}</span>
              </button>
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
