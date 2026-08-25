import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { InvestigationPage } from './InvestigationPage'
import { expectNoA11yViolations } from '../../test/axe'

const GOLDEN_ROUTE =
  '/investigations/blank-cheque-golden/scenes/scene-2-blank-cheque'

function renderPage(mode: 'workspace' | 'inspector' = 'workspace', path = GOLDEN_ROUTE) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route
            path="/investigations/:packageId/scenes/:sceneId"
            element={<InvestigationPage mode={mode} />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('InvestigationPage (map-first workspace, the default)', () => {
  it('shows a loading state, then the workspace once data resolves', async () => {
    renderPage()
    expect(screen.getByRole('status')).toHaveTextContent(/loading/i)

    await waitFor(() =>
      expect(
        screen.getByRole('heading', {
          level: 1,
          name: /German Assurance and Vienna’s Posture/i,
        }),
      ).toBeInTheDocument(),
    )
    expect(screen.getByRole('link', { name: 'Chronicle' })).toBeInTheDocument()
    expect(document.title).toBe(
      'The German Assurance and Vienna’s Posture, 4–10 July 1914 · Chronicle',
    )
  })

  it('renders a lens selector and a link to Inspector', async () => {
    renderPage()
    await waitFor(() =>
      expect(screen.getByLabelText(/lens/i)).toBeInTheDocument(),
    )
    expect(screen.getByRole('link', { name: /inspector/i })).toHaveAttribute(
      'href',
      '/investigations/blank-cheque-golden/scenes/scene-2-blank-cheque/inspector',
    )
  })

  it('uses the time control to reveal only events available by the selected moment', async () => {
    renderPage()
    const slider = await screen.findByRole('slider', { name: /historical event position/i })

    expect(slider).toHaveValue('2')
    expect(screen.getByText(/3 events visible/i)).toBeInTheDocument()

    fireEvent.change(slider, { target: { value: '0' } })

    expect(slider).toHaveValue('0')
    expect(slider).toHaveAttribute(
      'aria-valuetext',
      expect.stringMatching(/Szögyény meets Wilhelm II/i),
    )
    expect(screen.getByText(/1 event visible/i)).toBeInTheDocument()
    expect(
      screen.getAllByText(/Szögyény meets Wilhelm II in Berlin/i).length,
    ).toBeGreaterThan(0)
  })

  it('has no detectable accessibility violations once loaded', async () => {
    const { container } = renderPage()
    await waitFor(() =>
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument(),
    )
    await expectNoA11yViolations(container)
  })

  it('shows a package-not-found state for an unknown investigation id', async () => {
    renderPage('workspace', '/investigations/unknown-package/scenes/scene-any')

    expect(await screen.findByRole('alert')).toHaveTextContent(
      /investigation could not be found/i,
    )
  })
})

describe('InvestigationPage (Inspector mode — the preserved article-first renderer)', () => {
  it('renders the scene heading and prototype-content notice', async () => {
    renderPage('inspector')

    await waitFor(() =>
      expect(
        screen.getByRole('heading', { level: 2, name: /blank cheque/i }),
      ).toBeInTheDocument(),
    )
    expect(screen.getByText(/prototype content/i)).toBeInTheDocument()
    expect(document.title).toBe(
      'The German Assurance and Vienna’s Posture, 4–10 July 1914 · Inspector · Chronicle',
    )
  })

  it('has no detectable accessibility violations once loaded', async () => {
    const { container } = renderPage('inspector')
    await waitFor(() =>
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument(),
    )
    await expectNoA11yViolations(container)
  })
})
