import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { InvestigationAssistantController } from '../../assistant/useInvestigationAssistant'
import { AskTab } from './AskTab'

function controller(
  overrides: Partial<InvestigationAssistantController> = {},
): InvestigationAssistantController {
  return {
    turns: [],
    active: false,
    ask: vi.fn(async () => {}),
    retry: vi.fn(async () => {}),
    ...overrides,
  }
}

describe('AskTab', () => {
  it('submits a real investigation question and clears the composer', async () => {
    const user = userEvent.setup()
    const assistant = controller()
    render(<AskTab assistant={assistant} />)

    const composer = screen.getByLabelText(/continue the investigation/i)
    await user.type(composer, 'What did the report say?')
    await user.click(screen.getByRole('button', { name: 'Investigate' }))

    expect(assistant.ask).toHaveBeenCalledWith('What did the report say?')
    expect(composer).toHaveValue('')
  })

  it('renders streamed progress through Chronicle’s five sequential roles', () => {
    render(
      <AskTab
        assistant={controller({
          active: true,
          turns: [
            {
              id: 'turn-1',
              question: 'What did the report say?',
              events: [
                {
                  sequence: 1,
                  runId: 'run-1',
                  type: 'stage_started',
                  stage: 'analyst',
                  round: 0,
                  message: 'Analyst started.',
                  occurredAt: '2026-08-20T12:00:00Z',
                },
              ],
            },
          ],
        })}
      />,
    )

    expect(screen.getByRole('status')).toHaveTextContent('Analyst started')
    expect(screen.getByRole('list', { name: /investigation progress/i })).toHaveTextContent(
      'ScopeRetrieveAnalyzeVerifyCompose',
    )
  })

  it('shows the cited answer, limitations, tool activity, and workspace actions', async () => {
    const user = userEvent.setup()
    const onAction = vi.fn()
    render(
      <AskTab
        onAction={onAction}
        assistant={controller({
          turns: [
            {
              id: 'turn-1',
              question: 'What did the report say?',
              events: [],
              runId: 'run-1',
              run: {
                runId: 'run-1',
                status: 'answer_ready',
                stages: [],
                finalAnswer: {
                  status: 'answered',
                  directAnswer: 'The report records an assurance of full German support.',
                  keyPoints: [
                    { statementId: 's1', text: 'The assurance was reported directly.' },
                  ],
                  disagreements: [],
                  limitations: ['The received time is not established in this edition.'],
                  citations: [
                    {
                      statementId: 's1',
                      citation: {
                        toolCallId: 'call-1',
                        evidenceLinkId: 'link-1',
                        passageId: 'passage-1',
                        sourceId: 'source-1',
                        targetType: 'claim',
                        targetId: 'claim-1',
                        role: 'supporting',
                      },
                    },
                  ],
                  suggestedQuestions: [],
                  actions: [{ type: 'FOCUS_EVENT', eventId: 'event-1' }],
                },
                abstentionReason: null,
                errorMessage: null,
                warnings: [],
                toolCalls: [{ toolName: 'get_claim_evidence', status: 'succeeded', resultCount: 1 }],
              },
            },
          ],
        })}
      />,
    )

    expect(screen.getByText(/assurance of full German support/i)).toBeInTheDocument()
    expect(screen.getByText(/1 citation/i)).toBeInTheDocument()
    expect(screen.getByText(/get claim evidence/i)).toBeInTheDocument()
    await user.click(screen.getByText(/limits and provenance/i))
    expect(screen.getByText(/received time is not established/i)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /show event on map/i }))
    expect(onAction).toHaveBeenCalledWith({ type: 'FOCUS_EVENT', eventId: 'event-1' })
  })

  it('offers bounded recovery when a run fails', async () => {
    const user = userEvent.setup()
    const assistant = controller({
      turns: [
        {
          id: 'turn-failed',
          question: 'Investigate this claim.',
          runId: 'run-failed',
          events: [],
          error: 'The local model timed out.',
        },
      ],
    })
    render(<AskTab assistant={assistant} />)

    expect(screen.getByRole('alert')).toHaveTextContent(/local qwen model took too long/i)
    await user.click(screen.getByRole('button', { name: /resume from the last safe stage/i }))
    expect(assistant.retry).toHaveBeenCalledWith('turn-failed')
  })

  it('presents abstention as a safety outcome rather than a cited finding', () => {
    render(
      <AskTab
        assistant={controller({
          turns: [
            {
              id: 'turn-abstained',
              question: 'What can the corpus establish?',
              events: [],
              run: {
                runId: 'run-abstained',
                status: 'abstained',
                stages: [],
                finalAnswer: {
                  status: 'abstained',
                  directAnswer: 'abstained',
                  keyPoints: [],
                  disagreements: [],
                  limitations: [],
                  citations: [],
                  suggestedQuestions: [],
                  actions: [],
                },
                abstentionReason: 'The retrieved record was too limited for a reliable answer.',
                errorMessage: null,
                warnings: [],
                toolCalls: [],
              },
            },
          ],
        })}
      />,
    )

    expect(screen.getByText(/stopped short of an answer/i)).toBeInTheDocument()
    expect(screen.getByText(/too limited for a reliable answer/i)).toBeInTheDocument()
    expect(screen.queryByText(/cited finding/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/0 citations/i)).not.toBeInTheDocument()
  })
})
