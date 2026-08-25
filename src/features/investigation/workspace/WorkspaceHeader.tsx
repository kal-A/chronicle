import { Link } from 'react-router-dom'
import type { InvestigationLens } from '../model/experiencePlan'

export function WorkspaceHeader({
  investigationTitle,
  lenses,
  activeLensId,
  onSelectLens,
  inspectorHref,
  focusDescription,
  canClearFocus,
  onClearFocus,
}: {
  investigationTitle: string
  lenses: InvestigationLens[]
  activeLensId: string
  onSelectLens: (lensId: string) => void
  inspectorHref: string
  focusDescription: string
  canClearFocus: boolean
  onClearFocus: () => void
}) {
  return (
    <div className="chronicle-workspace-header">
      <div className="chronicle-workspace-identity">
        <Link to="/" className="chronicle-workspace-wordmark">Chronicle</Link>
        <h1>{investigationTitle}</h1>
      </div>
      <div className="chronicle-workspace-controls">
        <p
          role="status"
          aria-live="polite"
          className="chronicle-focus-status sr-only"
        >
          {focusDescription}
        </p>
        <div className="chronicle-lens-controls">
          <label
            htmlFor="workspace-lens-select"
            className="chronicle-control-label"
          >
            Lens
          </label>
          <select
            id="workspace-lens-select"
            value={activeLensId}
            onChange={(event) => onSelectLens(event.target.value)}
            className="chronicle-lens-select"
          >
            {lenses.map((lens) => (
              <option key={lens.id} value={lens.id}>
                {lens.label}
              </option>
            ))}
          </select>
          {canClearFocus ? (
            <button
              type="button"
              className="chronicle-return-to-scene"
              onClick={onClearFocus}
            >
              Show all events
            </button>
          ) : null}
          <Link
            to={inspectorHref}
            className="chronicle-inspector-link"
          >
            Inspector →
          </Link>
        </div>
      </div>
    </div>
  )
}
