import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { expectNoA11yViolations } from '../../../test/axe'
import { AskEntryPage } from './AskEntryPage'

function jsonResponse(body: unknown) {
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve(body),
  } as Response
}

/** Route the live-generation fetches (resolve-scope, build, run poll) to canned
 * responses so the flow can be exercised without a backend. */
function mockGenerationBackend(run: unknown) {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = typeof input === 'string' ? input : input.toString()
    if (url.endsWith('/resolve-scope')) {
      return Promise.resolve(
        jsonResponse({
          resolved: true,
          topic: 'The Meiji Restoration',
          interpretedQuestion: 'What was the economic impact of the Meiji Restoration?',
          geographicScope: ['Japan'],
          dateEarliest: '1868-01-01',
          dateLatest: '1889-12-31',
          terms: ['Meiji', 'silk'],
        }),
      )
    }
    if (url.endsWith('/investigations/build')) {
      return Promise.resolve(
        jsonResponse({
          corpusId: 'acq-meiji',
          alreadyBuilt: false,
          discovered: 3,
          acquired: 3,
          passages: 12,
          run: {
            runId: 'run-gen-1',
            status: 'running',
            statusUrl: '/api/agent-runs/run-gen-1',
            eventsUrl: '/api/agent-runs/run-gen-1/events',
          },
          corpusUrl: '/api/corpora/acq-meiji',
        }),
      )
    }
    if (url.includes('/agent-runs/')) {
      return Promise.resolve(jsonResponse(run))
    }
    // Benign fallback (e.g. the hero atlas coastline geojson) so unrelated
    // mounts don't error under the stubbed fetch.
    return Promise.resolve(jsonResponse({ type: 'FeatureCollection', features: [] }))
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

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
  afterEach(() => {
    vi.unstubAllGlobals()
  })

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

  it('researches an unmatched question live and shows the real cited answer inline', async () => {
    mockGenerationBackend({
      runId: 'run-gen-1',
      status: 'answer_ready',
      stages: [{ stageName: 'guide', status: 'succeeded', errors: [] }],
      finalAnswer: {
        status: 'partial',
        directAnswer: 'According to the sources, the Meiji Restoration reshaped silk exports.',
        keyPoints: [{ statementId: 's1', text: 'Silk became a leading export.' }],
        disagreements: [],
        limitations: ['Retrieval was truncated; reflects only the returned records.'],
        citations: [{ statementId: 's1', citation: { toolCallId: 'c1', passageId: 'p1' } }],
        suggestedQuestions: [],
        actions: [],
      },
      abstentionReason: null,
      errorMessage: null,
      warnings: [],
      toolCalls: [],
    })
    renderAskEntryPage()

    fireEvent.change(screen.getByLabelText(/ask a historical question/i), {
      target: { value: 'What was the economic impact of the Meiji Restoration on silk exports?' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Ask' }))

    // The backend proposes a scope for review (model assists, human confirms).
    expect(await screen.findByText(/review the proposed scope/i)).toBeInTheDocument()
    expect(screen.getByDisplayValue('The Meiji Restoration')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Japan')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /acquire sources & investigate/i }))

    // The real cited answer is presented inline (never navigates to the map
    // workspace, since a generated corpus is passage-only).
    expect(await screen.findByText(/what the sources support/i)).toBeInTheDocument()
    expect(
      screen.getByText(/the meiji restoration reshaped silk exports/i),
    ).toBeInTheDocument()
    expect(screen.queryByTestId('workspace-landed')).not.toBeInTheDocument()
  })

  it('abstains honestly inline when the live run cannot ground an answer', async () => {
    mockGenerationBackend({
      runId: 'run-gen-1',
      status: 'abstained',
      stages: [{ stageName: 'analyst', status: 'rejected', errors: [] }],
      finalAnswer: null,
      abstentionReason: 'The acquired evidence could not ground an analysis.',
      errorMessage: null,
      warnings: [],
      toolCalls: [],
    })
    renderAskEntryPage()

    fireEvent.change(screen.getByLabelText(/ask a historical question/i), {
      target: { value: 'What was the economic impact of the Meiji Restoration on silk exports?' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Ask' }))
    fireEvent.click(await screen.findByRole('button', { name: /acquire sources & investigate/i }))

    expect(await screen.findByText(/chronicle abstained/i)).toBeInTheDocument()
    expect(screen.getByText(/could not ground an analysis/i)).toBeInTheDocument()
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
