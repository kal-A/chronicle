import { describe, expect, it } from 'vitest'
import {
  activeControlStates,
  historicalYear,
  polityColorIndex,
  territoryFeatureCollections,
  territoryLegend,
} from './territory'
import type { ControlState, TerritoryGeometry } from '../model/generatedInvestigation'
import type { HistoricalDate } from '../model/schema'

function date(earliest: string, latest: string, label?: string): HistoricalDate {
  return { precision: 'range', earliest, latest, ...(label ? { label } : {}) } as unknown as HistoricalDate
}

// A BC interval (ADR-005): signed astronomical years, no calendar date. e.g.
// 218 BC = year -217. Chronicle stores the signed year, not the label.
function bcDate(earliestYear: number, latestYear: number, label?: string): HistoricalDate {
  return { precision: 'range', earliestYear, latestYear, ...(label ? { label } : {}) } as unknown as HistoricalDate
}

function control(
  id: string,
  polity: string,
  kind: ControlState['kind'],
  geometryRef: string,
  from: HistoricalDate,
  to: HistoricalDate,
  extra: Partial<ControlState> = {},
): ControlState {
  return {
    id,
    polity,
    kind,
    geometryRef,
    validFrom: from,
    validTo: to,
    precision: 'region',
    evidenceLinkIds: ['e1'],
    reviewStatus: 'proposed',
    visibility: 'public',
    ...extra,
  } as unknown as ControlState
}

function geometry(id: string, attestedYear: number): TerritoryGeometry {
  return {
    id,
    type: 'Polygon',
    coordinates: [[[0, 0], [1, 0], [1, 1], [0, 0]]],
    sourceDataset: 'historical-basemaps',
    attestedYear,
    license: 'GPL-3.0',
  } as unknown as TerritoryGeometry
}

describe('polityColorIndex', () => {
  it('assigns a stable colour index by first appearance', () => {
    const span = date('1900-01-01', '1900-12-31')
    const idx = polityColorIndex([
      control('c1', 'Rome', 'controlled', 'g1', span, span),
      control('c2', 'Carthage', 'influence', 'g2', span, span),
      control('c3', 'Rome', 'controlled', 'g3', span, span),
    ])
    expect(idx.get('Rome')).toBe(0)
    expect(idx.get('Carthage')).toBe(1)
  })
})

describe('historicalYear', () => {
  it('reads the signed astronomical year for BC dates', () => {
    // 218 BC = year -217; the field is the source of truth, not the label.
    expect(historicalYear(bcDate(-217, -201, '218–202 BC'), 'start')).toBe(-217)
    expect(historicalYear(bcDate(-217, -201, '218–202 BC'), 'end')).toBe(-201)
  })
  it('reads the ISO year for CE dates', () => {
    expect(historicalYear(date('1914-06-28', '1914-08-04'), 'start')).toBe(1914)
  })
  it('falls back to a legacy BC label when no field or date is present', () => {
    expect(historicalYear({ precision: 'range', label: '44 BC' } as unknown as HistoricalDate, 'start')).toBe(-43)
  })
  it('returns null for an empty date', () => {
    expect(historicalYear(undefined, 'start')).toBeNull()
  })
})

describe('activeControlStates', () => {
  const states = [
    control('a', 'Rome', 'controlled', 'g1', date('1900-01-01', '1900-12-31'), date('1910-12-31', '1910-12-31')),
    control('b', 'Gaul', 'controlled', 'g2', date('1920-01-01', '1920-12-31'), date('1930-12-31', '1930-12-31')),
  ]
  it('keeps only states whose interval contains the year', () => {
    expect(activeControlStates(states, 1905).map((s) => s.id)).toEqual(['a'])
    expect(activeControlStates(states, 1925).map((s) => s.id)).toEqual(['b'])
    expect(activeControlStates(states, 1915)).toEqual([])
  })
  it('returns everything when there is no cursor', () => {
    expect(activeControlStates(states, null)).toHaveLength(2)
  })
})

describe('territoryFeatureCollections', () => {
  const geometries = [geometry('g1', 1900), geometry('g2', 1900)]
  const states = [
    control('a', 'Rome', 'controlled', 'g1', date('1900-01-01', '1900-12-31'), date('1930-12-31', '1930-12-31')),
    control('b', 'Carthage', 'influence', 'g2', date('1900-01-01', '1900-12-31'), date('1930-12-31', '1930-12-31')),
    control('c', 'Rome', 'controlled', 'gMISSING', date('1900-01-01', '1900-12-31'), date('1930-12-31', '1930-12-31')),
  ]
  const idx = polityColorIndex(states)

  it('splits into control/influence bands, joining sourced geometry', () => {
    const fc = territoryFeatureCollections(states, geometries, 1910, idx)
    expect(fc.control.features).toHaveLength(1)
    expect(fc.influence.features).toHaveLength(1)
    expect((fc.control.features[0].properties as { polity: string }).polity).toBe('Rome')
  })

  it('drops a control state whose geometryRef does not resolve', () => {
    const fc = territoryFeatureCollections(states, geometries, 1910, idx)
    const ids = fc.control.features.map((f) => (f.properties as { id: string }).id)
    expect(ids).not.toContain('c') // gMISSING -> omitted, never fabricated
  })

  it('gives a contested band the second claimant colour for the stripe', () => {
    const contestedStates = [
      control('x', 'Rome', 'contested', 'gShared', date('1900-01-01', '1900-12-31'), date('1930-12-31', '1930-12-31')),
      control('y', 'Carthage', 'contested', 'gShared', date('1900-01-01', '1900-12-31'), date('1930-12-31', '1930-12-31')),
    ]
    const ci = polityColorIndex(contestedStates)
    const fc = territoryFeatureCollections(contestedStates, [geometry('gShared', 1900)], 1910, ci)
    expect(fc.contested.features.length).toBeGreaterThan(0)
    const props = fc.contested.features[0].properties as { colorIndex: number; otherColorIndex: number }
    expect(props.otherColorIndex).not.toBe(props.colorIndex)
  })
})

describe('territoryLegend', () => {
  it('lists active polities and which bands are present', () => {
    const states = [
      control('a', 'Rome', 'controlled', 'g1', date('1900-01-01', '1900-12-31'), date('1930-12-31', '1930-12-31')),
      control('b', 'Carthage', 'influence', 'g2', date('1900-01-01', '1900-12-31'), date('1930-12-31', '1930-12-31')),
    ]
    const legend = territoryLegend(states, 1910, polityColorIndex(states))
    expect(legend.polities.map((p) => p.polity)).toEqual(['Rome', 'Carthage'])
    expect(legend.hasControl).toBe(true)
    expect(legend.hasInfluence).toBe(true)
    expect(legend.hasContested).toBe(false)
  })
})
