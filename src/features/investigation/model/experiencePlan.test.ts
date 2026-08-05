import { describe, expect, it } from 'vitest'
import { validateGeneratedInvestigation } from './generatedInvestigation'
import goldenInvestigation from '../../../../fixtures/blank-cheque.golden-investigation.json'
import experiencePlanUnknownLocation from '../../../../fixtures/contracts/invalid/experience-plan-unknown-location.json'
import experiencePlanUnknownInitialLens from '../../../../fixtures/contracts/invalid/experience-plan-unknown-initial-lens.json'

function makeBasePackage() {
  return {
    schemaVersion: '1.0.0',
    packageId: 'investigation-test',
    packageRevision: 1,
    generatedAt: '2026-08-03T12:00:00.000Z',
    request: {
      id: 'request-test',
      rawInput: 'Why did the test decision happen?',
      requestType: 'causal-investigation',
      requestedDepth: 'focused',
      createdAt: '2026-08-03T11:00:00.000Z',
    },
    scope: {
      interpretedQuestion: 'Why did the test decision happen?',
      dateRange: { precision: 'range', earliest: '1900-01-01', latest: '1900-01-02' },
      geographicScope: ['Test City'],
      themes: ['diplomacy'],
      inclusions: ['the decision'],
      exclusions: ['later consequences'],
      approvalStatus: 'approved',
    },
    status: 'draft',
    presentation: {
      title: 'A test investigation',
      synthesis: [
        {
          id: 'narrative-1',
          order: 0,
          text: 'The surviving passage directly supports the decision claim.',
          isMaterialAssertion: true,
          referencedRecordIds: ['claim-1'],
          relatedEventId: 'event-1',
        },
      ],
      findings: [],
      sceneIds: ['scene-1'],
      perspectiveIds: [],
    },
    entities: [
      {
        id: 'place-1',
        entityType: 'place',
        canonicalName: 'Test City',
        reviewStatus: 'reviewed',
        coordinates: { lat: 50, lng: 10 },
        periodRecords: [
          {
            periodLabel: '1900',
            nameAtTime: 'Test City',
            controllingPolity: 'Test Polity',
            precision: 'city',
          },
        ],
      },
    ],
    events: [
      {
        id: 'event-1',
        title: 'A decision was recorded',
        placeId: 'place-1',
        eventTime: { precision: 'exact', earliest: '1900-01-01', latest: '1900-01-01' },
        evidenceLinkIds: ['evidence-event-1'],
        relatedRecordIds: ['claim-1'],
        reviewStatus: 'reviewed',
        visibility: 'public',
      },
    ],
    decisions: [],
    communications: [],
    knowledgeStates: [],
    claims: [
      {
        id: 'claim-1',
        statement: 'The decision was recorded in the surviving document.',
        directOrInferred: 'direct',
        reviewStatus: 'reviewed',
        visibility: 'public',
        evidenceLinkIds: ['evidence-claim-1'],
      },
    ],
    relationships: [],
    perspectives: [],
    conflicts: [],
    uncertainties: [],
    researchGaps: [],
    sources: [
      {
        id: 'source-1',
        title: 'Test source',
        sourceType: 'primary-official-diplomatic',
        authorOrOrigin: 'Test archive',
        dateOfSource: { precision: 'exact', earliest: '1900-01-01', latest: '1900-01-01' },
        originalLanguage: 'English',
        rightsStatus: 'public-domain',
        curationStatus: 'reviewed',
        knownLimitations: 'Created only for contract testing.',
        linkOrLocation: 'test://source-1',
      },
    ],
    documents: [
      {
        id: 'document-1',
        sourceId: 'source-1',
        editionCitation: 'Test edition, p. 1.',
        visibility: 'public',
        knownLimitations: 'Created only for contract testing.',
      },
    ],
    passages: [
      { id: 'passage-1', documentId: 'document-1', excerpt: 'The decision was recorded.', locator: 'p. 1' },
    ],
    evidenceLinks: [
      { id: 'evidence-claim-1', targetType: 'claim', targetId: 'claim-1', passageId: 'passage-1', role: 'supporting' },
      { id: 'evidence-event-1', targetType: 'event', targetId: 'event-1', passageId: 'passage-1', role: 'supporting' },
    ],
    claimLedgers: [],
    timeline: [{ id: 'timeline-1', eventId: 'event-1', order: 0 }],
    mapAssets: [],
    mapScenes: [],
    scenes: [
      {
        id: 'scene-1',
        title: 'The recorded decision',
        curationStatus: 'reviewed',
        dateRange: { precision: 'range', earliest: '1900-01-01', latest: '1900-01-02' },
        placeIds: ['place-1'],
        entityIds: ['place-1'],
        sourceIds: ['source-1'],
        documentIds: ['document-1'],
        passageIds: ['passage-1'],
        eventIds: ['event-1'],
        claimIds: ['claim-1'],
        relationshipIds: [],
        knowledgeStateIds: [],
        narrativeBlockIds: ['narrative-1'],
      },
    ],
    interactionSpec: {
      defaultSceneId: 'scene-1',
      focusKinds: ['scene', 'event', 'entity', 'claim', 'relationship', 'source', 'passage', 'timeRange'],
      enabledFacets: ['narrative', 'timeline', 'map', 'graph', 'evidence'],
      omittedCapabilities: [],
    },
    generationReport: {
      outcome: 'complete',
      stages: [{ id: 'fixture-migration', status: 'passed' }],
      omissions: [],
      warnings: [],
      verificationChecks: [{ id: 'references', status: 'passed', message: 'All references resolve.' }],
    },
  }
}

