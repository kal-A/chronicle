import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { expectNoA11yViolations } from '../../../test/axe'
import { AskEntryPage } from './AskEntryPage'

// GenerationProgress's real per-stage delay is tuned for the actual UX
// (~350ms/stage); tests use a negligible override so the flow completes
// almost instantly instead of fighting Testing Library's findBy polling
// against fake timers.
const TEST_STEP_DELAY_MS = 1

function renderAskEntryPage() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route path="/" element={<AskEntryPage generationStepDelayMs={TEST_STEP_DELAY_MS} />} />
        <Route
          path="/investigations/:packageId/scenes/:sceneId"
          element={<div data-testid="workspace-landed" />}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe('AskEntryPage', () => {
  it('has no detectable accessibility violations in its default ask state', async () => {
    const { container } = renderAskEntryPage()
    await expectNoA11yViolations(container)
  })

  it('matches a typed question to scope review, then generates into the matched workspace', async () => {
    renderAskEntryPage()

    fireEvent.change(screen.getByLabelText(/ask a historical question/i), {
      target: {
        value: 'How did the Concert of Europe respond to revolutionary intervention at Troppau?',
      },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Ask' }))

    expect(await screen.findByText(/proposed scope/i)).toBeInTheDocument()
    expect(screen.getByText(/Vienna, Troppau, Laibach, Naples, and Verona/i)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /generate this investigation/i }))
    expect(screen.getByRole('status', { name: /generation progress/i })).toBeInTheDocument()

    expect(await screen.findByTestId('workspace-landed')).toBeInTheDocument()
  })

  it('shows an honest no-match message for an unrelated question, without navigating', () => {
    renderAskEntryPage()

    fireEvent.change(screen.getByLabelText(/ask a historical question/i), {
      target: { value: 'What was the economic impact of the Meiji Restoration on silk exports?' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Ask' }))

    expect(screen.getByRole('alert')).toHaveTextContent(/nothing curated matches/i)
    expect(screen.queryByTestId('workspace-landed')).not.toBeInTheDocument()
  })

  it('lets a suggested starting point be clicked directly, matching itself', async () => {
    renderAskEntryPage()

    const startingPointButtons = screen.getAllByRole('button').filter(
      (button) => button.textContent && /german assurance|concert of europe/i.test(button.textContent),
    )
    expect(startingPointButtons.length).toBeGreaterThan(0)

    fireEvent.click(startingPointButtons[0])

    expect(await screen.findByText(/proposed scope/i)).toBeInTheDocument()
  })

  it('returns to the ask state from scope review via "Ask something else"', async () => {
    renderAskEntryPage()

    fireEvent.change(screen.getByLabelText(/ask a historical question/i), {
      target: { value: 'What did the German assurance to Austria-Hungary promise?' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
    expect(await screen.findByText(/proposed scope/i)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /ask something else/i }))
    expect(screen.queryByText(/proposed scope/i)).not.toBeInTheDocument()
    expect(screen.getByLabelText(/ask a historical question/i)).toBeInTheDocument()
  })
})
