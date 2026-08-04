import goldenInvestigationJson from '../../fixtures/blank-cheque.golden-investigation.json'
import concertOfEuropeInvestigationJson from '../../fixtures/concert-of-europe.generated-investigation.json'
import {
  validateGeneratedInvestigation,
  type GeneratedInvestigation,
} from '../features/investigation/model/generatedInvestigation'

export const EMPTY_INVESTIGATION_PACKAGE_ID = 'fixture-empty-investigation'

interface FixtureRegistration {
  investigation: GeneratedInvestigation
  isDefault: boolean
}

function makeEmptyInvestigation(
  source: GeneratedInvestigation,
): GeneratedInvestigation {
  const defaultSceneId = source.interactionSpec.defaultSceneId
  const placeholder = {
    id: 'narrative-empty-placeholder',
    order: 0,
    text: 'No reviewed or prototype-curated content is available for this investigation yet.',
    isMaterialAssertion: false,
    referencedRecordIds: [],
  }

  return validateGeneratedInvestigation({
    ...source,
    packageId: EMPTY_INVESTIGATION_PACKAGE_ID,
    packageRevision: 1,
    status: 'partial',
    request: {
      ...source.request,
      id: 'request-empty-investigation',
      rawInput: 'Fixture for an investigation with no usable content.',
    },
    presentation: {
      ...source.presentation,
      title: 'Empty investigation fixture',
      synthesis: [placeholder],
      findings: [],
    },
    events: [],
    decisions: [],
    communications: [],
    knowledgeStates: [],
    claims: [],
    relationships: [],
    perspectives: [],
    conflicts: [],
    uncertainties: [],
    researchGaps: [],
    sources: [],
    documents: [],
    passages: [],
    evidenceLinks: [],
    claimLedgers: [],
    timeline: [],
    scenes: source.scenes.map((scene) => ({
      ...scene,
      title: 'Empty Scene (fixture for the no-content state)',
      sourceIds: [],
      documentIds: [],
      passageIds: [],
      eventIds: [],
      claimIds: [],
      relationshipIds: [],
      knowledgeStateIds: [],
      narrativeBlockIds: [placeholder.id],
    })),
    interactionSpec: {
      ...source.interactionSpec,
      defaultSceneId,
      omittedCapabilities: [
        ...source.interactionSpec.omittedCapabilities,
        'reviewed historical content',
      ],
    },
    generationReport: {
      outcome: 'partial',
      stages: [{ id: 'empty-state-fixture', status: 'partial' }],
      omissions: ['No evidence-backed historical records are available.'],
      warnings: ['This package exists only to exercise the empty-content state.'],
      verificationChecks: [
        {
          id: 'empty-state-honesty',
          status: 'abstained',
          message: 'No historical assertions were generated or displayed.',
        },
      ],
    },
  })
}

const goldenInvestigation = validateGeneratedInvestigation(
  goldenInvestigationJson,
)

// Generated end-to-end by the Python pipeline's curated (not mock) provider
// set — see backend/src/chronicle/providers/curated/concert_of_europe/ and
// plans/current-phase.md's Phase C3 section. Registering it here, alongside
// the hand-authored golden fixture, is what proves the generic renderer has
// no hidden coupling to blank-cheque's specific content.
const concertOfEuropeInvestigation = validateGeneratedInvestigation(
  concertOfEuropeInvestigationJson,
)

export const investigationFixtures: FixtureRegistration[] = [
  { investigation: goldenInvestigation, isDefault: true },
  { investigation: concertOfEuropeInvestigation, isDefault: false },
  { investigation: makeEmptyInvestigation(goldenInvestigation), isDefault: false },
]
