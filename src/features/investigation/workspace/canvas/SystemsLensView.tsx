import { useEffect, useRef } from 'react'
import type { Core } from 'cytoscape'
import type { Scene, EvidenceClassification } from '../../model/schema'
import type { SystemPath } from '../../model/experiencePlan'
import type { FocusValue } from '../../model/focus'

const CLASSIFICATION_LABEL: Record<EvidenceClassification, string> = {
  directly_supported: 'directly supported',
  indirectly_supported: 'indirectly supported',
  contextual: 'contextual',
  correlational: 'correlational',
  disputed: 'disputed',
  speculative: 'speculative',
  insufficient_evidence: 'insufficient evidence',
}

/** Evidence-strength encoded by line style, never color alone (AGENTS.md §12,
 * map-first-workspace-instructions.md §13.3) — the classification label text
 * below each edge is the load-bearing signal; the style is a visual echo. */
const CLASSIFICATION_LINE_STYLE: Record<EvidenceClassification, string> = {
  directly_supported: 'solid',
  indirectly_supported: 'dashed',
  disputed: 'dashed',
  contextual: 'dotted',
  correlational: 'dotted',
  speculative: 'dotted',
  insufficient_evidence: 'dotted',
}

function labelForNode(scene: Scene, nodeId: string): string {
  const entity = scene.entities.find((e) => e.id === nodeId)
  if (entity) return entity.canonicalName
  const event = scene.events.find((e) => e.id === nodeId)
  if (event) return event.title
  const claim = scene.claims.find((c) => c.id === nodeId)
  if (claim) return claim.statement.length > 70 ? `${claim.statement.slice(0, 67)}…` : claim.statement
  const source = scene.sources.find((s) => s.id === nodeId)
  if (source) return source.title
  return nodeId
}

/**
 * The Systems lens's canvas — labelled historical objects and readable edge
 * verbs (map-first-workspace-instructions.md §13), replacing the numbered-
 * claim-graph GraphView uses (that view is preserved, unchanged, as
 * Inspector's claim-ledger graph — see docs/decisions/ADR-002-map-first-
 * workspace.md). Node labels resolve from whichever scene collection the id
 * actually belongs to (entity/event/claim/source) since a SystemPath's
 * nodeIds are deliberately heterogeneous.
 */
