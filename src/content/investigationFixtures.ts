import goldenInvestigationJson from '../../fixtures/blank-cheque.golden-investigation.json'
import concertOfEuropeInvestigationJson from '../../fixtures/concert-of-europe.generated-investigation.json'
import {
  validateGeneratedInvestigation,
  type GeneratedInvestigation,
} from '../features/investigation/model/generatedInvestigation'
import type { InvestigationExperiencePlan } from '../features/investigation/model/experiencePlan'

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
    // The empty fixture empties every record collection below — any
    // experiencePlan inherited from `source` would reference ids that no
    // longer exist. Dropping it also exercises resolveLenses()'s
    // synthesized-overview fallback for packages without a plan.
    experiencePlan: undefined,
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

/**
 * Blank-cheque has no generation pipeline behind it (it's the original
 * hand-authored golden fixture, migrated), so its InvestigationExperiencePlan
 * stays hand-authored here rather than baked into the on-disk JSON
 * (docs/decisions/ADR-002-map-first-workspace.md). Concert of Europe's plan
 * used to be hand-authored the same way in D0.3; as of D0.4 it is generated
 * by the curated pipeline's own experience_plan.py stage and is already part
 * of fixtures/concert-of-europe.generated-investigation.json — proving no
 * React branching is needed either way, since the workspace only ever reads
 * `investigation.experiencePlan`.
 */

