import type { HistoricalDate } from './schema'

/**
 * Renders a HistoricalDate honestly: precision is stated in the label, never
 * flattened into a bare date that implies more certainty than the record has
 * (AGENTS.md §3/§12).
 */
export function formatHistoricalDate(date: HistoricalDate): string {
  if (date.label) return date.label

  switch (date.precision) {
    case 'exact':
      return date.earliest
    case 'approximate':
      return `approximately ${date.earliest}`
    case 'range':
      return `${date.earliest} – ${date.latest}`
    case 'disputed':
      return `disputed: ${date.earliest} – ${date.latest}`
  }
}
