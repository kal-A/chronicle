import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import {
  fetchInvestigationScene,
  InvestigationPackageLoadError,
  InvestigationPackageNotFoundError,
} from './data/investigationRepository'
import { InvestigationSceneNotFoundError } from './model/normalizeInvestigation'
import { FocusProvider } from './focus/FocusContext'
import { useFocus } from './focus/useFocus'
import { InvestigationLayout } from './InvestigationLayout'
import { NarrativeView } from './narrative/NarrativeView'
import { TimelineView } from './timeline/TimelineView'
import { MapView } from './map/MapView'
import { GraphView } from './graph/GraphView'
import { EvidencePanel } from './evidence/EvidencePanel'
import { describeFocus } from './model/describeFocus'
import type { Scene } from './model/schema'

export function InvestigationPage() {
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
      <InvestigationContent
        scene={data.scene}
        investigationTitle={data.investigation.presentation.title}
      />
    </FocusProvider>
  )
}

function InvestigationContent({
  scene,
  investigationTitle,
}: {
  scene: Scene
  investigationTitle: string
}) {
  const { focus, setFocus } = useFocus()
  const isWholeScene = focus.kind === 'scene'

  useEffect(() => {
    document.title = `${investigationTitle} · Chronicle`
    return () => {
      document.title = 'Chronicle'
    }
  }, [investigationTitle])

  return (
    <InvestigationLayout
      header={
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-neutral-900 dark:text-neutral-50">
              Chronicle
            </h1>
            <p className="text-sm text-neutral-500 dark:text-neutral-400">
              {investigationTitle}
            </p>
          </div>
          <div className="flex flex-col items-end gap-1 text-right">
            {/* Announces focus changes to screen-reader users, not just
                visually (docs/design/accessibility.md — "live status where
                necessary"). Also the plain-language answer to "what does
                selecting something do." */}
            <p
              role="status"
              aria-live="polite"
              className="text-xs text-neutral-500 dark:text-neutral-400"
            >
              {describeFocus(focus, scene)}
            </p>
            {!isWholeScene && (
              <button
                type="button"
                className="rounded border border-neutral-300 px-2 py-1 text-xs font-medium text-neutral-700 hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
                onClick={() =>
                  setFocus({ kind: 'scene', sceneId: scene.id }, 'narrative')
                }
              >
                ← Show everything
              </button>
            )}
          </div>
        </div>
      }
      timeline={
        <TimelineView
          scene={scene}
          focus={focus}
          onSelectFocus={(f) => setFocus(f, 'timeline')}
        />
      }
      narrative={
        <NarrativeView
          scene={scene}
          focus={focus}
          onSelectFocus={(f) => setFocus(f, 'narrative')}
        />
      }
      map={
        <MapView
          scene={scene}
          focus={focus}
          onSelectFocus={(f) => setFocus(f, 'map')}
        />
      }
      graph={
        <GraphView
          scene={scene}
          focus={focus}
          onSelectFocus={(f) => setFocus(f, 'graph')}
        />
      }
      evidence={
        <EvidencePanel
          scene={scene}
          focus={focus}
          onSelectFocus={(f) => setFocus(f, 'evidence')}
        />
      }
    />
  )
}
