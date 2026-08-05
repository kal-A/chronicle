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
    <div className="flex h-full min-h-0 flex-col">
      <div
        role="tablist"
        aria-label="Investigation panel"
        className="flex flex-none border-b border-neutral-200 dark:border-neutral-800"
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
            className={`flex-1 px-2 py-2 text-sm font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-blue-600 ${
              activeTab === tab.id
                ? 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300'
                : 'text-neutral-500 hover:bg-neutral-50 dark:text-neutral-400 dark:hover:bg-neutral-800'
            }`}
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
        className="min-h-0 flex-1 overflow-y-auto p-3"
      >
        {children}
      </div>
    </div>
  )
}
