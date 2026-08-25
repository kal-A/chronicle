import { useQuery } from '@tanstack/react-query'
import { useLocation, useParams } from 'react-router-dom'
import {
  fetchInvestigationScene,
  InvestigationPackageLoadError,
  InvestigationPackageNotFoundError,
} from './data/investigationRepository'
import { InvestigationSceneNotFoundError } from './model/normalizeInvestigation'
import { FocusProvider } from './focus/FocusContext'
import { InvestigationWorkspace } from './workspace/InvestigationWorkspace'
import { InspectorView } from './inspector/InspectorView'

/**
 * Shared loader/error/pending shell for both the map-first workspace (the
 * default) and Inspector (docs/decisions/ADR-002-map-first-workspace.md) —
 * `mode` picks which one renders once the package/scene resolve; neither
 * duplicates the fetch/loading/error handling.
 */
export function InvestigationPage({ mode = 'workspace' }: { mode?: 'workspace' | 'inspector' }) {
  const { packageId = '', sceneId = '' } = useParams()
  const location = useLocation()
  const enteredFromAsk = Boolean(
    (location.state as { enteredFromAsk?: boolean } | null)?.enteredFromAsk,
  )
  const submittedQuestion =
    (location.state as { question?: string } | null)?.question?.trim() || undefined
  const { data, isPending, isError, error } = useQuery({
    queryKey: ['investigation', packageId, 'scene', sceneId],
    queryFn: () => fetchInvestigationScene(packageId, sceneId),
  })

  if (isPending) {
    return (
      <main className="chronicle-investigation-state">
        <p role="status">
          Loading investigation…
        </p>
      </main>
    )
  }

  if (isError) {
    const message =
      error instanceof InvestigationPackageNotFoundError
        ? 'This investigation could not be found.'
        : error instanceof InvestigationSceneNotFoundError
          ? 'This scene could not be found.'
          : error instanceof InvestigationPackageLoadError
            ? 'This investigation failed to load. Please try again.'
          : 'Something went wrong loading this investigation.'
    return (
      <main className="chronicle-investigation-state chronicle-investigation-state--error">
        <p role="alert">
          {message}
        </p>
      </main>
    )
  }

  return (
    <FocusProvider defaultFocus={{ kind: 'scene', sceneId: data.scene.id }}>
      {mode === 'inspector' ? (
        <InspectorView
          scene={data.scene}
          investigationTitle={data.investigation.presentation.title}
          workspaceHref={`/investigations/${encodeURIComponent(packageId)}/scenes/${encodeURIComponent(sceneId)}`}
        />
      ) : (
        <InvestigationWorkspace
          investigation={data.investigation}
          scene={data.scene}
          enteredFromAsk={enteredFromAsk}
          submittedQuestion={submittedQuestion}
        />
      )}
    </FocusProvider>
  )
}