function makeValidExperiencePlan() {
  const timeRange = { precision: 'range' as const, earliest: '1900-01-01', latest: '1900-01-02' }
  return {
    opening: {
      question: 'Why did the test decision happen?',
      scopeSummary: 'One decision, one city, one day.',
      leadAnswer: 'The decision was recorded and is directly supported.',
      evidenceCoverageSummary: 'One primary source, fully cited.',
    },
    workspace: {
      initialMapScope: {
        bounds: {
          topLeft: { lat: 55, lng: 5 },
          topRight: { lat: 55, lng: 15 },
          bottomRight: { lat: 45, lng: 15 },
          bottomLeft: { lat: 45, lng: 5 },
        },
        focusRegions: [{ id: 'region-test', label: 'Test Region' }],
        contextRegions: [],
        initialViewport: { center: { lat: 50, lng: 10 }, zoom: 5 },
        minimumZoom: 2,
        maximumZoom: 10,
        geographicRationale: 'Test City is the only location in this fixture.',
        representedPeriod: timeRange,
        unavailableHistoricalBoundaries: [],
        geographicLimitations: [],
      },
      initialLensId: 'lens-sequence',
      initialTimeRange: timeRange,
      initialPanelTab: 'explore',
      defaultPanelWidth: 380,
    },
    lenses: [
      {
        id: 'lens-sequence',
        label: 'Sequence',
        purpose: 'Show what happened, where, and in what order.',
        historicalQuestion: 'What happened, where, and in what order?',
        visualizationType: 'map' as const,
        applicableTimeRange: timeRange,
        visibleLocations: ['place-1'],
        visibleEvents: ['event-1'],
        visibleRelationships: [],
        visibleRegions: [],
        legend: [],
        evidenceReferences: ['evidence-claim-1'],
        limitations: [],
        textFallback: ['1. Test City — A decision was recorded, 1 January 1900'],
      },
    ],
    storySequences: [
      {
        id: 'story-1',
        title: 'The decision',
        summary: 'A single-step sequence.',
        stepIds: ['event-1'],
        defaultLensId: 'lens-sequence',
        defaultTimeRange: timeRange,
      },
    ],
    systemPaths: [
      {
        id: 'path-1',
        title: 'The decision path',
        lensId: 'lens-sequence',
        nodeIds: ['claim-1'],
        relationshipIds: [],
        summary: 'A single-node path.',
        limitations: [],
      },
    ],
    perspectiveComparisons: [],
    contextualPrompts: [
      {
        id: 'prompts-no-selection',
        appliesTo: 'no-selection',
        prompts: [{ id: 'prompt-1', text: 'What is the main conclusion?', targetLensId: 'lens-sequence' }],
      },
    ],
    recommendedSelections: [
      { id: 'selection-1', kind: 'event', recordId: 'event-1', label: 'A decision was recorded' },
    ],
    limitations: [
      { id: 'limitation-1', summary: 'Only one source is curated.', affectedLensIds: ['lens-sequence'] },
    ],
    inspector: {
      defaultEvidenceDepth: 'standard',
      exposeGenerationReport: true,
      exposeRejectedSources: false,
    },
  }
}

