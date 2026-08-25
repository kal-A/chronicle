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
  question,
  ask,
  explore,
  evidence,
  sources,
  initialTab,
}: {
  question: string
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
      className={`chronicle-bottom-sheet lg:hidden ${HEIGHT_CLASS[sheetState]}`}
    >
      <button
        type="button"
        className="chronicle-bottom-sheet__handle"
        aria-label={`Investigation panel is ${sheetState}. Activate to show more or less.`}
        onClick={() => setSheetState((current) => NEXT_STATE[current])}
      >
        <span aria-hidden="true" />
      </button>
      {sheetState !== 'collapsed' && (
        <>
          <div className="chronicle-panel-question chronicle-panel-question--mobile">
            <p>{question}</p>
            <strong>Investigation ready</strong>
          </div>
          <PanelTabs activeTab={tab} onSelectTab={setTab}>
            {panelContent[tab]}
          </PanelTabs>
        </>
      )}
    </div>
  )
}
