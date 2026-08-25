import { describe, expect, it } from 'vitest'
import { ATLANTIC_LABELS, ATLANTIC_VIEW } from './atlasGeography'
import { resolveAtlasDrawStages } from './atlasDrawStages'

describe('AtlanticAtlas cartographic labels', () => {
  it('keeps the physical-feature spellings reviewed for the homepage', () => {
    expect(ATLANTIC_LABELS.map((label) => label.name)).toEqual([
      'North Atlantic Ocean',
      'Caribbean Sea',
    ])
  })

  it('places the Caribbean Sea label inside the central Caribbean basin', () => {
    const caribbean = ATLANTIC_LABELS.find((label) => label.name === 'Caribbean Sea')
    expect(caribbean).toEqual({ name: 'Caribbean Sea', longitude: -75, latitude: 15 })
    expect(caribbean!.longitude).toBeGreaterThan(-89)
    expect(caribbean!.longitude).toBeLessThan(-60)
    expect(caribbean!.latitude).toBeGreaterThan(9)
    expect(caribbean!.latitude).toBeLessThan(23)
  })

  it('keeps every physical label inside the declared Atlantic viewport', () => {
    for (const label of ATLANTIC_LABELS) {
      expect(label.longitude).toBeGreaterThan(ATLANTIC_VIEW.west)
      expect(label.longitude).toBeLessThan(ATLANTIC_VIEW.east)
      expect(label.latitude).toBeGreaterThan(ATLANTIC_VIEW.south)
      expect(label.latitude).toBeLessThan(ATLANTIC_VIEW.north)
    }
  })
})

describe('AtlanticAtlas authored draw sequence', () => {
  it('starts with no cartographic geometry or instruments visible', () => {
    expect(resolveAtlasDrawStages(0)).toEqual({
      coastline: 0,
      graticule: 0,
      labels: 0,
      instruments: 0,
      settledInk: 0,
    })
  })

  it('draws coastline before adding orientation furniture', () => {
    const stages = resolveAtlasDrawStages(0.5)

    expect(stages.coastline).toBe(0.5)
    expect(stages.graticule).toBeGreaterThan(0)
    expect(stages.labels).toBe(0)
    expect(stages.instruments).toBe(0)
    expect(stages.settledInk).toBe(0)
  })

  it('finishes with every cartographic layer resolved', () => {
    expect(resolveAtlasDrawStages(1)).toEqual({
      coastline: 1,
      graticule: 1,
      labels: 1,
      instruments: 1,
      settledInk: 1,
    })
  })
})
