import type { HistoricalDate } from './schema'
import { historicalDateLowerKey, historicalDateUpperKey } from './schema'

/**
 * Renders a HistoricalDate honestly: precision is stated in the label, never
 * flattened into a bare date that implies more certainty than the record has
 * (AGENTS.md §3/§12). Era-capable (ADR-005): a bound with no CE calendar date
 * is rendered from its signed astronomical year ("44 BC", "9").
 */
function renderBound(iso: string | undefined, year: number): string {
  if (iso !== undefined) return iso
  return year >= 1 ? String(year) : `${1 - year} BC`
}

export function formatHistoricalDate(date: HistoricalDate): string {
  if (date.label) return date.label

  const lo = renderBound(date.earliest, historicalDateLowerKey(date)[0])
  const hi = renderBound(date.latest, historicalDateUpperKey(date)[0])

  switch (date.precision) {
    case 'exact':
      return lo
    case 'approximate':
      return `approximately ${lo}`
    case 'range':
      return `${lo} – ${hi}`
    case 'disputed':
      return `disputed: ${lo} – ${hi}`
  }
}
