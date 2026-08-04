import type { Scene } from '../model/schema'
import type { FocusValue } from '../model/focus'

/**
 * Primary reading facet. Every material block that has a related Event is a
 * clickable focus target — sets Focus with source: 'narrative'
 * (docs/design/map-timeline-graph-sync.md). Non-material (scene-setting)
 * blocks are plain prose, not interactive.
 */
export function NarrativeView({
  scene,
  focus,
  onSelectFocus,
}: {
  scene: Scene
  focus: FocusValue
  onSelectFocus: (focus: FocusValue) => void
}) {
  const hasClickableBlocks = scene.narrativeBlocks.some((b) => b.relatedEventId)

  return (
    <section aria-labelledby="narrative-heading" className="flex flex-col gap-4">
      <div>
        <h2
          id="narrative-heading"
          className="text-2xl font-bold tracking-tight text-neutral-900 dark:text-neutral-50"
        >
          {scene.title}
        </h2>
        {hasClickableBlocks && (
          <p className="mt-1 text-xs text-neutral-500 dark:text-neutral-400">
            Underlined paragraphs are selectable — pick one to see the exact
            evidence behind it, and where it appears on the timeline and map.
          </p>
        )}
      </div>

      {scene.curationStatus !== 'reviewed' && (
        <p className="rounded-lg border border-amber-400 bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:border-amber-700 dark:bg-amber-950/40 dark:text-amber-200">
          <strong>Prototype content.</strong> Curated for this prototype and
          owner-reviewed only — not independently reviewed historical
          content.
        </p>
      )}

      <ol className="flex flex-col gap-2">
        {[...scene.narrativeBlocks]
          .sort((a, b) => a.order - b.order)
          .map((block) => {
            const isFocused =
              focus.kind === 'event' && focus.eventId === block.relatedEventId
            const clickable = Boolean(block.relatedEventId)
            return (
              <li key={block.id}>
                {clickable ? (
                  <button
                    type="button"
                    className={`w-full rounded-lg border-l-4 p-3 text-left text-[15px] leading-relaxed underline decoration-dotted decoration-neutral-400 underline-offset-4 transition-colors hover:bg-neutral-50 dark:hover:bg-neutral-900 ${
                      isFocused
                        ? 'border-blue-600 bg-blue-50 font-medium no-underline dark:bg-blue-950/40'
                        : 'border-transparent text-neutral-800 dark:text-neutral-200'
                    }`}
                    aria-pressed={isFocused}
                    onClick={() =>
                      block.relatedEventId &&
                      onSelectFocus({ kind: 'event', eventId: block.relatedEventId })
                    }
                  >
                    {block.text}
                  </button>
                ) : (
                  <p className="p-3 text-[15px] leading-relaxed text-neutral-600 dark:text-neutral-400">
                    {block.text}
                  </p>
                )}
              </li>
            )
          })}
      </ol>
    </section>
  )
}
