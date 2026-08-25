import type { Scene } from '../../model/schema'

/** Corpus coverage summary — accepted sources, type, and disclosed
 * limitations for the current scene (map-first-workspace-instructions.md
 * §8.2). Rejected/deferred candidates aren't tracked in the current
 * contract yet, so that part of the spec is out of scope until the
 * discovery pipeline (Phase E) produces them. */
export function SourcesTab({ scene }: { scene: Scene }) {
  if (scene.sources.length === 0) {
    return (
      <p className="chronicle-panel-muted">
        No sources are curated for this scene yet.
      </p>
    )
  }

  return (
    <ul className="chronicle-panel-list chronicle-source-list">
      {scene.sources.map((source) => (
        <li key={source.id} className="chronicle-panel-record">
          <p className="chronicle-panel-lead">{source.title}</p>
          <p className="chronicle-panel-muted">
            {source.sourceType.replace(/-/g, ' ')} &middot; {source.authorOrOrigin}
          </p>
          <p className="chronicle-panel-copy">{source.knownLimitations}</p>
        </li>
      ))}
    </ul>
  )
}
