import { describe, expect, it } from 'vitest'
import {
  GeneratedInvestigationValidationError,
  validateGeneratedInvestigation,
} from './generatedInvestigation'
import goldenInvestigation from '../../../../fixtures/blank-cheque.golden-investigation.json'
import unsupportedVersion from '../../../../fixtures/contracts/invalid/unsupported-version.json'
import missingEvidenceReference from '../../../../fixtures/contracts/invalid/missing-evidence-reference.json'
import claimWithoutSupportingEvidence from '../../../../fixtures/contracts/invalid/claim-without-supporting-evidence.json'
import disputedRelationshipMissingCounterevidence from '../../../../fixtures/contracts/invalid/disputed-relationship-missing-counterevidence.json'
import overpreciseMapMarker from '../../../../fixtures/contracts/invalid/overprecise-map-marker.json'

function makeValidPackage() {
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
      dateRange: {
        precision: 'range',
        earliest: '1900-01-01',
        latest: '1900-01-02',
      },
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
      findings: [
        {
          id: 'finding-1',
          recordType: 'claim',
          recordId: 'claim-1',
          label: 'The decision was recorded.',
          importance: 'major',
        },
      ],
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
        eventTime: {
          precision: 'exact',
          earliest: '1900-01-01',
          latest: '1900-01-01',
        },
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
        dateOfSource: {
          precision: 'exact',
          earliest: '1900-01-01',
          latest: '1900-01-01',
        },
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
      {
        id: 'passage-1',
        documentId: 'document-1',
        excerpt: 'The decision was recorded.',
        locator: 'p. 1',
      },
    ],
    evidenceLinks: [
      {
        id: 'evidence-claim-1',
        targetType: 'claim',
        targetId: 'claim-1',
        passageId: 'passage-1',
        role: 'supporting',
      },
      {
        id: 'evidence-event-1',
        targetType: 'event',
        targetId: 'event-1',
        passageId: 'passage-1',
        role: 'supporting',
      },
    ],
    claimLedgers: [
      {
        id: 'ledger-claim-1',
        claimId: 'claim-1',
        evidenceLinkIds: ['evidence-claim-1'],
        conclusion: 'supported',
        limitations: ['Single-source test fixture.'],
      },
    ],
    timeline: [{ id: 'timeline-1', eventId: 'event-1', order: 0 }],
    mapAssets: [
      {
        id: 'map-asset-1',
        imagePath: '/maps/test.jpg',
        bounds: {
          topLeft: { lat: 55, lng: 5 },
          topRight: { lat: 55, lng: 15 },
          bottomRight: { lat: 45, lng: 15 },
          bottomLeft: { lat: 45, lng: 5 },
        },
        defaultView: { center: { lat: 50, lng: 10 }, zoom: 4 },
        periodLabel: 'Test map, 1900',
        sourceCitation: 'Test atlas (1900).',
        attribution: 'Test archive',
        license: 'Public domain',
        georeferencingNote: 'Approximate fit to a printed graticule.',
        rightsStatus: 'public-domain',
        periodFitDecision: 'approved',
        georeferencingPrecision: 'approximate',
      },
    ],
    mapScenes: [
      {
        id: 'map-scene-1',
        sceneId: 'scene-1',
        mapAssetId: 'map-asset-1',
        markers: [{ placeId: 'place-1', precision: 'city' }],
      },
    ],
    scenes: [
      {
        id: 'scene-1',
        title: 'The recorded decision',
        curationStatus: 'reviewed',
        dateRange: {
          precision: 'range',
          earliest: '1900-01-01',
          latest: '1900-01-02',
        },
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
        mapSceneId: 'map-scene-1',
      },
    ],
    interactionSpec: {
      defaultSceneId: 'scene-1',
      focusKinds: [
        'scene',
        'event',
        'entity',
        'claim',
        'relationship',
        'source',
        'passage',
        'timeRange',
      ],
      enabledFacets: ['narrative', 'timeline', 'map', 'graph', 'evidence'],
      omittedCapabilities: [],
    },
    generationReport: {
      outcome: 'complete',
      stages: [{ id: 'fixture-migration', status: 'passed' }],
      omissions: [],
      warnings: [],
      verificationChecks: [
        { id: 'references', status: 'passed', message: 'All references resolve.' },
      ],
    },
  }
}

