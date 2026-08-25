import type { EventRecord } from '../model/schema'
import { formatHistoricalDate } from '../model/formatHistoricalDate'

function ArrowIcon({ direction }: { direction: 'previous' | 'next' }) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d={direction === 'previous' ? 'm14.5 6-6 6 6 6' : 'm9.5 6 6 6-6 6'} />
    </svg>
  )
}

export function TemporalMapRail({
  events,
  selectedIndex,
  onSelectIndex,
}: {
  events: EventRecord[]
  selectedIndex: number
  onSelectIndex: (index: number) => void
}) {
  if (events.length === 0) {
    return (
      <section className="chronicle-time-rail chronicle-time-rail--empty" aria-label="Investigation time">
        No dated events are available for this lens.
      </section>
    )
  }

  const boundedIndex = Math.min(events.length - 1, Math.max(0, selectedIndex))
  const activeEvent = events[boundedIndex]

  return (
    <section className="chronicle-time-rail" aria-label="Investigation time">
      <div className="chronicle-time-rail__reading" aria-live="polite">
        <span>Time</span>
        <strong>{formatHistoricalDate(activeEvent.eventTime)}</strong>
        <p>{activeEvent.title}</p>
      </div>

      <div className="chronicle-time-rail__control">
        <button
          type="button"
          aria-label="Previous event"
          disabled={boundedIndex === 0}
          onClick={() => onSelectIndex(boundedIndex - 1)}
        >
          <ArrowIcon direction="previous" />
        </button>
        <div>
          <input
            type="range"
            min="0"
            max={events.length - 1}
            step="1"
            value={boundedIndex}
            aria-label="Historical event position"
            aria-valuetext={`${formatHistoricalDate(activeEvent.eventTime)}: ${activeEvent.title}`}
            onChange={(event) => onSelectIndex(Number(event.target.value))}
          />
          <div className="chronicle-time-rail__range" aria-hidden="true">
            <span>{formatHistoricalDate(events[0].eventTime)}</span>
            <span>{formatHistoricalDate(events[events.length - 1].eventTime)}</span>
          </div>
        </div>
        <button
          type="button"
          aria-label="Next event"
          disabled={boundedIndex === events.length - 1}
          onClick={() => onSelectIndex(boundedIndex + 1)}
        >
          <ArrowIcon direction="next" />
        </button>
      </div>
    </section>
  )
}
