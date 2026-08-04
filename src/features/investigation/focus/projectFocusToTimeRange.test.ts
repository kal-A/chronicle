import { describe, expect, it } from 'vitest'
import goldenInvestigation from '../../../../fixtures/blank-cheque.golden-investigation.json'
import { validateGeneratedInvestigation } from '../model/generatedInvestigation'
import { normalizeInvestigationScene } from '../model/normalizeInvestigation'
import { projectFocusToTimeRange } from './projectFocusToTimeRange'

const investigation = validateGeneratedInvestigation(goldenInvestigation)
const scene2BlankCheque = normalizeInvestigationScene(
  investigation,
  investigation.interactionSpec.defaultSceneId,
)

describe('projectFocusToTimeRange', () => {
  it('projects scene focus onto the scene’s own date range', () => {
    const result = projectFocusToTimeRange(
      { kind: 'scene', sceneId: scene2BlankCheque.id },
      scene2BlankCheque,
    )
    expect(result).toEqual(scene2BlankCheque.dateRange)
  })

  it('projects entity focus onto the current scene’s date range (no independent temporal record yet)', () => {
    const result = projectFocusToTimeRange(
      { kind: 'entity', entityId: 'person-wilhelm-ii', entityType: 'person' },
      scene2BlankCheque,
    )
    expect(result).toEqual(scene2BlankCheque.dateRange)
  })

  it('passes an explicit timeRange focus through unchanged', () => {
    const range = {
      precision: 'exact' as const,
      earliest: '1914-07-05',
      latest: '1914-07-05',
    }
    const result = projectFocusToTimeRange(
      { kind: 'timeRange', range },
      scene2BlankCheque,
    )
    expect(result).toEqual(range)
  })
})
