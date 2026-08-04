import { useRef, useState, type KeyboardEvent, type ReactNode } from 'react'

const TABS = [
  { id: 'map', label: 'Map' },
  { id: 'graph', label: 'Relationships' },
] as const
type SecondaryView = (typeof TABS)[number]['id']

/**
 * Responsive investigation shell per docs/design/investigation-layout.md:
 * a persistent timeline strip, primary narrative reading column, a
 * map/graph toggle (never both crammed on-screen at once), and a
 * contextual evidence panel. Facets stack on narrow viewports.
 *
 * The map/graph toggle follows the WAI-ARIA Tabs pattern with roving
 * tabindex and Left/Right arrow-key navigation (docs/design/accessibility.md
 * — keyboard accessibility is a Plan 5 requirement, not left to default
 * button behavior once ARIA tab roles are used).
 */
export function InvestigationLayout({
  header,
  timeline,
  narrative,
  map,
  graph,
  evidence,
}: {
  header: ReactNode
  timeline: ReactNode
  narrative: ReactNode
  map: ReactNode
  graph: ReactNode
  evidence: ReactNode
}) {
  const [secondaryView, setSecondaryView] = useState<SecondaryView>('map')
  const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({})

  function focusAndSelect(id: SecondaryView) {
    setSecondaryView(id)
    tabRefs.current[id]?.focus()
  }

  function handleTabKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    const currentIndex = TABS.findIndex((t) => t.id === secondaryView)
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
    <main className="mx-auto flex min-h-svh max-w-6xl flex-col gap-5 p-4 md:p-8">
      <header className="border-b border-neutral-200 pb-4 dark:border-neutral-800">
        {header}
      </header>

      <div className="rounded-lg border border-neutral-200 bg-white p-3 dark:border-neutral-800 dark:bg-neutral-900">
        {timeline}
      </div>

      <div className="flex flex-col gap-5 lg:flex-row lg:items-start">
        <div className="rounded-lg border border-neutral-200 bg-white p-4 lg:flex-1 lg:p-5 dark:border-neutral-800 dark:bg-neutral-900">
          {narrative}
        </div>

        <div className="flex flex-col gap-5 lg:w-96 lg:flex-none">
          <section
            aria-label="Map and relationship graph"
            className="overflow-hidden rounded-lg border border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-900"
          >
            <div
              role="tablist"
              aria-label="Map or relationship graph"
              className="flex border-b border-neutral-200 dark:border-neutral-800"
            >
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  ref={(el) => {
                    tabRefs.current[tab.id] = el
                  }}
                  id={`tab-${tab.id}`}
                  role="tab"
                  type="button"
                  aria-selected={secondaryView === tab.id}
                  aria-controls={`tabpanel-${tab.id}`}
                  tabIndex={secondaryView === tab.id ? 0 : -1}
                  className={`flex-1 px-3 py-2.5 text-sm font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-blue-600 ${
                    secondaryView === tab.id
                      ? 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300'
                      : 'text-neutral-500 hover:bg-neutral-50 dark:text-neutral-400 dark:hover:bg-neutral-800'
                  }`}
                  onClick={() => focusAndSelect(tab.id)}
                  onKeyDown={handleTabKeyDown}
                >
                  {tab.label}
                </button>
              ))}
            </div>
            <div
              id={`tabpanel-${secondaryView}`}
              role="tabpanel"
              aria-labelledby={`tab-${secondaryView}`}
              tabIndex={0}
              className="p-3"
            >
              {secondaryView === 'map' ? map : graph}
            </div>
          </section>

          <div className="rounded-lg border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
            {evidence}
          </div>
        </div>
      </div>
    </main>
  )
}
