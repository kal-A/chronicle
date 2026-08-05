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
    <div className="flex flex-col gap-3 text-sm">
      {!hasAnything && (
        <p className="text-neutral-500 dark:text-neutral-400">
          No reviewed or prototype-curated evidence is linked to this selection yet.
        </p>
      )}

      {claims.map((claim) => (
        <div key={claim.id} className="rounded-lg border border-neutral-200 p-2 dark:border-neutral-800">
          <p className="font-medium text-neutral-900 dark:text-neutral-50">{claim.statement}</p>
          <p className="mt-1 text-xs text-neutral-500 dark:text-neutral-400">
            {claim.directOrInferred === 'direct' ? 'Direct' : 'Inferred'} claim
          </p>
        </div>
      ))}

      {relationships.map((relationship) => (
        <div
          key={relationship.id}
          className="rounded-lg border border-dashed border-amber-400 bg-amber-50/60 p-2 dark:border-amber-700 dark:bg-amber-950/20"
        >
          <p className="text-xs font-bold uppercase tracking-wide text-amber-700 dark:text-amber-400">
            {relationship.evidenceClassification.replace('_', ' ')}
          </p>
          <p className="text-xs text-neutral-600 dark:text-neutral-400">{relationship.relationshipType}</p>
        </div>
      ))}

      {hasAnything && (
        <button
          type="button"
          className="self-start text-xs font-semibold text-blue-700 hover:underline dark:text-blue-400"
          onClick={onOpenInspector}
        >
          Open full evidence in Inspector →
        </button>
      )}
    </div>
  )
}
