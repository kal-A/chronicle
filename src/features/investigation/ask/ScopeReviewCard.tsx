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
    <div className="chronicle-scope-card">
      <div className="chronicle-scope-heading">
        <p className="chronicle-eyebrow">Before Chronicle opens the workspace</p>
        <h2>Proposed scope</h2>
        <p>{opening.question}</p>
      </div>
      <dl>
        <div>
          <dt>Scope</dt>
          <dd>{opening.scopeSummary}</dd>
        </div>
        <div>
          <dt>What the evidence currently shows</dt>
          <dd>{opening.leadAnswer}</dd>
        </div>
        <div>
          <dt>Evidence coverage</dt>
          <dd>{opening.evidenceCoverageSummary}</dd>
        </div>
      </dl>
      <div className="chronicle-scope-actions">
        <button
          type="button"
          onClick={onGenerate}
          className="chronicle-primary-action"
        >
          Generate this investigation
        </button>
        <button
          type="button"
          onClick={onAskSomethingElse}
          className="chronicle-secondary-action"
        >
          Ask something else
        </button>
      </div>
    </div>
  )
}
