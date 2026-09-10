import { useState } from 'react'
import type { EditableScope } from './useAskGeneration'

/**
 * The reviewable, editable acquisition scope for the live-generation path. The
 * backend proposes a scope from the question (model assists) and the user
 * confirms or edits it here before anything is acquired (human decides). When
 * the model could not propose a scope, the fields arrive empty and the user
 * fills them in — the same form, no dead-end.
 */
export function GeneratedScopeForm({
  initialScope,
  autoResolved,
  note,
  onGenerate,
  onCancel,
}: {
  initialScope: EditableScope
  autoResolved: boolean
  note?: string
  onGenerate: (scope: EditableScope) => void
  onCancel: () => void
}) {
  const [scope, setScope] = useState<EditableScope>(initialScope)

  const canGenerate =
    scope.topic.trim().length > 0 &&
    scope.geographicScope.trim().length > 0 &&
    scope.dateEarliest.length > 0 &&
    scope.dateLatest.length > 0 &&
    scope.dateEarliest <= scope.dateLatest

  function update<K extends keyof EditableScope>(key: K, value: EditableScope[K]) {
    setScope((current) => ({ ...current, [key]: value }))
  }

  return (
    <form
      className="chronicle-scope-card"
      onSubmit={(event) => {
        event.preventDefault()
        if (canGenerate) onGenerate(scope)
      }}
    >
      <div className="chronicle-scope-heading">
        <p className="chronicle-eyebrow">Before Chronicle acquires sources</p>
        <h2>Review the proposed scope</h2>
        <p>
          {autoResolved
            ? 'Chronicle proposed this scope from your question. Adjust anything before it acquires free, public sources.'
            : 'Chronicle could not propose a scope automatically — set the geography and date range to acquire sources.'}
        </p>
        {note && !autoResolved ? (
          <p role="note" className="chronicle-scope-note">
            {note}
          </p>
        ) : null}
      </div>

      <div className="chronicle-scope-fields">
        <label>
          <span>Topic</span>
          <input
            type="text"
            value={scope.topic}
            onChange={(event) => update('topic', event.target.value)}
            placeholder="e.g. The Great Fire of London"
          />
        </label>
        <label>
          <span>Geography (comma-separated)</span>
          <input
            type="text"
            value={scope.geographicScope}
            onChange={(event) => update('geographicScope', event.target.value)}
            placeholder="e.g. London, England"
          />
        </label>
        <div className="chronicle-scope-dates">
          <label>
            <span>Earliest date</span>
            <input
              type="date"
              value={scope.dateEarliest}
              onChange={(event) => update('dateEarliest', event.target.value)}
            />
          </label>
          <label>
            <span>Latest date</span>
            <input
              type="date"
              value={scope.dateLatest}
              onChange={(event) => update('dateLatest', event.target.value)}
            />
          </label>
        </div>
      </div>

      <p className="chronicle-scope-disclosure">
        Live generation researches free, public sources with a local model. It is
        slow (minutes) and experimental; the result is a cited text answer or an
        honest abstention, not the curated map workspace.
      </p>

      <div className="chronicle-scope-actions">
        <button type="submit" disabled={!canGenerate} className="chronicle-primary-action">
          Acquire sources &amp; investigate
        </button>
        <button type="button" onClick={onCancel} className="chronicle-secondary-action">
          Ask something else
        </button>
      </div>
    </form>
  )
}
