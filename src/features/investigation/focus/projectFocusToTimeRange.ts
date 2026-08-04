import type { HistoricalDate, Scene } from '../model/schema'
import type { FocusValue } from '../model/focus'

/**
 * Projects any Focus onto a time range for timeline/map filtering, per the
 * "time-range vs. point focus" rule in docs/design/map-timeline-graph-sync.md:
 * scene focus implies its scene's date range even though the user set no
 * explicit range. Event/entity focus (no independent temporal record yet at
 * Plan 3 scope) falls back to the current scene's range, not an unbounded one.
 */
export function projectFocusToTimeRange(
  focus: FocusValue,
  scene: Scene,
): HistoricalDate {
  if (focus.kind === 'timeRange') {
    return focus.range
  }
  return scene.dateRange
}
