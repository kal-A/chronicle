import { useState, type ReactNode } from 'react'
import { PanelTabs } from './PanelTabs'
import type { PanelTab } from '../../model/experiencePlan'

type SheetState = 'collapsed' | 'half' | 'expanded'

const HEIGHT_CLASS: Record<SheetState, string> = {
  collapsed: 'h-14',
  half: 'h-[50vh]',
  expanded: 'h-[85vh]',
}

const NEXT_STATE: Record<SheetState, SheetState> = {
  collapsed: 'half',
  half: 'expanded',
  expanded: 'collapsed',
}

/** Mobile/tablet-portrait equivalent of DockedPanel (see InvestigationWorkspace's
 * `lg:hidden` gate). The drag handle is a real button, not gesture-only —
 * activating it cycles collapsed -> half -> expanded -> collapsed, so it's
 * keyboard- and screen-reader-operable per map-first-workspace-
 * instructions.md §9.1/§17.2, not just draggable. */
export function BottomSheet({
  ask,
  explore,
  evidence,
  sources,
  initialTab,
}: {
  ask: ReactNode
  explore: ReactNode
  evidence: ReactNode
  sources: ReactNode
  initialTab: PanelTab
}) {
  const [tab, setTab] = useState<PanelTab>(initialTab)
  const [sheetState, setSheetState] = useState<SheetState>('half')

  const panelContent: Record<PanelTab, ReactNode> = { ask, explore, evidence, sources }

  return (
    <div
      className={`flex flex-none flex-col overflow-hidden rounded-t-lg border border-neutral-200 bg-white transition-[height] duration-200 motion-reduce:transition-none lg:hidden ${HEIGHT_CLASS[sheetState]} dark:border-neutral-800 dark:bg-neutral-900`}
    >
      <button
        type="button"
        className="flex flex-none items-center justify-center py-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-600"
        aria-label={`Investigation panel is ${sheetState}. Activate to show more or less.`}
        onClick={() => setSheetState((current) => NEXT_STATE[current])}
      >
        <span aria-hidden="true" className="h-1 w-10 rounded-full bg-neutral-300 dark:bg-neutral-700" />
      </button>
      {sheetState !== 'collapsed' && (
        <PanelTabs activeTab={tab} onSelectTab={setTab}>
          {panelContent[tab]}
        </PanelTabs>
      )}
    </div>
  )
}