export function SystemsLensView({
  scene,
  systemPath,
  focus,
  onSelectFocus,
}: {
  scene: Scene
  systemPath: SystemPath
  focus: FocusValue
  onSelectFocus: (focus: FocusValue) => void
}) {
  const canvasRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<Core | null>(null)
  const onSelectFocusRef = useRef(onSelectFocus)
  onSelectFocusRef.current = onSelectFocus

  const relationships = scene.relationships.filter((relationship) =>
    systemPath.relationshipIds.includes(relationship.id),
  )

  useEffect(() => {
    let cancelled = false

    async function initCytoscape() {
      if (!canvasRef.current) return
      try {
        const { default: cytoscape } = await import('cytoscape')
        if (cancelled || !canvasRef.current) return

        const nodes = systemPath.nodeIds.map((id) => ({
          data: { id, label: labelForNode(scene, id) },
        }))
        const edges = relationships.map((relationship) => ({
          data: {
            id: relationship.id,
            source: relationship.fromId,
            target: relationship.toId,
            label: relationship.relationshipType,
          },
          classes: CLASSIFICATION_LINE_STYLE[relationship.evidenceClassification],
        }))

        cyRef.current = cytoscape({
          container: canvasRef.current,
          elements: [...nodes, ...edges],
          userZoomingEnabled: true,
          userPanningEnabled: true,
          boxSelectionEnabled: false,
          minZoom: 0.5,
          maxZoom: 2.5,
          style: [
            {
              selector: 'node',
              style: {
                label: 'data(label)',
                'font-size': 11,
                'font-weight': 'bold',
                color: '#ffffff',
                'text-valign': 'center',
                'text-halign': 'center',
                'text-wrap': 'wrap',
                'text-max-width': '80px',
                'background-color': '#2563eb',
                width: 90,
                height: 90,
                shape: 'round-rectangle',
                'border-width': 2,
                'border-color': '#1d4ed8',
              },
            },
            {
              selector: 'node.focused',
              style: { 'border-width': 4, 'border-color': '#f59e0b' },
            },
            {
              selector: 'edge',
              style: {
                width: 3,
                label: 'data(label)',
                'font-size': 10,
                color: '#92400e',
                'text-background-color': '#fffbeb',
                'text-background-opacity': 1,
                'line-color': '#d97706',
                'target-arrow-shape': 'triangle',
                'target-arrow-color': '#d97706',
                'curve-style': 'bezier',
              },
            },
            { selector: 'edge.dashed', style: { 'line-style': 'dashed' } },
            { selector: 'edge.dotted', style: { 'line-style': 'dotted' } },
            { selector: 'edge.solid', style: { 'line-style': 'solid' } },
          ],
          layout: { name: 'cose', animate: true, padding: 32 },
        })

        cyRef.current.on('tap', 'node', (event) => {
          const nodeId = event.target.id() as string
          if (scene.claims.some((claim) => claim.id === nodeId)) {
            onSelectFocusRef.current({ kind: 'claim', claimId: nodeId })
          } else if (scene.events.some((e) => e.id === nodeId)) {
            onSelectFocusRef.current({ kind: 'event', eventId: nodeId })
          } else if (scene.entities.some((e) => e.id === nodeId)) {
            const entity = scene.entities.find((e) => e.id === nodeId)!
            onSelectFocusRef.current({ kind: 'entity', entityId: nodeId, entityType: entity.entityType })
          }
        })
        cyRef.current.on('tap', 'edge', (event) => {
          onSelectFocusRef.current({ kind: 'relationship', relationshipId: event.target.id() as string })
        })
      } catch {
        // Progressive enhancement only — see the accessible list below.
      }
    }

    void initCytoscape()
    return () => {
      cancelled = true
      cyRef.current?.destroy()
      cyRef.current = null
    }
  }, [scene, systemPath, relationships])

  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return
    cy.nodes().removeClass('focused')
    if (focus.kind === 'claim') cy.getElementById(focus.claimId).addClass('focused')
    if (focus.kind === 'event') cy.getElementById(focus.eventId).addClass('focused')
    if (focus.kind === 'entity') cy.getElementById(focus.entityId).addClass('focused')
  }, [focus])

  return (
    <div className="flex flex-col gap-3">
      <div>
        <h2 className="text-sm font-semibold text-neutral-900 dark:text-neutral-50">{systemPath.title}</h2>
        <p className="text-xs text-neutral-500 dark:text-neutral-400">{systemPath.summary}</p>
      </div>
      <div
        ref={canvasRef}
        aria-hidden="true"
        className="h-64 w-full rounded-lg border border-neutral-200 bg-neutral-50 dark:border-neutral-800 dark:bg-neutral-950"
      />

      <nav aria-label={`${systemPath.title}: nodes and relationships`}>
        <ol className="flex flex-col gap-1">
          {systemPath.nodeIds.map((nodeId) => (
            <li key={nodeId} className="text-xs text-neutral-700 dark:text-neutral-300">
              {labelForNode(scene, nodeId)}
            </li>
          ))}
        </ol>
        {relationships.length > 0 && (
          <ul className="mt-2 flex flex-col gap-1">
            {relationships.map((relationship) => {
              const isFocused = focus.kind === 'relationship' && focus.relationshipId === relationship.id
              return (
                <li key={relationship.id}>
                  <button
                    type="button"
                    aria-current={isFocused ? 'true' : undefined}
                    className={`w-full rounded-lg border border-dashed p-2 text-left text-xs ${
                      isFocused
                        ? 'border-blue-600 border-l-4 bg-blue-50 dark:bg-blue-950/40'
                        : 'border-amber-400 bg-amber-50/60 dark:border-amber-700 dark:bg-amber-950/20'
                    }`}
                    onClick={() => onSelectFocus({ kind: 'relationship', relationshipId: relationship.id })}
                  >
                    <span className="block">
                      {labelForNode(scene, relationship.fromId)} — {relationship.relationshipType} →{' '}
                      {labelForNode(scene, relationship.toId)}
                    </span>
                    <span className="mt-1 block font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-400">
                      {CLASSIFICATION_LABEL[relationship.evidenceClassification]}
                    </span>
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </nav>
    </div>
  )
}
