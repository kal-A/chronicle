import { useEffect, useRef } from 'react'
import type { Core } from 'cytoscape'
import type { Scene, Relationship, EvidenceClassification } from '../model/schema'
import type { FocusValue } from '../model/focus'

const CLASSIFICATION_LABEL: Record<EvidenceClassification, string> = {
  directly_supported: 'directly supported',
  indirectly_supported: 'indirectly supported',
  contextual: 'contextual',
  correlational: 'correlational',
  disputed: 'disputed',
  speculative: 'speculative',
  insufficient_evidence: 'insufficient evidence',
}

function claimIndexLabel(scene: Scene, claimId: string): string {
  const index = scene.claims.findIndex((c) => c.id === claimId)
  return index === -1 ? '?' : String(index + 1)
}

/**
 * Focused local relationship graph — only claims/relationships that actually
 * exist in reviewed/prototype-curated content are shown (never a fabricated
 * edge to make the graph look more connected than the evidence supports;
 * docs/product/product-principles.md's "unreadable graph" rule + AGENTS.md
 * §3). A claim with no stated relationship yet renders as an isolated node —
 * that's honest, not a bug.
 *
 * The canvas deliberately shows numbered nodes (1, 2, 3…) rather than
 * shrinking full claim text to illegible font sizes — the numbers key
 * directly to the accessible, full-text list below, which remains the
 * first-class interaction (docs/design/accessibility.md).
 *
 * Zoom/pan/drag are genuinely enabled (Obsidian-style exploration) with a
 * force-directed `cose` layout — a static, non-interactive canvas was the
 * wrong tradeoff when fixing the earlier illegibility problem. Clicking a
 * node mirrors the list button below it.
 */
export function GraphView({
  scene,
  focus,
  onSelectFocus,
}: {
  scene: Scene
  focus: FocusValue
  onSelectFocus: (focus: FocusValue) => void
}) {
  const canvasRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<Core | null>(null)
  const onSelectFocusRef = useRef(onSelectFocus)
  onSelectFocusRef.current = onSelectFocus

  useEffect(() => {
    let cancelled = false

    async function initCytoscape() {
      if (!canvasRef.current) return
      try {
        const { default: cytoscape } = await import('cytoscape')
        if (cancelled || !canvasRef.current) return

        const nodes = scene.claims.map((c, i) => ({
          data: { id: c.id, label: String(i + 1) },
        }))
        const edges = scene.relationships.map((r) => ({
          data: { id: r.id, source: r.fromId, target: r.toId },
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
                'font-size': 16,
                'font-weight': 'bold',
                color: '#ffffff',
                'text-valign': 'center',
                'text-halign': 'center',
                'background-color': '#2563eb',
                width: 36,
                height: 36,
                'border-width': 2,
                'border-color': '#1d4ed8',
              },
            },
            {
              selector: 'node.focused',
              style: {
                'border-width': 4,
                'border-color': '#f59e0b',
                width: 44,
                height: 44,
              },
            },
            {
              selector: 'edge',
              style: {
                width: 3,
                'line-style': 'dashed',
                'line-color': '#d97706',
                'target-arrow-shape': 'triangle',
                'target-arrow-color': '#d97706',
                'curve-style': 'bezier',
              },
            },
          ],
          layout: { name: 'cose', animate: true, padding: 24 },
        })

        cyRef.current.on('tap', 'node', (event) => {
          const claimId = event.target.id() as string
          onSelectFocusRef.current({ kind: 'claim', claimId })
        })
      } catch {
        // Canvas rendering is a visual enhancement only — jsdom (tests) and
        // any environment without canvas support fall back gracefully to
        // the accessible list below, which is the first-class interaction.
      }
    }

    void initCytoscape()
    return () => {
      cancelled = true
      cyRef.current?.destroy()
      cyRef.current = null
    }
  }, [scene])

  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return
    cy.nodes().removeClass('focused')
    if (focus.kind === 'claim') {
      cy.getElementById(focus.claimId).addClass('focused')
    }
  }, [focus])

  const relationships: Relationship[] = scene.relationships

  return (
    <div className="flex flex-col gap-3">
      <div
        ref={canvasRef}
        aria-hidden="true"
        className="h-56 w-full rounded-lg border border-neutral-200 bg-neutral-50 dark:border-neutral-800 dark:bg-neutral-950"
      />
      {relationships.length > 0 && (
        <p aria-hidden="true" className="-mt-1 text-xs text-neutral-500 dark:text-neutral-400">
          Dashed line = a curated, classified relationship. Numbers match the list below.
        </p>
      )}

      <nav aria-label="Claims and relationships in this scene">
        <ul className="flex flex-col gap-2">
          {scene.claims.map((claim, i) => {
            const isFocused = focus.kind === 'claim' && focus.claimId === claim.id
            return (
              <li key={claim.id}>
                <button
                  type="button"
                  aria-current={isFocused ? 'true' : undefined}
                  className={`flex w-full items-start gap-2 rounded-lg border p-2 text-left text-xs transition-colors ${
                    isFocused
                      ? 'border-blue-600 border-l-4 bg-blue-50 dark:bg-blue-950/40'
                      : 'border-neutral-200 hover:bg-neutral-50 dark:border-neutral-800 dark:hover:bg-neutral-900'
                  }`}
                  onClick={() =>
                    onSelectFocus({
                      kind: 'claim',
                      claimId: claim.id,
                    })
                  }
                >
                  <span className="flex h-5 w-5 flex-none items-center justify-center rounded-full bg-blue-600 text-[10px] font-bold text-white">
                    {i + 1}
                  </span>
                  <span>{claim.statement}</span>
                </button>
              </li>
            )
          })}
        </ul>

        {relationships.length === 0 ? (
          <p className="mt-2 text-xs text-neutral-500 dark:text-neutral-400">
            No relationships between these claims have been curated yet.
          </p>
        ) : (
          <ul className="mt-2 flex flex-col gap-1">
            {relationships.map((rel) => {
              const isFocused =
                focus.kind === 'relationship' &&
                focus.relationshipId === rel.id
              return (
                <li key={rel.id}>
                  <button
                    type="button"
                    aria-current={isFocused ? 'true' : undefined}
                    className={`w-full rounded-lg border border-dashed p-2 text-left text-xs ${
                      isFocused
                        ? 'border-blue-600 border-l-4 bg-blue-50 dark:bg-blue-950/40'
                        : 'border-amber-400 bg-amber-50/60 dark:border-amber-700 dark:bg-amber-950/20'
                    }`}
                    onClick={() =>
                      onSelectFocus({
                        kind: 'relationship',
                        relationshipId: rel.id,
                      })
                    }
                  >
                    <span className="block">
                      <strong>{claimIndexLabel(scene, rel.fromId)}</strong>
                      {' → '}
                      <strong>{claimIndexLabel(scene, rel.toId)}</strong>
                      {': '}
                      {rel.relationshipType}
                    </span>
                    <span className="mt-1 block font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-400">
                      {CLASSIFICATION_LABEL[rel.evidenceClassification]}
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
