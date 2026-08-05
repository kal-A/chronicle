import type { InvestigationExperiencePlan } from '../model/experiencePlan'

/**
 * map-first-workspace-instructions.md §5's scope-review step. Only two real
 * actions are offered — Generate and Ask something else — not the fuller
 * §4.2 action set (Edit scope, Expand timeframe, ...), since those would be
 * non-functional buttons with no real destination given there is no live
 * generation pipeline behind this prototype (see topicMatch.ts's docstring).
 */
export function ScopeReviewCard({
  opening,
  onGenerate,
  onAskSomethingElse,
}: {
  opening: InvestigationExperiencePlan['opening']
  onGenerate: () => void
  onAskSomethingElse: () => void
}) {
  return (
    <div className="flex flex-col gap-4 rounded-lg border border-neutral-300 bg-white p-5 dark:border-neutral-700 dark:bg-neutral-900">
      <div>
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-50">
          Proposed scope
        </h2>
        <p className="mt-1 text-sm text-neutral-700 dark:text-neutral-300">{opening.question}</p>
      </div>
      <dl className="grid gap-3 text-sm">
        <div>
          <dt className="font-medium text-neutral-600 dark:text-neutral-400">Scope</dt>
          <dd className="text-neutral-800 dark:text-neutral-200">{opening.scopeSummary}</dd>
        </div>
        <div>
          <dt className="font-medium text-neutral-600 dark:text-neutral-400">
            What the evidence currently shows
          </dt>
          <dd className="text-neutral-800 dark:text-neutral-200">{opening.leadAnswer}</dd>
        </div>
        <div>
          <dt className="font-medium text-neutral-600 dark:text-neutral-400">Evidence coverage</dt>
          <dd className="text-neutral-800 dark:text-neutral-200">
            {opening.evidenceCoverageSummary}
          </dd>
        </div>
      </dl>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={onGenerate}
          className="rounded bg-neutral-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-neutral-700 dark:bg-neutral-100 dark:text-neutral-900 dark:hover:bg-neutral-300"
        >
          Generate this investigation
        </button>
        <button
          type="button"
          onClick={onAskSomethingElse}
          className="rounded border border-neutral-300 px-3 py-1.5 text-sm font-medium text-neutral-700 hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
        >
          Ask something else
        </button>
      </div>
    </div>
  )
}
