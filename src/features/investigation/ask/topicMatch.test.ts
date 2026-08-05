import { describe, expect, it } from 'vitest'
import { investigationFixtures } from '../../../content/investigationFixtures'
import { matchInvestigationToQuestion } from './topicMatch'

const investigations = investigationFixtures.map((fixture) => fixture.investigation)

describe('matchInvestigationToQuestion', () => {
  it('matches the Concert of Europe package on a Troppau/intervention-flavored question', () => {
    const match = matchInvestigationToQuestion(
      'How did the Concert of Europe respond to revolutionary intervention at Troppau and Naples?',
      investigations,
    )
    expect(match?.packageId).toBe('concert-of-europe-1814-1822')
  })

  it('matches the blank-cheque package on a German-assurance/Austria-Hungary question', () => {
    const match = matchInvestigationToQuestion(
      'What did the German assurance to Austria-Hungary promise in July 1914?',
      investigations,
    )
    expect(match?.packageId).toBe('blank-cheque-golden')
  })

  it('returns null for a question unrelated to any curated investigation', () => {
    const match = matchInvestigationToQuestion(
      'What was the economic impact of the Meiji Restoration on Japanese silk exports?',
      investigations,
    )
    expect(match).toBeNull()
  })

  it('returns null for an empty question', () => {
    expect(matchInvestigationToQuestion('', investigations)).toBeNull()
  })

  it('ignores investigations without an experiencePlan', () => {
    const emptyOnly = investigations.filter(
      (investigation) => investigation.packageId === 'fixture-empty-investigation',
    )
    const match = matchInvestigationToQuestion(
      'How did the Concert of Europe respond to revolutionary intervention?',
      emptyOnly,
    )
    expect(match).toBeNull()
  })
})
