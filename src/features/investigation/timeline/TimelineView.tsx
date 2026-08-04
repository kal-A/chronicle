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
}: {
  scene: Scene
  focus: FocusValue
  onSelectFocus: (focus: FocusValue) => void
}) {
  const events = [...scene.events].sort(
    (a, b) => (a.eventTime.earliest < b.eventTime.earliest ? -1 : 1),
  )

  if (events.length === 0) {
    return (
      <p className="text-sm text-neutral-500 dark:text-neutral-400">
        No events are available for this scene yet.
      </p>
    )
  }

  return (
    <nav aria-label="Timeline of events in this scene">
      <ol className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
        {events.map((event) => {
          const isFocused = focus.kind === 'event' && focus.eventId === event.id
          return (
            <li key={event.id} className="sm:flex-1 sm:basis-48">
              <button
                type="button"
                aria-current={isFocused ? 'true' : undefined}
                className={`w-full rounded-lg border-l-4 border p-2 text-left text-sm transition-colors ${
                  isFocused
                    ? 'border-blue-600 bg-blue-50 font-semibold dark:bg-blue-950/40'
                    : 'border-l-transparent border-neutral-200 hover:bg-neutral-50 dark:border-neutral-800 dark:hover:bg-neutral-900'
                }`}
                onClick={() => onSelectFocus({ kind: 'event', eventId: event.id })}
              >
                <span className="block text-xs font-medium tracking-wide text-neutral-500 dark:text-neutral-400">
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
