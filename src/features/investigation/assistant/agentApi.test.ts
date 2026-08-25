import { afterEach, describe, expect, it, vi } from 'vitest'
import { AgentApiError, fetchAgentRun, submitInvestigationQuestion } from './agentApi'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('agentApi', () => {
  it('submits the question with the immutable workspace context snapshot', async () => {
    const fetchMock = vi.fn<typeof fetch>(async () => new Response(JSON.stringify({
      runId: 'run-1',
      status: 'created',
      statusUrl: '/api/agent-runs/run-1',
      eventsUrl: '/api/agent-runs/run-1/events',
    }), { status: 202, headers: { 'Content-Type': 'application/json' } }))
    vi.stubGlobal('fetch', fetchMock)

    await submitInvestigationQuestion(
      'blank-cheque-golden',
      'What did the report say?',
      {
        sceneId: 'scene-2',
        selectedLensId: 'chronology',
        selectedRecords: [{ recordType: 'claim', recordId: 'claim-1' }],
      },
      'Earlier context',
    )

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/investigations/blank-cheque-golden/questions')
    expect(JSON.parse(String(init?.body))).toEqual({
      question: 'What did the report say?',
      conversationSummary: 'Earlier context',
      workspaceContext: {
        sceneId: 'scene-2',
        selectedLensId: 'chronology',
        selectedRecords: [{ recordType: 'claim', recordId: 'claim-1' }],
      },
    })
  })

  it('returns a useful recovery message when the local backend is unavailable', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw new TypeError('connection refused') }))

    await expect(fetchAgentRun('run-1')).rejects.toEqual(
      expect.objectContaining<Partial<AgentApiError>>({
        message: expect.stringMatching(/start the backend/i),
      }),
    )
  })
})
