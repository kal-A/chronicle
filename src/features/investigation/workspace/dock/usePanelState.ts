import { useCallback, useEffect, useState } from 'react'
import type { PanelTab } from '../../model/experiencePlan'

const WIDTH_STORAGE_KEY = 'chronicle.workspace.panelWidth'
const COLLAPSED_STORAGE_KEY = 'chronicle.workspace.panelCollapsed'

export const MIN_PANEL_WIDTH = 320
export const RESIZE_STEP = 24

function readStoredWidth(defaultWidth: number): number {
  if (typeof window === 'undefined') return defaultWidth
  const stored = Number(window.localStorage.getItem(WIDTH_STORAGE_KEY))
  return Number.isFinite(stored) && stored >= MIN_PANEL_WIDTH ? stored : defaultWidth
}

function readStoredCollapsed(): boolean {
  if (typeof window === 'undefined') return false
  return window.localStorage.getItem(COLLAPSED_STORAGE_KEY) === 'true'
}

/** Panel chrome (tab/width/collapsed) is device-local UI state, not
 * investigation state — deliberately NOT URL-persisted (unlike Focus and the
 * active lens), but width/collapsed persist locally across sessions per
 * map-first-workspace-instructions.md §8.1. */
export function usePanelState(initialTab: PanelTab, defaultWidth: number, workspaceWidthPx: number) {
  const [tab, setTab] = useState<PanelTab>(initialTab)
  const [width, setWidthState] = useState(() => readStoredWidth(defaultWidth))
  const [collapsed, setCollapsed] = useState(readStoredCollapsed)

  useEffect(() => {
    window.localStorage.setItem(WIDTH_STORAGE_KEY, String(width))
  }, [width])
  useEffect(() => {
    window.localStorage.setItem(COLLAPSED_STORAGE_KEY, String(collapsed))
  }, [collapsed])

  const maxWidth = Math.max(MIN_PANEL_WIDTH, Math.floor(workspaceWidthPx / 2))

  const setWidth = useCallback(
    (next: number) => {
      setWidthState(Math.min(maxWidth, Math.max(MIN_PANEL_WIDTH, next)))
    },
    [maxWidth],
  )

  const resizeBy = useCallback((delta: number) => setWidth(width + delta), [width, setWidth])
  const resetWidth = useCallback(() => setWidth(defaultWidth), [setWidth, defaultWidth])
  const collapse = useCallback(() => setCollapsed(true), [])
  const reopen = useCallback(() => setCollapsed(false), [])

  return { tab, setTab, width, setWidth, maxWidth, collapsed, collapse, reopen, resizeBy, resetWidth }
}