const BLANK_CHEQUE_EXPERIENCE_PLAN: InvestigationExperiencePlan = {
  opening: {
    question: 'What did the German assurance to Austria-Hungary promise, and how was it used?',
    scopeSummary: 'Berlin and Vienna, 5-10 July 1914.',
    leadAnswer:
      'Germany assured Austria-Hungary of full support against Serbia; whether that assurance directly shaped Vienna’s subsequent posture is disputed, not settled.',
    evidenceCoverageSummary: 'Diplomatic dispatches and a marginal annotation, directly cited.',
  },
  workspace: {
    initialMapScope: {
      bounds: {
        topLeft: { lat: 72, lng: -30 },
        topRight: { lat: 72, lng: 75 },
        bottomRight: { lat: 33, lng: 75 },
        bottomLeft: { lat: 33, lng: -30 },
      },
      focusRegions: [{ id: 'region-central-europe', label: 'Central Europe' }],
      contextRegions: [],
      initialViewport: { center: { lat: 50.3, lng: 14.9 }, zoom: 4.3 },
      minimumZoom: 3,
      maximumZoom: 8,
      geographicRationale: 'Berlin and Vienna are the only two active locations in this investigation.',
      representedPeriod: { precision: 'range', earliest: '1914-07-05', latest: '1914-07-10' },
      unavailableHistoricalBoundaries: [],
      geographicLimitations: [],
    },
    initialLensId: 'lens-sequence',
    initialTimeRange: { precision: 'range', earliest: '1914-07-05', latest: '1914-07-10' },
    initialPanelTab: 'explore',
    defaultPanelWidth: 380,
  },
  lenses: [
    {
      id: 'lens-sequence',
      label: 'Sequence',
      purpose: 'Show what happened, where, and in what order.',
      historicalQuestion: 'What happened, where, and in what order?',
      visualizationType: 'map',
      applicableTimeRange: { precision: 'range', earliest: '1914-07-05', latest: '1914-07-10' },
      visibleLocations: ['place-berlin', 'place-vienna'],
      visibleEvents: [
        'event-1-assurance-given',
        'event-2-vienna-posture-reported',
        'event-3-wilhelm-marginal-reaction',
      ],
      visibleRelationships: [],
      visibleRegions: [],
      legend: [],
      evidenceReferences: ['evidence-event-1-assurance-given-1'],
      limitations: [],
      textFallback: [
        '1. Berlin — Szögyény meets Wilhelm II; the assurance is given, 5 July 1914',
        '2. Vienna — Tschirschky reports Vienna’s ultimatum deliberations to Berlin, 10 July 1914',
        '3. Berlin — Wilhelm II annotates the report, dismissing further consultation, 10 July 1914',
      ],
    },
    {
      id: 'lens-systems',
      label: 'Systems',
      purpose: 'Show the mechanism connecting the assurance to Vienna’s posture, and its evidentiary strength.',
      historicalQuestion: 'How are these connected?',
      visualizationType: 'graph',
      applicableTimeRange: { precision: 'range', earliest: '1914-07-05', latest: '1914-07-10' },
      visibleLocations: [],
      visibleEvents: [],
      visibleRelationships: ['rel-r1-assurance-enabled-posture'],
      visibleRegions: [],
      legend: [],
      evidenceReferences: ['evidence-claim-c1-assurance-reported-1'],
      limitations: ['This causal link is disputed, not directly documented.'],
      textFallback: [
        'The reported assurance (claim) — causal-influence, disputed — Vienna’s posture (claim)',
      ],
    },
    {
      id: 'lens-uncertainty',
      label: 'Uncertainty',
      purpose: 'Show which parts of this investigation remain disputed.',
      historicalQuestion: 'Which parts remain weak, approximate, disputed, or unsupported?',
      visualizationType: 'map',
      applicableTimeRange: { precision: 'range', earliest: '1914-07-10', latest: '1914-07-10' },
      visibleLocations: ['place-vienna'],
      visibleEvents: ['event-2-vienna-posture-reported', 'event-3-wilhelm-marginal-reaction'],
      visibleRelationships: ['rel-r1-assurance-enabled-posture'],
      visibleRegions: [],
      legend: [],
      evidenceReferences: [],
      limitations: ['The link between the German assurance and Vienna’s posture is disputed, not directly documented.'],
      textFallback: [
        'Disputed: whether the assurance directly enabled Vienna’s posture (rel-r1-assurance-enabled-posture).',
      ],
    },
  ],
  storySequences: [],
  systemPaths: [
    {
      id: 'path-assurance-to-posture',
      title: 'The assurance and Vienna’s posture',
      lensId: 'lens-systems',
      nodeIds: ['claim-c1-assurance-reported', 'claim-c3-vienna-posture'],
      relationshipIds: ['rel-r1-assurance-enabled-posture'],
      summary: 'A disputed causal link between the reported German assurance and Vienna’s subsequent posture.',
      limitations: ['Not directly documented; classified disputed, not directly supported.'],
    },
  ],
  perspectiveComparisons: [],
  contextualPrompts: [],
  recommendedSelections: [],
  limitations: [],
  inspector: {
    defaultEvidenceDepth: 'standard',
    exposeGenerationReport: true,
    exposeRejectedSources: false,
  },
}

const goldenInvestigation = validateGeneratedInvestigation({
  ...goldenInvestigationJson,
  experiencePlan: BLANK_CHEQUE_EXPERIENCE_PLAN,
})

// Generated end-to-end by the Python pipeline's curated (not mock) provider
// set — see backend/src/chronicle/providers/curated/concert_of_europe/ and
// plans/current-phase.md's Phase C3/D0.4 sections. Registering it here,
// alongside the hand-authored golden fixture, is what proves the generic
// renderer has no hidden coupling to blank-cheque's specific content. Its
// experiencePlan is generated by the curated pipeline's own
// experience_plan.py stage (Phase D0.4) — baked directly into the fixture
// JSON, no manual attachment needed here, unlike blank-cheque's.
const concertOfEuropeInvestigation = validateGeneratedInvestigation(
  concertOfEuropeInvestigationJson,
)

export const investigationFixtures: FixtureRegistration[] = [
  { investigation: goldenInvestigation, isDefault: true },
  { investigation: concertOfEuropeInvestigation, isDefault: false },
  { investigation: makeEmptyInvestigation(goldenInvestigation), isDefault: false },
]
