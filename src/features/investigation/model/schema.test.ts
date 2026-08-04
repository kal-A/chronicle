import { describe, expect, it } from 'vitest'
import {
  ClaimSchema,
  RelationshipSchema,
  HistoricalDateSchema,
  LocationPrecisionSchema,
  SourceSchema,
  HistoricalMapLayerSchema,
} from './schema'

const validPassageId = 'passage-1'

describe('ClaimSchema', () => {
  it('rejects a claim with no EvidenceLinks', () => {
    const result = ClaimSchema.safeParse({
      id: 'c1',
      statement: 'Something happened.',
      directOrInferred: 'direct',
      reviewStatus: 'proposed',
      evidenceLinks: [],
    })
    expect(result.success).toBe(false)
  })

  it('rejects a claim whose only EvidenceLink is not "supporting"', () => {
    const result = ClaimSchema.safeParse({
      id: 'c1',
      statement: 'Something happened.',
      directOrInferred: 'direct',
      reviewStatus: 'proposed',
      evidenceLinks: [{ passageId: validPassageId, role: 'context' }],
    })
    expect(result.success).toBe(false)
  })

  it('accepts a claim with a supporting EvidenceLink', () => {
    const result = ClaimSchema.safeParse({
      id: 'c1',
      statement: 'Something happened.',
      directOrInferred: 'direct',
      reviewStatus: 'proposed',
      evidenceLinks: [{ passageId: validPassageId, role: 'supporting' }],
    })
    expect(result.success).toBe(true)
  })
})

describe('RelationshipSchema', () => {
  const base = {
    id: 'r1',
    relationshipType: 'causal-influence',
    fromId: 'a',
    toId: 'b',
    directOrInferred: 'inferred' as const,
  }

  it('rejects a relationship with no evidenceClassification', () => {
    const result = RelationshipSchema.safeParse({
      ...base,
      evidenceLinks: [{ passageId: validPassageId, role: 'supporting' }],
    })
    expect(result.success).toBe(false)
  })

  it('rejects a directly_supported relationship with no supporting EvidenceLink', () => {
    const result = RelationshipSchema.safeParse({
      ...base,
      evidenceClassification: 'directly_supported',
      evidenceLinks: [{ passageId: validPassageId, role: 'context' }],
    })
    expect(result.success).toBe(false)
  })

  it('rejects a disputed relationship missing a counterevidence link', () => {
    const result = RelationshipSchema.safeParse({
      ...base,
      evidenceClassification: 'disputed',
      evidenceLinks: [{ passageId: validPassageId, role: 'supporting' }],
    })
    expect(result.success).toBe(false)
  })

  it('accepts a disputed relationship with both supporting and counterevidence links', () => {
    const result = RelationshipSchema.safeParse({
      ...base,
      evidenceClassification: 'disputed',
      evidenceLinks: [
        { passageId: validPassageId, role: 'supporting' },
        { passageId: 'passage-2', role: 'counterevidence' },
      ],
    })
    expect(result.success).toBe(true)
  })
})

describe('HistoricalDateSchema', () => {
  it('rejects earliest after latest', () => {
    const result = HistoricalDateSchema.safeParse({
      precision: 'range',
      earliest: '1914-07-10',
      latest: '1914-07-05',
    })
    expect(result.success).toBe(false)
  })

  it('rejects an "exact" date whose earliest and latest differ', () => {
    const result = HistoricalDateSchema.safeParse({
      precision: 'exact',
      earliest: '1914-07-05',
      latest: '1914-07-06',
    })
    expect(result.success).toBe(false)
  })

  it('accepts a valid exact date', () => {
    const result = HistoricalDateSchema.safeParse({
      precision: 'exact',
      earliest: '1914-07-05',
      latest: '1914-07-05',
    })
    expect(result.success).toBe(true)
  })
})

describe('LocationPrecisionSchema', () => {
  it('rejects an invalid precision value', () => {
    const result = LocationPrecisionSchema.safeParse('street')
    expect(result.success).toBe(false)
  })

  it('accepts the four defined precision values', () => {
    for (const value of ['building', 'city', 'region', 'approximate']) {
      expect(LocationPrecisionSchema.safeParse(value).success).toBe(true)
    }
  })
})

describe('SourceSchema', () => {
  it('accepts a Source with no investigation reference and full temporal/geographic-adjacent coverage', () => {
    const result = SourceSchema.safeParse({
      id: 'jc-src-099',
      title: 'An unassigned source',
      sourceType: 'primary-official-diplomatic',
      authorOrOrigin: 'Unknown chancellery clerk',
      dateOfSource: { precision: 'exact', earliest: '1914-07-06', latest: '1914-07-06' },
      originalLanguage: 'German',
      rightsStatus: 'unknown',
      curationStatus: 'identified',
      knownLimitations: 'Not yet acquired.',
      linkOrLocation: 'archive-catalog-reference',
    })
    expect(result.success).toBe(true)
    // Confirms the schema has no investigationId field at all — a Source
    // cannot be required to belong to an Investigation (docs/architecture/domain-model.md).
    expect(result.data && 'investigationId' in result.data).toBe(false)
  })
})

describe('HistoricalMapLayerSchema', () => {
  const validLayer = {
    imagePath: '/maps/july-crisis/shepherd-europe-1911.jpg',
    bounds: {
      topLeft: { lat: 72, lng: -30 },
      topRight: { lat: 72, lng: 75 },
      bottomRight: { lat: 33, lng: 75 },
      bottomLeft: { lat: 33, lng: -30 },
    },
    defaultView: { center: { lat: 50.3, lng: 14.9 }, zoom: 4.3 },
    periodLabel: 'Europe, 1911–1914',
    sourceCitation: 'Shepherd, Historical Atlas (1911), pp. 166–167.',
    attribution: 'Perry–Castañeda Library Map Collection',
    license: 'Public domain (US publication, 1911)',
    georeferencingNote: 'Approximate rectangular fit from the plate\'s printed graticule.',
  }

  it('accepts a fully-specified historical map layer', () => {
    expect(HistoricalMapLayerSchema.safeParse(validLayer).success).toBe(true)
  })

  it('rejects a map layer missing a disclosed georeferencing note', () => {
    const { georeferencingNote: _omit, ...withoutNote } = validLayer
    expect(HistoricalMapLayerSchema.safeParse(withoutNote).success).toBe(false)
  })

  it('rejects a map layer missing bound corners', () => {
    const { bounds: _omit, ...withoutBounds } = validLayer
    expect(HistoricalMapLayerSchema.safeParse(withoutBounds).success).toBe(false)
  })
})
