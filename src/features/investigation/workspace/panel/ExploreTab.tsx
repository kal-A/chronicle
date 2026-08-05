import type { GeneratedInvestigation } from '../../model/generatedInvestigation'
import type { InvestigationLens } from '../../model/experiencePlan'

/** Lens-aware summary — direct answer, what the active lens shows, and its
 * disclosed limitations. Distinct from Inspector's full narrative: this is
 * the default-evidence-depth view map-first-workspace-instructions.md §8.2
 * describes for the Explore tab. */
export function ExploreTab({
  investigation,
  lens,
}: {
  investigation: GeneratedInvestigation
  lens: InvestigationLens
}) {
  const plan = investigation.experiencePlan

  return (
    <div className="flex flex-col gap-4 text-sm">
      {plan && (
        <div>
          <p className="font-medium text-neutral-900 dark:text-neutral-50">{plan.opening.leadAnswer}</p>
          <p className="mt-1 text-xs text-neutral-500 dark:text-neutral-400">
            {plan.opening.evidenceCoverageSummary}
          </p>
        </div>
      )}

      <div>
        <h2 className="text-xs font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
          {lens.label} lens
        </h2>
        <p className="mt-1 text-neutral-700 dark:text-neutral-300">{lens.purpose}</p>
      </div>

      <div>
        <h2 className="text-xs font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
          What&rsquo;s visible
        </h2>
        <ol className="mt-1 flex flex-col gap-1">
          {lens.textFallback.map((line) => (
            <li key={line} className="text-neutral-700 dark:text-neutral-300">
              {line}
            </li>
          ))}
        </ol>
      </div>

      {lens.limitations.length > 0 && (
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-amber-700 dark:text-amber-400">
            Limitations
          </h2>
          <ul className="mt-1 flex flex-col gap-1">
            {lens.limitations.map((limitation) => (
              <li key={limitation} className="text-amber-800 dark:text-amber-300">
                {limitation}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
