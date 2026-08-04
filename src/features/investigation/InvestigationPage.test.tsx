import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { InvestigationPage } from './InvestigationPage'
import { expectNoA11yViolations } from '../../test/axe'

const GOLDEN_ROUTE =
  '/investigations/blank-cheque-golden/scenes/scene-2-blank-cheque'

function renderPage(path = GOLDEN_ROUTE) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route
            path="/investigations/:packageId/scenes/:sceneId"
            element={<InvestigationPage />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('InvestigationPage', () => {
  it('shows a loading state, then the scene heading once data resolves', async () => {
    renderPage()
    expect(screen.getByRole('status')).toHaveTextContent(/loading/i)

    await waitFor(() =>
      expect(
        screen.getByRole('heading', { level: 1, name: 'Chronicle' }),
      ).toBeInTheDocument(),
    )
    expect(
      screen.getByRole('heading', { level: 2, name: /blank cheque/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/German Assurance and Vienna’s Posture/i),
    ).toBeInTheDocument()
    expect(document.title).toBe(
      'The German Assurance and Vienna’s Posture, 4–10 July 1914 · Chronicle',
    )
  })

  it('renders the prototype-content notice, honoring the honest-labeling requirement', async () => {
    renderPage()
    await waitFor(() =>
      expect(screen.getByText(/prototype content/i)).toBeInTheDocument(),
    )
  })

  it('has no detectable accessibility violations once loaded', async () => {
    const { container } = renderPage()
    await waitFor(() =>
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument(),
    )
    await expectNoA11yViolations(container)
  })

  it('shows a package-not-found state for an unknown investigation id', async () => {
    renderPage('/investigations/unknown-package/scenes/scene-any')

    expect(await screen.findByRole('alert')).toHaveTextContent(
      /investigation could not be found/i,
    )
  })
})
