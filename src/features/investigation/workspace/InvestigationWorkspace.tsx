import { useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useFocus } from '../focus/useFocus'
import { MapView } from '../map/MapView'
import { TimelineView } from '../timeline/TimelineView'
import { describeFocus } from '../model/describeFocus'
import type { Scene } from '../model/schema'
import type { GeneratedInvestigation } from '../model/generatedInvestigation'
import { WorkspaceHeader } from './WorkspaceHeader'
import { DockedPanel } from './dock/DockedPanel'
import { BottomSheet } from './dock/BottomSheet'
import { AskTab } from './panel/AskTab'
import { ExploreTab } from './panel/ExploreTab'
import { EvidenceTab } from './panel/EvidenceTab'
import { SourcesTab } from './panel/SourcesTab'
import { SystemsLensView } from './canvas/SystemsLensView'
import { resolveLenses, sceneScopeLens } from './lenses/lensResolution'
import { useActiveLensId } from './lenses/useActiveLensId'

/** A reasonable default for the panel's max-width clamp — this workspace
 * doesn't track live viewport width via ResizeObserver (kept simple for
 * D0.3); the panel's own min/max/keyboard-resize behavior is what matters
 * for the completion criteria, not pixel-perfect clamping against the
 * actual rendered width. */
const ASSUMED_WORKSPACE_WIDTH_PX = 1024

export function InvestigationWorkspace({
  investigation,
  scene,
}: {
  investigation: GeneratedInvestigation
  scene: Scene
}) {
  const { focus, setFocus } = useFocus()
  const navigate = useNavigate()
  const isWholeScene = focus.kind === 'scene'

  useEffect(() => {
    document.title = `${investigation.presentation.title} · Chronicle`
    return () => {
      document.title = 'Chronicle'
    }
  }, [investigation.presentation.title])

  const lenses = useMemo(() => resolveLenses(investigation, scene), [investigation, scene])
  const defaultLensId = investigation.experiencePlan?.workspace.initialLensId ?? lenses[0].id
  const [activeLensId, setActiveLensId] = useActiveLensId(defaultLensId)
  const activeLens = lenses.find((lens) => lens.id === activeLensId) ?? lenses[0]
  const scoped = useMemo(() => sceneScopeLens(activeLens, scene), [activeLens, scene])

  const systemPath = investigation.experiencePlan?.systemPaths.find(
    (path) => path.lensId === activeLens.id,
  )

  const inspectorHref = `/investigations/${encodeURIComponent(investigation.packageId)}/scenes/${encodeURIComponent(scene.id)}/inspector`

  return (
    <main className="mx-auto flex min-h-svh max-w-6xl flex-col gap-4 p-4 md:p-8">
      <header className="border-b border-neutral-200 pb-4 dark:border-neutral-800">
        <WorkspaceHeader
          investigationTitle={investigation.presentation.title}
          lenses={lenses}
          activeLensId={activeLens.id}
          onSelectLens={setActiveLensId}
          inspectorHref={inspectorHref}
          focusDescription={describeFocus(focus, scene)}
        />
        {!isWholeScene && (
          <button
            type="button"
            className="mt-2 rounded border border-neutral-300 px-2 py-1 text-xs font-medium text-neutral-700 hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
            onClick={() => setFocus({ kind: 'scene', sceneId: scene.id }, 'url')}
          >
            ← Show everything
          </button>
        )}
      </header>

      <div className="rounded-lg border border-neutral-200 bg-white p-3 dark:border-neutral-800 dark:bg-neutral-900">
        <TimelineView
          scene={scene}
          focus={focus}
          onSelectFocus={(f) => setFocus(f, 'timeline')}
          eventIds={scoped.eventIds}
        />
      </div>

      <div className="flex flex-1 flex-col gap-4 lg:flex-row lg:items-start">
        <div className="min-w-0 flex-1 rounded-lg border border-neutral-200 bg-white p-3 dark:border-neutral-800 dark:bg-neutral-900">
          {activeLens.visualizationType === 'graph' && systemPath ? (
            <SystemsLensView
              scene={scene}
              systemPath={systemPath}
              focus={focus}
              onSelectFocus={(f) => setFocus(f, 'graph')}
            />
          ) : (
            <MapView
              scene={scene}
              focus={focus}
              onSelectFocus={(f) => setFocus(f, 'map')}
              placeIds={scoped.placeIds}
            />
          )}
        </div>

        <DockedPanel
          ask={<AskTab />}
          explore={<ExploreTab investigation={investigation} lens={activeLens} />}
          evidence={
            <EvidenceTab
              scene={scene}
              focus={focus}
              onOpenInspector={() => navigate(inspectorHref)}
            />
          }
          sources={<SourcesTab scene={scene} />}
          initialTab={investigation.experiencePlan?.workspace.initialPanelTab ?? 'explore'}
          defaultWidth={investigation.experiencePlan?.workspace.defaultPanelWidth ?? 380}
          workspaceWidthPx={ASSUMED_WORKSPACE_WIDTH_PX}
        />
      </div>

      <BottomSheet
        ask={<AskTab />}
        explore={<ExploreTab investigation={investigation} lens={activeLens} />}
        evidence={
          <EvidenceTab scene={scene} focus={focus} onOpenInspector={() => navigate(inspectorHref)} />
        }
        sources={<SourcesTab scene={scene} />}
        initialTab={investigation.experiencePlan?.workspace.initialPanelTab ?? 'explore'}
      />
    </main>
  )
}
