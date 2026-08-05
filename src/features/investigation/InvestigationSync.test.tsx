import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { InvestigationPage } from './InvestigationPage'

/**
 * Plan 4 requirement: "Make selection in each facet update every other
 * facet through the central Focus contract" — tested end to end here rather
 * than trusted from the unit-level Focus tests alone.
 *
 * Phase D: this exercises Inspector mode specifically, since Inspector is
 * where the narrative/map/graph/evidence five-facet sync this test proves
 * still lives unchanged (docs/decisions/ADR-002-map-first-workspace.md) —
 * the map-first workspace built in D0.3 has its own, simpler sync (lens +
 * map/timeline + shallow panel tabs), not this five-facet mechanism.
 */
function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter
        initialEntries={[
          '/investigations/blank-cheque-golden/scenes/scene-2-blank-cheque',
        ]}
      >
        <Routes>
          <Route
            path="/investigations/:packageId/scenes/:sceneId"
            element={<InvestigationPage mode="inspector" />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

async function waitForLoaded() {
  await waitFor(() =>
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument(),
  )
}

function evidenceRegion() {
  return screen.getByRole('region', { name: /evidence/i })
}

function mapRegion() {
  return screen.getByRole('region', { name: /map and relationship graph/i })
}

describe('cross-facet synchronization', () => {
  it('selecting a timeline event highlights it, and updates the evidence panel', async () => {
    const user = userEvent.setup()
    renderPage()
    await waitForLoaded()

    // Whole-scene default focus shows all curated evidence up front.
    expect(
      within(evidenceRegion()).getAllByText(/could count on germany.?s full support/i)
        .length,
    ).toBeGreaterThan(0)

    const eventButton = screen.getByRole('button', {
      name: /vienna's ultimatum deliberations/i,
    })
    await user.click(eventButton)

    // Timeline: the selected event is marked current.
    expect(eventButton).toHaveAttribute('aria-current', 'true')

    // Narrative: the block about that same event is now the focused one.
    expect(
      screen.getByRole('button', {
        name: /tschirschky reported from vienna/i,
      }),
    ).toHaveAttribute('aria-pressed', 'true')

    // Evidence panel: scoped down to just this event's claim, per
    // Event.relatedRecordIds — the assurance-telegram claim from a
    // different event should no longer be shown.
    expect(
      within(evidenceRegion()).queryByText(/could count on germany.?s full support/i),
    ).not.toBeInTheDocument()
    expect(
      within(evidenceRegion()).getByText(/vienna.?s diplomatic posture/i),
    ).toBeInTheDocument()
  })

  it('selecting a place in the map scopes evidence to events at that place', async () => {
    const user = userEvent.setup()
    renderPage()
    await waitForLoaded()

    const viennaButton = within(mapRegion()).getByRole('button', {
      name: /^Vienna/,
    })
    await user.click(viennaButton)

    expect(viennaButton).toHaveAttribute('aria-current', 'true')
    // Vienna's only event is the 10 July report — its claim should surface.
    expect(
      within(evidenceRegion()).getByText(/vienna.?s diplomatic posture/i),
    ).toBeInTheDocument()
  })

  it('selecting a graph node uses first-class claim focus', async () => {
    const user = userEvent.setup()
    renderPage()
    await waitForLoaded()

    await user.click(screen.getByRole('tab', { name: /relationships/i }))
    await user.click(
      within(mapRegion()).getByRole('button', {
        name: /Szögyény reported that Wilhelm II stated/i,
      }),
    )

    expect(screen.getByRole('status')).toHaveTextContent(/showing claim/i)
    expect(
      within(evidenceRegion()).getAllByText(/could count on Germany’s full support/i)
        .length,
    ).toBeGreaterThan(0)
  })

  it('selecting a graph edge summary uses first-class relationship focus', async () => {
    const user = userEvent.setup()
    renderPage()
    await waitForLoaded()

    await user.click(screen.getByRole('tab', { name: /relationships/i }))
    await user.click(
      within(mapRegion()).getByRole('button', { name: /causal-influence/i }),
    )

    expect(screen.getByRole('status')).toHaveTextContent(
      /showing relationship: causal-influence/i,
    )
    expect(
      within(evidenceRegion()).getByText(/Clark-aligned reading/i),
    ).toBeInTheDocument()
  })

  it('source inspection exposes first-class source and passage focus', async () => {
    const user = userEvent.setup()
    renderPage()
    await waitForLoaded()

    await user.click(within(evidenceRegion()).getAllByRole('button', { name: /view source/i })[0])
    expect(screen.getByRole('status')).toHaveTextContent(/showing source/i)

    const sourceDialog = screen.getByRole('dialog')
    await user.click(
      within(sourceDialog).getByRole('button', {
        name: /Franz Joseph writes that the Sarajevo assassination/i,
      }),
    )

    expect(screen.getByRole('status')).toHaveTextContent(/showing passage/i)
  })
})
