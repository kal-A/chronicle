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
    <div className="chronicle-panel-stack">
      {plan && (
        <div>
          <p className="chronicle-panel-lead">{plan.opening.leadAnswer}</p>
          <p className="chronicle-panel-muted">
            {plan.opening.evidenceCoverageSummary}
          </p>
        </div>
      )}

      <div>
        <h2 className="chronicle-panel-section-title">
          {lens.label} lens
        </h2>
        <p className="chronicle-panel-copy">{lens.purpose}</p>
      </div>

      <div>
        <h2 className="chronicle-panel-section-title">
          What&rsquo;s visible
        </h2>
        <ol className="chronicle-panel-list">
          {lens.textFallback.map((line) => (
            <li key={line}>
              {line}
            </li>
          ))}
        </ol>
      </div>

      {lens.limitations.length > 0 && (
        <div>
          <h2 className="chronicle-panel-section-title chronicle-panel-section-title--warning">
            Limitations
          </h2>
          <ul className="chronicle-panel-list chronicle-panel-list--warning">
            {lens.limitations.map((limitation) => (
              <li key={limitation}>
                {limitation}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
