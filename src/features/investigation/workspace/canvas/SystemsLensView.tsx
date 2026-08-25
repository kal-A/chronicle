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
                color: '#f0e7d5',
                'text-valign': 'center',
                'text-halign': 'center',
                'text-wrap': 'wrap',
                'text-max-width': '80px',
                'background-color': '#173f56',
                width: 90,
                height: 90,
                shape: 'round-rectangle',
                'border-width': 2,
                'border-color': '#72a8b5',
              },
            },
            {
              selector: 'node.focused',
              style: { 'border-width': 3, 'border-color': '#c45e3c' },
            },
            {
              selector: 'edge',
              style: {
                width: 3,
                label: 'data(label)',
                'font-size': 10,
                color: '#e9dec5',
                'text-background-color': '#06121b',
                'text-background-opacity': 1,
                'line-color': '#c45e3c',
                'target-arrow-shape': 'triangle',
                'target-arrow-color': '#c45e3c',
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
    <div className="chronicle-systems-lens">
      <div>
        <h2>{systemPath.title}</h2>
        <p>{systemPath.summary}</p>
      </div>
      <div
        ref={canvasRef}
        aria-hidden="true"
        className="chronicle-systems-canvas"
      />

      <nav aria-label={`${systemPath.title}: nodes and relationships`}>
        <ol className="chronicle-system-node-list">
          {systemPath.nodeIds.map((nodeId) => (
            <li key={nodeId}>
              {labelForNode(scene, nodeId)}
            </li>
          ))}
        </ol>
        {relationships.length > 0 && (
          <ul className="chronicle-system-relationships">
            {relationships.map((relationship) => {
              const isFocused = focus.kind === 'relationship' && focus.relationshipId === relationship.id
              return (
                <li key={relationship.id}>
                  <button
                    type="button"
                    aria-current={isFocused ? 'true' : undefined}
                    className={`chronicle-system-relationship ${isFocused ? 'is-focused' : ''}`}
                    onClick={() => onSelectFocus({ kind: 'relationship', relationshipId: relationship.id })}
                  >
                    <span className="block">
                      {labelForNode(scene, relationship.fromId)} — {relationship.relationshipType} →{' '}
                      {labelForNode(scene, relationship.toId)}
                    </span>
                    <span className="chronicle-system-classification">
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
