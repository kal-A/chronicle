import { describe, expect, it } from 'vitest'
import { formatHistoricalDate } from './formatHistoricalDate'
import type { HistoricalDate } from './schema'

describe('formatHistoricalDate', () => {
  it('prefers the authored label when present', () => {
    const d = { precision: 'range', earliestYear: -218, latestYear: -201, label: '219–202 BC' }
    expect(formatHistoricalDate(d as HistoricalDate)).toBe('219–202 BC')
  })

  it('renders a labelless CE exact date as its ISO string', () => {
    const d = { precision: 'exact', earliest: '1914-07-05', latest: '1914-07-05' }
    expect(formatHistoricalDate(d as HistoricalDate)).toBe('1914-07-05')
  })

  it('renders a labelless BC range from signed years (ADR-005)', () => {
    // -218 = 219 BC, -201 = 202 BC.
    const d = { precision: 'range', earliestYear: -218, latestYear: -201 }
    expect(formatHistoricalDate(d as HistoricalDate)).toBe('219 BC – 202 BC')
  })

  it('renders a labelless BC exact date from its signed year', () => {
    const d = { precision: 'exact', earliestYear: -43, latestYear: -43 }
    expect(formatHistoricalDate(d as HistoricalDate)).toBe('44 BC')
  })
})
