import { useRef, type KeyboardEvent, type ReactNode } from 'react'
import { PanelTabs } from './PanelTabs'
import { MIN_PANEL_WIDTH, RESIZE_STEP, usePanelState } from './usePanelState'
import type { PanelTab } from '../../model/experiencePlan'

/**
 * Desktop-only (see InvestigationWorkspace's `hidden lg:flex` gate —
 * BottomSheet covers mobile/tablet-portrait). Resizable via a keyboard-
 * operable `role="separator"` divider (arrow keys, Home/End to min/max,
 * Enter to collapse) and mouse drag; collapses to an icon rail without
 * losing tab/width state (map-first-workspace-instructions.md §8.1). Focus
 * moves to the reopen button on collapse and back to the divider on reopen —
 * fixing, not repeating, SourceDetail's missing focus-management gap.
 */
export function DockedPanel({
  question,
  scopeSummary,
  ask,
  explore,
  evidence,
  sources,
  initialTab,
  defaultWidth,
  workspaceWidthPx,
}: {
  question: string
  scopeSummary?: string
  ask: ReactNode
  explore: ReactNode
  evidence: ReactNode
  sources: ReactNode
  initialTab: PanelTab
  defaultWidth: number
  workspaceWidthPx: number
}) {
  const { tab, setTab, width, setWidth, maxWidth, collapsed, collapse, reopen, resizeBy, resetWidth } =
    usePanelState(initialTab, defaultWidth, workspaceWidthPx)
  const dragStateRef = useRef<{ startX: number; startWidth: number } | null>(null)
  const reopenButtonRef = useRef<HTMLButtonElement>(null)
  const separatorRef = useRef<HTMLDivElement>(null)

  function handlePointerDown(event: React.PointerEvent<HTMLDivElement>) {
    dragStateRef.current = { startX: event.clientX, startWidth: width }
    event.currentTarget.setPointerCapture(event.pointerId)
  }

  function handlePointerMove(event: React.PointerEvent<HTMLDivElement>) {
    if (!dragStateRef.current) return
    const delta = dragStateRef.current.startX - event.clientX
    setWidth(dragStateRef.current.startWidth + delta)
  }

  function handlePointerUp() {
    dragStateRef.current = null
  }

  function handleSeparatorKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === 'ArrowLeft') {
      event.preventDefault()
      resizeBy(RESIZE_STEP)
    } else if (event.key === 'ArrowRight') {
      event.preventDefault()
      resizeBy(-RESIZE_STEP)
    } else if (event.key === 'Home') {
      event.preventDefault()
      setWidth(MIN_PANEL_WIDTH)
    } else if (event.key === 'End') {
      event.preventDefault()
      setWidth(maxWidth)
    } else if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      collapse()
      requestAnimationFrame(() => reopenButtonRef.current?.focus())
    }
  }

  function handleReopen() {
    reopen()
    requestAnimationFrame(() => separatorRef.current?.focus())
  }

  if (collapsed) {
    return (
      <div className="chronicle-dock-rail hidden flex-none lg:flex">
        <button
          ref={reopenButtonRef}
          type="button"
          aria-label="Reopen investigation panel"
          aria-expanded="false"
          className="chronicle-panel-reopen"
          onClick={handleReopen}
        >
          <span aria-hidden="true">«</span>
        </button>
      </div>
    )
  }

  const panelContent: Record<PanelTab, ReactNode> = { ask, explore, evidence, sources }

  return (
    <div className="chronicle-dock hidden flex-none lg:flex" style={{ width }}>
      <div
        ref={separatorRef}
        role="separator"
        aria-label="Resize investigation panel"
        aria-orientation="vertical"
        aria-valuenow={width}
        aria-valuemin={MIN_PANEL_WIDTH}
        aria-valuemax={maxWidth}
        tabIndex={0}
        className="chronicle-panel-resizer"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onDoubleClick={resetWidth}
        onKeyDown={handleSeparatorKeyDown}
      />
      <section
        aria-label="Investigation panel"
        aria-expanded="true"
        className="chronicle-panel-shell"
      >
        <div className="chronicle-panel-utility">
          <button
            type="button"
            aria-label="Collapse investigation panel"
            className="chronicle-panel-collapse"
            onClick={() => {
              collapse()
              requestAnimationFrame(() => reopenButtonRef.current?.focus())
            }}
          >
            Collapse »
          </button>
        </div>
        <div className="chronicle-panel-question">
          <p>{question}</p>
          {scopeSummary ? <span>{scopeSummary}</span> : null}
          <strong>Investigation ready</strong>
        </div>
        <PanelTabs activeTab={tab} onSelectTab={setTab}>
          {panelContent[tab]}
        </PanelTabs>
      </section>
    </div>
  )
}