describe('GeneratedInvestigation contract', () => {
  it('accepts a complete, internally supported package', () => {
    expect(() => validateGeneratedInvestigation(makeValidPackage())).not.toThrow()
  })

  it('rejects an unsupported schema major version', () => {
    const broken = makeValidPackage()
    broken.schemaVersion = '2.0.0'

    expect(() => validateGeneratedInvestigation(broken)).toThrow(
      GeneratedInvestigationValidationError,
    )
  })

  it('rejects a reference to an unknown record id', () => {
    const broken = makeValidPackage()
    broken.documents[0].sourceId = 'source-missing'

    expect(() => validateGeneratedInvestigation(broken)).toThrow(
      /unknown Source/i,
    )
  })

  it('rejects a major synthesis claim without a claim ledger', () => {
    const broken = makeValidPackage()
    broken.claimLedgers = []

    expect(() => validateGeneratedInvestigation(broken)).toThrow(
      /major finding.*ledger/i,
    )
  })

  it('rejects proposed evidence records from a published package', () => {
    const broken = makeValidPackage()
    broken.status = 'published'
    broken.claims[0].reviewStatus = 'proposed'

    expect(() => validateGeneratedInvestigation(broken)).toThrow(
      /published package.*reviewed or disputed/i,
    )
  })

  it('rejects a displayed map whose rights do not permit display', () => {
    const broken = makeValidPackage()
    broken.mapAssets[0].rightsStatus = 'needs-permission'

    expect(() => validateGeneratedInvestigation(broken)).toThrow(
      /map asset.*rights/i,
    )
  })

  it('rejects a map marker more precise than its Place evidence', () => {
    const broken = makeValidPackage()
    broken.mapScenes[0].markers[0].precision = 'building'

    expect(() => validateGeneratedInvestigation(broken)).toThrow(
      /marker.*precision/i,
    )
  })
})

describe('Blank Cheque golden investigation', () => {
  it('validates through the same package boundary used by the renderer', () => {
    const investigation = validateGeneratedInvestigation(goldenInvestigation)

    expect(investigation.packageId).toBe('blank-cheque-golden')
    expect(investigation.scenes[0].id).toBe('scene-2-blank-cheque')
  })

  it('retains the prototype claim and its disputed relationship without embedded evidence duplication', () => {
    const investigation = validateGeneratedInvestigation(goldenInvestigation)
    const claim = investigation.claims.find(
      (record) => record.id === 'claim-c1-assurance-reported',
    )
    const relationship = investigation.relationships.find(
      (record) => record.id === 'rel-r1-assurance-enabled-posture',
    )

    expect(claim?.statement).toMatch(/could count on Germany’s full support/i)
    expect(claim && 'evidenceLinks' in claim).toBe(false)
    expect(relationship?.evidenceClassification).toBe('disputed')
    expect(relationship?.evidenceLinkIds).toHaveLength(2)
  })
})

/**
 * Phase C0 cross-language parity: fixtures/contracts/invalid/*.json are
 * minimal, deliberately-broken mutations of the golden package, each
 * targeting one validateGeneratedInvestigation() rule. The Python mirror
 * (backend/tests/contract/test_invalid_fixtures.py) asserts the exact same
 * fixtures are rejected — this is the cheap half of "Preventing schema
 * drift" (chronicle_phase_c_adjusted_plan.md §6): both runtimes reject the
 * same broken packages, not just accept the same valid one.
 */
describe('Shared invalid fixtures (Python/TypeScript parity)', () => {
  it.each([
    ['unsupported-version', unsupportedVersion, /unsupported.*schema version/i],
    ['missing-evidence-reference', missingEvidenceReference, /unknown Passage/i],
    ['claim-without-supporting-evidence', claimWithoutSupportingEvidence, /requires a supporting EvidenceLink/i],
    [
      'disputed-relationship-missing-counterevidence',
      disputedRelationshipMissingCounterevidence,
      /requires supporting and counterevidence links/i,
    ],
    ['overprecise-map-marker', overpreciseMapMarker, /exceeds Place/i],
  ])('rejects %s', (_name, fixture, messagePattern) => {
    expect(() => validateGeneratedInvestigation(fixture)).toThrow(messagePattern)
  })
})
