import { describe, expect, it } from 'vitest'
import goldenInvestigation from '../../../../fixtures/blank-cheque.golden-investigation.json'
import { validateGeneratedInvestigation } from './generatedInvestigation'
import {
  InvestigationSceneNotFoundError,
  normalizeInvestigationScene,
} from './normalizeInvestigation'

describe('normalizeInvestigationScene', () => {
  const investigation = validateGeneratedInvestigation(goldenInvestigation)

  it('derives the existing Scene view from package references', () => {
    const scene = normalizeInvestigationScene(
      investigation,
      'scene-2-blank-cheque',
    )

    expect(scene.title).toBe('Vienna and Berlin: The Blank Cheque')
    expect(scene.claims).toHaveLength(4)
    expect(scene.events).toHaveLength(3)
    expect(scene.narrativeBlocks).toHaveLength(6)
    expect(scene.mapLayer?.periodLabel).toMatch(/1911–1914/)
  })

  it('rehydrates canonical package evidence links for the Scene-facing facets', () => {
    const scene = normalizeInvestigationScene(
      investigation,
      'scene-2-blank-cheque',
    )
    const relationship = scene.relationships.find(
      (record) => record.id === 'rel-r1-assurance-enabled-posture',
    )

    expect(relationship?.evidenceLinks.map((link) => link.role)).toEqual([
      'supporting',
      'counterevidence',
    ])
    expect(relationship?.evidenceLinks[0].reviewerNote).toMatch(
      /Fischer-aligned reading/i,
    )
  })

  it('rejects a scene id that is not present in the package', () => {
    expect(() =>
      normalizeInvestigationScene(investigation, 'scene-does-not-exist'),
    ).toThrow(InvestigationSceneNotFoundError)
  })
})
