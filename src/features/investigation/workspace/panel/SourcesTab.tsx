import type { Scene } from '../../model/schema'

/** Corpus coverage summary — accepted sources, type, and disclosed
 * limitations for the current scene (map-first-workspace-instructions.md
 * §8.2). Rejected/deferred candidates aren't tracked in the current
 * contract yet, so that part of the spec is out of scope until the
 * discovery pipeline (Phase E) produces them. */
export function SourcesTab({ scene }: { scene: Scene }) {
  if (scene.sources.length === 0) {
    return (
      <p className="text-sm text-neutral-500 dark:text-neutral-400">
        No sources are curated for this scene yet.
      </p>
    )
  }

  return (
    <ul className="flex flex-col gap-2 text-sm">
      {scene.sources.map((source) => (
        <li key={source.id} className="rounded-lg border border-neutral-200 p-2 dark:border-neutral-800">
          <p className="font-medium text-neutral-900 dark:text-neutral-50">{source.title}</p>
          <p className="text-xs text-neutral-500 dark:text-neutral-400">
            {source.sourceType.replace(/-/g, ' ')} &middot; {source.authorOrOrigin}
          </p>
          <p className="mt-1 text-xs text-neutral-600 dark:text-neutral-400">{source.knownLimitations}</p>
        </li>
      ))}
    </ul>
  )
}
