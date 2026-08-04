import { describe, expect, it } from 'vitest'
import type { FocusValue } from '../model/focus'
import { decodeFocus, encodeFocus } from './serialization'

describe('encodeFocus / decodeFocus round-trip', () => {
  const cases: FocusValue[] = [
    { kind: 'scene', sceneId: 'scene-2-blank-cheque' },
    { kind: 'event', eventId: 'event-1' },
    { kind: 'entity', entityId: 'person-wilhelm-ii', entityType: 'person' },
    { kind: 'entity', entityId: 'place-berlin', entityType: 'place' },
    { kind: 'claim', claimId: 'claim-1' },
    { kind: 'relationship', relationshipId: 'relationship-1' },
    { kind: 'source', sourceId: 'source-1' },
    { kind: 'passage', passageId: 'passage-1' },
    {
      kind: 'timeRange',
      range: { precision: 'range', earliest: '1914-07-04', latest: '1914-07-10' },
    },
    {
      kind: 'timeRange',
      range: {
        precision: 'exact',
        earliest: '1914-07-05',
        latest: '1914-07-05',
        label: 'the day of the assurance',
      },
    },
  ]

  for (const focus of cases) {
    it(`round-trips a "${focus.kind}" focus`, () => {
      const params = encodeFocus(focus)
      const decoded = decodeFocus(params)
      expect(decoded).toEqual(focus)
    })
  }
})

describe('decodeFocus invalid-URL handling', () => {
  it('returns null when there is no focus param at all', () => {
    expect(decodeFocus(new URLSearchParams())).toBeNull()
  })

  it('returns null for an unknown focus kind', () => {
    expect(decodeFocus(new URLSearchParams('focus=bogus'))).toBeNull()
  })

  it('returns null when a required field is missing (scene with no sceneId)', () => {
    expect(decodeFocus(new URLSearchParams('focus=scene'))).toBeNull()
  })

  it('returns null for an entity with an invalid entityType', () => {
    expect(
      decodeFocus(
        new URLSearchParams('focus=entity&entityId=x&entityType=spaceship'),
      ),
    ).toBeNull()
  })

  it('returns null for a timeRange with an invalid precision', () => {
    expect(
      decodeFocus(
        new URLSearchParams(
          'focus=timeRange&rangePrecision=bogus&rangeEarliest=1914-07-04&rangeLatest=1914-07-10',
        ),
      ),
    ).toBeNull()
  })

  it('returns null for a timeRange with earliest after latest', () => {
    expect(
      decodeFocus(
        new URLSearchParams(
          'focus=timeRange&rangePrecision=range&rangeEarliest=1914-07-10&rangeLatest=1914-07-04',
        ),
      ),
    ).toBeNull()
  })

  it('returns null for garbage query strings entirely unrelated to focus', () => {
    expect(decodeFocus(new URLSearchParams('utm_source=test&ref=abc'))).toBeNull()
  })
})
