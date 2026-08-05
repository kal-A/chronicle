import { Link } from 'react-router-dom'
import type { InvestigationLens } from '../model/experiencePlan'

export function WorkspaceHeader({
  investigationTitle,
  lenses,
  activeLensId,
  onSelectLens,
  inspectorHref,
  focusDescription,
}: {
  investigationTitle: string
  lenses: InvestigationLens[]
  activeLensId: string
  onSelectLens: (lensId: string) => void
  inspectorHref: string
  focusDescription: string
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-neutral-900 dark:text-neutral-50">
          Chronicle
        </h1>
        <p className="text-sm text-neutral-500 dark:text-neutral-400">{investigationTitle}</p>
      </div>
      <div className="flex flex-col items-end gap-2">
        <p
          role="status"
          aria-live="polite"
          className="text-xs text-neutral-500 dark:text-neutral-400"
        >
          {focusDescription}
        </p>
        <div className="flex items-center gap-2">
          <label
            htmlFor="workspace-lens-select"
            className="text-xs font-medium text-neutral-600 dark:text-neutral-400"
          >
            Lens
          </label>
          <select
            id="workspace-lens-select"
            value={activeLensId}
            onChange={(event) => onSelectLens(event.target.value)}
            className="rounded border border-neutral-300 bg-white px-2 py-1 text-xs dark:border-neutral-700 dark:bg-neutral-900"
          >
            {lenses.map((lens) => (
              <option key={lens.id} value={lens.id}>
                {lens.label}
              </option>
            ))}
          </select>
          <Link
            to={inspectorHref}
            className="rounded border border-neutral-300 px-2 py-1 text-xs font-medium text-neutral-700 hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
          >
            Inspector →
          </Link>
        </div>
      </div>
    </div>
  )
}
