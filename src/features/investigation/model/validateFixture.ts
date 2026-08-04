import {
  SceneSchema,
  DISPLAYABLE_CURATION_STATUSES,
  type Scene,
} from './schema'

export class FixtureValidationError extends Error {}

/**
 * Whole-fixture graph validation, distinct from per-record Zod schemas.
 * Confirms cross-references actually resolve within the fixture and that
 * every material NarrativeBlock rests on a displayable (prototype-curated or
 * reviewed) record — a Zod .refine on one object can't see across the graph.
 * Plan 0/Plan 2 requirement: "reject unsupported claims" at startup/test time.
 */
export function validateFixture(input: unknown): Scene {
  const scene = SceneSchema.parse(input)

  const passageIds = new Set(scene.passages.map((p) => p.id))
  const documentIds = new Set(scene.documents.map((d) => d.id))
  const sourceIds = new Set(scene.sources.map((s) => s.id))
  const placeIds = new Set(
    scene.entities.filter((e) => e.entityType === 'place').map((e) => e.id),
  )

  for (const doc of scene.documents) {
    if (!sourceIds.has(doc.sourceId)) {
      throw new FixtureValidationError(
        `Document "${doc.id}" references unknown Source "${doc.sourceId}"`,
      )
    }
  }

  for (const passage of scene.passages) {
    if (!documentIds.has(passage.documentId)) {
      throw new FixtureValidationError(
        `Passage "${passage.id}" references unknown Document "${passage.documentId}"`,
      )
    }
  }

  for (const placeId of scene.placeIds) {
    if (!placeIds.has(placeId)) {
      throw new FixtureValidationError(
        `Scene "${scene.id}" references unknown Place entity "${placeId}"`,
      )
    }
  }

  const displayableRecordIds = new Set<string>()

  for (const claim of scene.claims) {
    for (const link of claim.evidenceLinks) {
      if (!passageIds.has(link.passageId)) {
        throw new FixtureValidationError(
          `Claim "${claim.id}" references unknown Passage "${link.passageId}"`,
        )
      }
    }
    if (
      DISPLAYABLE_CURATION_STATUSES.includes('prototype-curated') ||
      claim.reviewStatus === 'reviewed'
    ) {
      // Phase 1 claims are validated at the fixture level as prototype-curated
      // (see docs/research/validation-status.md); reviewStatus alone governs
      // eligibility once Phase 2's full review workflow exists.
      displayableRecordIds.add(claim.id)
    }
  }

  for (const rel of scene.relationships) {
    for (const link of rel.evidenceLinks) {
      if (!passageIds.has(link.passageId)) {
        throw new FixtureValidationError(
          `Relationship "${rel.id}" references unknown Passage "${link.passageId}"`,
        )
      }
    }
    displayableRecordIds.add(rel.id)
  }

  for (const kat of scene.knownAtTimes) {
    for (const link of kat.evidenceLinks) {
      if (!passageIds.has(link.passageId)) {
        throw new FixtureValidationError(
          `KnownAtTime "${kat.id}" references unknown Passage "${link.passageId}"`,
        )
      }
    }
    displayableRecordIds.add(kat.id)
  }

  const eventIds = new Set(scene.events.map((e) => e.id))

  for (const event of scene.events) {
    if (!placeIds.has(event.placeId)) {
      throw new FixtureValidationError(
        `Event "${event.id}" references unknown Place entity "${event.placeId}"`,
      )
    }
    for (const link of event.evidenceLinks) {
      if (!passageIds.has(link.passageId)) {
        throw new FixtureValidationError(
          `Event "${event.id}" references unknown Passage "${link.passageId}"`,
        )
      }
    }
    for (const recordId of event.relatedRecordIds) {
      if (!displayableRecordIds.has(recordId)) {
        throw new FixtureValidationError(
          `Event "${event.id}" references "${recordId}", which does not ` +
            `resolve to a displayable Claim, Relationship, or KnownAtTime in this fixture`,
        )
      }
    }
  }

  for (const block of scene.narrativeBlocks) {
    if (block.relatedEventId && !eventIds.has(block.relatedEventId)) {
      throw new FixtureValidationError(
        `NarrativeBlock "${block.id}" references unknown Event "${block.relatedEventId}"`,
      )
    }
    if (!block.isMaterialAssertion) continue
    for (const recordId of block.referencedRecordIds) {
      if (!displayableRecordIds.has(recordId)) {
        throw new FixtureValidationError(
          `NarrativeBlock "${block.id}" makes a material assertion referencing ` +
            `"${recordId}", which does not resolve to a displayable Claim, ` +
            `Relationship, or KnownAtTime in this fixture`,
        )
      }
    }
  }

  return scene
}
