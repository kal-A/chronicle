import {
  toSceneEvidenceLinks,
  type GeneratedInvestigation,
} from './generatedInvestigation'
import { validateFixture } from './validateFixture'
import type { HistoricalMapLayer, Scene } from './schema'

export class InvestigationSceneNotFoundError extends Error {
  constructor(sceneId: string) {
    super(`No scene found for id "${sceneId}" in this investigation package`)
    this.name = 'InvestigationSceneNotFoundError'
  }
}

function selectByIds<T extends { id: string }>(records: T[], ids: string[]): T[] {
  const recordsById = new Map(records.map((record) => [record.id, record]))
  return ids.map((id) => recordsById.get(id)!).filter(Boolean)
}

function toHistoricalMapLayer(
  investigation: GeneratedInvestigation,
  mapSceneId: string | undefined,
): HistoricalMapLayer | undefined {
  if (!mapSceneId) return undefined
  const mapScene = investigation.mapScenes.find(
    (candidate) => candidate.id === mapSceneId,
  )
  if (!mapScene) return undefined
  const asset = investigation.mapAssets.find(
    (candidate) => candidate.id === mapScene.mapAssetId,
  )
  if (!asset) return undefined

  return {
    imagePath: asset.imagePath,
    bounds: asset.bounds,
    defaultView: asset.defaultView,
    periodLabel: asset.periodLabel,
    sourceCitation: asset.sourceCitation,
    attribution: asset.attribution,
    license: asset.license,
    georeferencingNote: asset.georeferencingNote,
  }
}

/**
 * Projects one package scene into the stable Scene view consumed by the
 * existing Explore facets. The package remains canonical; embedded evidence
 * arrays exist only in this derived view.
 */
export function normalizeInvestigationScene(
  investigation: GeneratedInvestigation,
  sceneId: string,
): Scene {
  const sceneReference = investigation.scenes.find(
    (candidate) => candidate.id === sceneId,
  )
  if (!sceneReference) throw new InvestigationSceneNotFoundError(sceneId)

  const linksById = new Map(
    investigation.evidenceLinks.map((link) => [link.id, link]),
  )

  const scene: Scene = {
    id: sceneReference.id,
    title: sceneReference.title,
    curationStatus: sceneReference.curationStatus,
    dateRange: sceneReference.dateRange,
    placeIds: sceneReference.placeIds,
    entities: selectByIds(investigation.entities, sceneReference.entityIds),
    sources: selectByIds(investigation.sources, sceneReference.sourceIds),
    documents: selectByIds(
      investigation.documents,
      sceneReference.documentIds,
    ),
    passages: selectByIds(investigation.passages, sceneReference.passageIds),
    events: selectByIds(investigation.events, sceneReference.eventIds).map(
      ({ evidenceLinkIds, reviewStatus: _reviewStatus, visibility: _visibility, ...event }) => ({
        ...event,
        evidenceLinks: toSceneEvidenceLinks(evidenceLinkIds, linksById),
      }),
    ),
    claims: selectByIds(investigation.claims, sceneReference.claimIds).map(
      ({ evidenceLinkIds, visibility: _visibility, ...claim }) => ({
        ...claim,
        evidenceLinks: toSceneEvidenceLinks(evidenceLinkIds, linksById),
      }),
    ),
    relationships: selectByIds(
      investigation.relationships,
      sceneReference.relationshipIds,
    ).map(
      ({ evidenceLinkIds, reviewStatus: _reviewStatus, visibility: _visibility, ...relationship }) => ({
        ...relationship,
        evidenceLinks: toSceneEvidenceLinks(evidenceLinkIds, linksById),
      }),
    ),
    knownAtTimes: selectByIds(
      investigation.knowledgeStates,
      sceneReference.knowledgeStateIds,
    ).map(
      ({ evidenceLinkIds, reviewStatus: _reviewStatus, visibility: _visibility, ...knowledgeState }) => ({
        ...knowledgeState,
        evidenceLinks: toSceneEvidenceLinks(evidenceLinkIds, linksById),
      }),
    ),
    narrativeBlocks: selectByIds(
      investigation.presentation.synthesis,
      sceneReference.narrativeBlockIds,
    ),
    mapLayer: toHistoricalMapLayer(
      investigation,
      sceneReference.mapSceneId,
    ),
  }

  return validateFixture(scene)
}
