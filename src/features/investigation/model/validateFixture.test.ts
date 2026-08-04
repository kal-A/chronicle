import { describe, expect, it } from 'vitest'
import goldenInvestigation from '../../../../fixtures/blank-cheque.golden-investigation.json'
import { validateGeneratedInvestigation } from './generatedInvestigation'
import { normalizeInvestigationScene } from './normalizeInvestigation'
import { FixtureValidationError, validateFixture } from './validateFixture'

const investigation = validateGeneratedInvestigation(goldenInvestigation)
const scene2BlankCheque = normalizeInvestigationScene(
  investigation,
  investigation.interactionSpec.defaultSceneId,
)

describe('validateFixture', () => {
  it('accepts the real Scene 2 fixture', () => {
    expect(() => validateFixture(scene2BlankCheque)).not.toThrow()
  })

  it('rejects a material NarrativeBlock referencing an unknown record id', () => {
    const broken = {
      ...scene2BlankCheque,
      narrativeBlocks: [
        {
          id: 'nb-broken',
          order: 0,
          text: 'An unsupported assertion.',
          isMaterialAssertion: true,
          referencedRecordIds: ['claim-does-not-exist'],
        },
      ],
    }
    expect(() => validateFixture(broken)).toThrow(FixtureValidationError)
  })

  it('rejects a Document referencing an unknown Source', () => {
    const broken = {
      ...scene2BlankCheque,
      documents: [
        {
          id: 'doc-orphan',
          sourceId: 'source-does-not-exist',
          editionCitation: 'n/a',
          visibility: 'public',
          knownLimitations: 'n/a',
        },
      ],
    }
    expect(() => validateFixture(broken)).toThrow(FixtureValidationError)
  })

  it('rejects a Claim EvidenceLink referencing an unknown Passage', () => {
    const broken = {
      ...scene2BlankCheque,
      claims: [
        {
          id: 'claim-broken',
          statement: 'x',
          directOrInferred: 'direct',
          reviewStatus: 'proposed',
          evidenceLinks: [{ passageId: 'passage-does-not-exist', role: 'supporting' }],
        },
      ],
      narrativeBlocks: [
        {
          id: 'nb-1',
          order: 0,
          text: 'x',
          isMaterialAssertion: false,
          referencedRecordIds: [],
        },
      ],
    }
    expect(() => validateFixture(broken)).toThrow(FixtureValidationError)
  })

  it('rejects a Scene whose placeIds reference an unknown Place entity', () => {
    const broken = {
      ...scene2BlankCheque,
      placeIds: ['place-does-not-exist'],
    }
    expect(() => validateFixture(broken)).toThrow(FixtureValidationError)
  })
})
