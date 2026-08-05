import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useFocus } from '../focus/useFocus'
import { InvestigationLayout } from '../InvestigationLayout'
import { NarrativeView } from '../narrative/NarrativeView'
import { TimelineView } from '../timeline/TimelineView'
import { MapView } from '../map/MapView'
import { GraphView } from '../graph/GraphView'
import { EvidencePanel } from '../evidence/EvidencePanel'
import { describeFocus } from '../model/describeFocus'
import type { Scene } from '../model/schema'

/**
 * The original article-first renderer (docs/design/investigation-layout.md's
 * "Primary Layout — Inspector mode"), preserved unchanged per
 * docs/decisions/ADR-002-map-first-workspace.md rather than deleted: full
 * narrative, deep evidence/provenance, and the numbered claim-ledger graph.
 * Reachable from the map-first workspace, not the default entry point.
 */
export function InspectorView({
  scene,
  investigationTitle,
  workspaceHref,
}: {
  scene: Scene
  investigationTitle: string
  workspaceHref: string
}) {
  const { focus, setFocus } = useFocus()
  const isWholeScene = focus.kind === 'scene'

  useEffect(() => {
    document.title = `${investigationTitle} · Inspector · Chronicle`
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
              Chronicle Inspector
            </h1>
            <p className="text-sm text-neutral-500 dark:text-neutral-400">{investigationTitle}</p>
          </div>
          <div className="flex flex-col items-end gap-1 text-right">
            <p role="status" aria-live="polite" className="text-xs text-neutral-500 dark:text-neutral-400">
              {describeFocus(focus, scene)}
            </p>
            <div className="flex gap-2">
              {!isWholeScene && (
                <button
                  type="button"
                  className="rounded border border-neutral-300 px-2 py-1 text-xs font-medium text-neutral-700 hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
                  onClick={() => setFocus({ kind: 'scene', sceneId: scene.id }, 'narrative')}
                >
                  ← Show everything
                </button>
              )}
              <Link
                to={workspaceHref}
                className="rounded border border-neutral-300 px-2 py-1 text-xs font-medium text-neutral-700 hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
              >
                ← Back to workspace
              </Link>
            </div>
          </div>
        </div>
      }
      timeline={
        <TimelineView scene={scene} focus={focus} onSelectFocus={(f) => setFocus(f, 'timeline')} />
      }
      narrative={
        <NarrativeView scene={scene} focus={focus} onSelectFocus={(f) => setFocus(f, 'narrative')} />
      }
      map={<MapView scene={scene} focus={focus} onSelectFocus={(f) => setFocus(f, 'map')} />}
      graph={<GraphView scene={scene} focus={focus} onSelectFocus={(f) => setFocus(f, 'graph')} />}
      evidence={
        <EvidencePanel scene={scene} focus={focus} onSelectFocus={(f) => setFocus(f, 'evidence')} />
      }
    />
  )
}
