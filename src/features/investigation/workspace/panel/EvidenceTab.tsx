import type { Scene } from '../../model/schema'
import type { FocusValue } from '../../model/focus'

/** Shallow evidence view — concise claim/classification, no passage
 * excerpts inline, with an explicit hand-off to Inspector for the full
 * evidence/provenance view (map-first-workspace-instructions.md §16.1).
 * Deliberately not a reskin of EvidencePanel.tsx: that component is the
 * *deep* view Inspector keeps unchanged. */
function resolveForFocus(scene: Scene, focus: FocusValue) {
  if (focus.kind === 'scene') {
    return { claims: scene.claims, relationships: scene.relationships }
  }
  if (focus.kind === 'claim') {
    return { claims: scene.claims.filter((c) => c.id === focus.claimId), relationships: [] }
  }
  if (focus.kind === 'relationship') {
    return { claims: [], relationships: scene.relationships.filter((r) => r.id === focus.relationshipId) }
  }
  if (focus.kind === 'event') {
    const event = scene.events.find((e) => e.id === focus.eventId)
    const related = new Set(event?.relatedRecordIds ?? [])
    return {
      claims: scene.claims.filter((c) => related.has(c.id)),
      relationships: scene.relationships.filter((r) => related.has(r.id)),
    }
  }
  if (focus.kind === 'entity' && focus.entityType === 'place') {
    const relatedIds = new Set(
      scene.events.filter((e) => e.placeId === focus.entityId).flatMap((e) => e.relatedRecordIds),
    )
    return {
      claims: scene.claims.filter((c) => relatedIds.has(c.id)),
      relationships: scene.relationships.filter((r) => relatedIds.has(r.id)),
    }
  }
  return { claims: [], relationships: [] }
}

export function EvidenceTab({
  scene,
  focus,
  onOpenInspector,
}: {
  scene: Scene
  focus: FocusValue
  onOpenInspector: () => void
}) {
  const { claims, relationships } = resolveForFocus(scene, focus)
  const hasAnything = claims.length > 0 || relationships.length > 0

  return (
    <div className="chronicle-panel-stack">
      {!hasAnything && (
        <p className="chronicle-panel-muted">
          No reviewed or prototype-curated evidence is linked to this selection yet.
        </p>
      )}

      {claims.map((claim) => (
        <div key={claim.id} className="chronicle-panel-record">
          <p className="chronicle-panel-lead">{claim.statement}</p>
          <p className="chronicle-panel-muted">
            {claim.directOrInferred === 'direct' ? 'Direct' : 'Inferred'} claim
          </p>
        </div>
      ))}

      {relationships.map((relationship) => (
        <div
          key={relationship.id}
          className="chronicle-panel-record chronicle-panel-record--caution"
        >
          <p className="chronicle-panel-section-title chronicle-panel-section-title--warning">
            {relationship.evidenceClassification.replace('_', ' ')}
          </p>
          <p className="chronicle-panel-muted">{relationship.relationshipType}</p>
        </div>
      ))}

      {hasAnything && (
        <button
          type="button"
          className="chronicle-panel-link"
          onClick={onOpenInspector}
        >
          Open full evidence in Inspector →
        </button>
      )}
    </div>
  )
}
