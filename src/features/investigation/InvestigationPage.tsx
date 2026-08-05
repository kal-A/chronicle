import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
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
  const { data, isPending, isError, error } = useQuery({
    queryKey: ['investigation', packageId, 'scene', sceneId],
    queryFn: () => fetchInvestigationScene(packageId, sceneId),
  })

  if (isPending) {
    return (
      <main className="flex min-h-svh items-center justify-center bg-neutral-50 p-6 dark:bg-neutral-950">
        <p role="status" className="text-neutral-500 dark:text-neutral-400">
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
      <main className="flex min-h-svh items-center justify-center bg-neutral-50 p-6 dark:bg-neutral-950">
        <p role="alert" className="text-red-700 dark:text-red-400">
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
        <InvestigationWorkspace investigation={data.investigation} scene={data.scene} />
      )}
    </FocusProvider>
  )
}