describe('InvestigationExperiencePlan (optional, additive)', () => {
  it('accepts a package with a valid experience plan', () => {
    const withPlan = { ...makeBasePackage(), experiencePlan: makeValidExperiencePlan() }
    expect(() => validateGeneratedInvestigation(withPlan)).not.toThrow()
  })

  it('accepts a package with no experience plan at all (optional field)', () => {
    expect(() => validateGeneratedInvestigation(makeBasePackage())).not.toThrow()
  })

  it('the existing golden fixture (no experience plan) still validates unmodified', () => {
    expect(() => validateGeneratedInvestigation(goldenInvestigation)).not.toThrow()
  })

  it('rejects a lens that references an unknown Place', () => {
    const plan = makeValidExperiencePlan()
    plan.lenses[0].visibleLocations = ['place-missing']
    const broken = { ...makeBasePackage(), experiencePlan: plan }

    expect(() => validateGeneratedInvestigation(broken)).toThrow(/unknown Place/i)
  })

  it('rejects workspace.initialLensId referencing an unknown lens', () => {
    const plan = makeValidExperiencePlan()
    plan.workspace.initialLensId = 'lens-missing'
    const broken = { ...makeBasePackage(), experiencePlan: plan }

    expect(() => validateGeneratedInvestigation(broken)).toThrow(/unknown InvestigationLens/i)
  })

  it('rejects a StorySequence step that is not a known Event', () => {
    const plan = makeValidExperiencePlan()
    plan.storySequences[0].stepIds = ['event-missing']
    const broken = { ...makeBasePackage(), experiencePlan: plan }

    expect(() => validateGeneratedInvestigation(broken)).toThrow(/unknown Event/i)
  })

  it('rejects a SystemPath node that is not any known record', () => {
    const plan = makeValidExperiencePlan()
    plan.systemPaths[0].nodeIds = ['record-missing']
    const broken = { ...makeBasePackage(), experiencePlan: plan }

    expect(() => validateGeneratedInvestigation(broken)).toThrow(/unknown record/i)
  })

  it('rejects a ContextualPromptSet prompt targeting an unknown lens', () => {
    const plan = makeValidExperiencePlan()
    plan.contextualPrompts[0].prompts[0].targetLensId = 'lens-missing'
    const broken = { ...makeBasePackage(), experiencePlan: plan }

    expect(() => validateGeneratedInvestigation(broken)).toThrow(/unknown InvestigationLens/i)
  })

  it('rejects an InvestigationLimitation referencing an unknown lens', () => {
    const plan = makeValidExperiencePlan()
    plan.limitations[0].affectedLensIds = ['lens-missing']
    const broken = { ...makeBasePackage(), experiencePlan: plan }

    expect(() => validateGeneratedInvestigation(broken)).toThrow(/unknown InvestigationLens/i)
  })

  it('rejects a lens id colliding with an existing package id (global uniqueness)', () => {
    const plan = makeValidExperiencePlan()
    plan.lenses[0].id = 'claim-1'
    const broken = { ...makeBasePackage(), experiencePlan: plan }

    expect(() => validateGeneratedInvestigation(broken)).toThrow(/not unique/i)
  })
})

/**
 * Phase D0.2 cross-language parity, same pattern as C0's shared invalid
 * fixtures: minimal, deliberately-broken mutations of the golden package
 * plus a minimal experience plan, each targeting one
 * validateExperiencePlanReferences rule. The Python mirror
 * (backend/tests/contract/test_invalid_fixtures.py) asserts the same
 * fixtures are rejected there too.
 */
describe('Shared experience-plan invalid fixtures (Python/TypeScript parity)', () => {
  it.each([
    ['experience-plan-unknown-location', experiencePlanUnknownLocation, /unknown Place/i],
    ['experience-plan-unknown-initial-lens', experiencePlanUnknownInitialLens, /unknown InvestigationLens/i],
  ])('rejects %s', (_name, fixture, messagePattern) => {
    expect(() => validateGeneratedInvestigation(fixture)).toThrow(messagePattern)
  })
})
