import { useRef, type KeyboardEvent, type ReactNode } from 'react'
import type { PanelTab } from '../../model/experiencePlan'

const TABS: { id: PanelTab; label: string }[] = [
  { id: 'ask', label: 'Ask' },
  { id: 'explore', label: 'Explore' },
  { id: 'evidence', label: 'Evidence' },
  { id: 'sources', label: 'Sources' },
]

/** The docked panel's and bottom sheet's shared tab strip — the exact same
 * WAI-ARIA Tabs pattern (roving tabindex, Left/Right/Home/End) already
 * proven in InvestigationLayout's Map/Graph toggle, generalized to 4 tabs. */
export function PanelTabs({
  activeTab,
  onSelectTab,
  children,
}: {
  activeTab: PanelTab
  onSelectTab: (tab: PanelTab) => void
  children: ReactNode
}) {
  const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({})

  function focusAndSelect(id: PanelTab) {
    onSelectTab(id)
    tabRefs.current[id]?.focus()
  }

  function handleKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    const currentIndex = TABS.findIndex((t) => t.id === activeTab)
    if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
      event.preventDefault()
      const direction = event.key === 'ArrowRight' ? 1 : -1
      const nextIndex = (currentIndex + direction + TABS.length) % TABS.length
      focusAndSelect(TABS[nextIndex].id)
    } else if (event.key === 'Home') {
      event.preventDefault()
      focusAndSelect(TABS[0].id)
    } else if (event.key === 'End') {
      event.preventDefault()
      focusAndSelect(TABS[TABS.length - 1].id)
    }
  }

  return (
    <div className="chronicle-panel-tabs">
      <div
        role="tablist"
        aria-label="Investigation panel"
        className="chronicle-panel-tablist"
      >
        {TABS.map((tab) => (
          <button
            key={tab.id}
            ref={(el) => {
              tabRefs.current[tab.id] = el
            }}
            id={`panel-tab-${tab.id}`}
            role="tab"
            type="button"
            aria-selected={activeTab === tab.id}
            aria-controls={`panel-tabpanel-${tab.id}`}
            tabIndex={activeTab === tab.id ? 0 : -1}
            className={`chronicle-panel-tab ${activeTab === tab.id ? 'is-active' : ''}`}
            onClick={() => focusAndSelect(tab.id)}
            onKeyDown={handleKeyDown}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div
        id={`panel-tabpanel-${activeTab}`}
        role="tabpanel"
        aria-labelledby={`panel-tab-${activeTab}`}
        tabIndex={0}
        className="chronicle-panel-tabcontent"
      >
        {children}
      </div>
    </div>
  )
}
