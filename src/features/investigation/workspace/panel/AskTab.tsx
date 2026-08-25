import { useId, useState, type FormEvent } from 'react'
import type { AssistantAction } from '../../assistant/agentApi'
import type {
  InvestigationAssistantController,
  InvestigationTurn,
} from '../../assistant/useInvestigationAssistant'

const STAGES = ['planner', 'retrieval', 'analyst', 'critic', 'guide'] as const

const STAGE_LABELS = {
  planner: 'Scope',
  retrieval: 'Retrieve',
  analyst: 'Analyze',
  critic: 'Verify',
  guide: 'Compose',
} as const

export function AskTab({
  assistant,
  onAction,
}: {
  assistant: InvestigationAssistantController
  onAction?: (action: AssistantAction) => void
}) {
  const [question, setQuestion] = useState('')
  const questionId = useId()

  async function submit(event: FormEvent) {
    event.preventDefault()
    const nextQuestion = question.trim()
    if (!nextQuestion || assistant.active) return
    setQuestion('')
    await assistant.ask(nextQuestion)
  }

  return (
    <div className="chronicle-assistant">
      <div className="chronicle-assistant__intro">
        <p className="chronicle-panel-lead">Ask from this view</p>
        <p className="chronicle-panel-copy">
          Chronicle snapshots the visible scene, selected map record, lens, and time context before
          it searches the reviewed corpus.
        </p>
      </div>

      <div className="chronicle-assistant__history" aria-live="polite">
        {assistant.turns.length === 0 ? (
          <div className="chronicle-assistant__empty">
            <span aria-hidden="true" />
            <p>Your investigation thread will appear here with its evidence trail.</p>
          </div>
        ) : (
          assistant.turns.map((turn) => (
            <AssistantTurn key={turn.id} turn={turn} retry={assistant.retry} onAction={onAction} />
          ))
        )}
      </div>

      <form className="chronicle-assistant__composer" onSubmit={submit}>
        <label htmlFor={questionId}>Continue the investigation</label>
        <textarea
          id={questionId}
          value={question}
          maxLength={1_000}
          rows={3}
          placeholder="Ask about the selected event, source, claim, or relationship…"
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              event.currentTarget.form?.requestSubmit()
            }
          }}
        />
        <div>
          <span>{assistant.active ? 'Qwen is investigating locally' : 'Enter to ask · Shift+Enter for a new line'}</span>
          <button type="submit" disabled={assistant.active || !question.trim()}>
            {assistant.active ? 'Working…' : 'Investigate'}
          </button>
        </div>
      </form>
    </div>
  )
}

function AssistantTurn({
  turn,
  retry,
  onAction,
}: {
  turn: InvestigationTurn
  retry: InvestigationAssistantController['retry']
  onAction?: (action: AssistantAction) => void
}) {
  const run = turn.run
  const answer = run?.finalAnswer
  const latestEvent = turn.events.at(-1)
  const failed = Boolean(turn.error || run?.status === 'failed' || run?.status === 'cancelled')

  return (
    <article className="chronicle-assistant-turn">
      <div className="chronicle-assistant-turn__question">
        <span>You asked</span>
        <p>{turn.question}</p>
      </div>

      {!answer && !failed && run?.status !== 'abstained' ? (
        <div className="chronicle-agent-progress" role="status">
          <p>{latestEvent?.message ?? 'Preparing the investigation context…'}</p>
          <ol aria-label="Investigation progress">
            {STAGES.map((stage) => {
              const completed = turn.events.some(
                (event) => event.type === 'stage_completed' && event.stage === stage,
              )
              const current = turn.events.some(
                (event) => event.type === 'stage_started' && event.stage === stage,
              ) && !completed
              return (
                <li key={stage} className={completed ? 'is-complete' : current ? 'is-current' : ''}>
                  <span aria-hidden="true" />
                  {STAGE_LABELS[stage]}
                </li>
              )
            })}
          </ol>
        </div>
      ) : null}

      {answer && answer.status !== 'abstained' ? (
        <div className="chronicle-agent-answer">
          <div className="chronicle-agent-answer__status">
            <span>{answer.status === 'partial' ? 'Bounded finding' : 'Cited finding'}</span>
            <strong>{answer.citations.length} citation{answer.citations.length === 1 ? '' : 's'}</strong>
          </div>
          <p className="chronicle-agent-answer__direct">{answer.directAnswer}</p>

          {answer.keyPoints.length > 1 ? (
            <ul className="chronicle-agent-answer__points">
              {answer.keyPoints.map((point) => <li key={point.statementId}>{point.text}</li>)}
            </ul>
          ) : null}

          {answer.citations.length ? (
            <details className="chronicle-agent-disclosure">
              <summary>Evidence trail</summary>
              <ol>
                {answer.citations.map(({ statementId, citation }) => (
                  <li key={`${statementId}-${citation.evidenceLinkId ?? citation.targetId}`}>
                    <strong>{citation.role ?? 'retrieved'}</strong>
                    <span>{citation.sourceId ?? citation.targetId}</span>
                    {citation.passageId ? <small>Passage {citation.passageId}</small> : null}
                  </li>
                ))}
              </ol>
            </details>
          ) : null}

          {answer.limitations.length || run?.warnings.length ? (
            <details className="chronicle-agent-disclosure chronicle-agent-disclosure--limits">
              <summary>Limits and provenance</summary>
              <ul>
                {[...answer.limitations, ...(run?.warnings ?? [])].map((limitation) => (
                  <li key={limitation}>{limitation}</li>
                ))}
              </ul>
            </details>
          ) : null}

          {run?.toolCalls.length ? (
            <p className="chronicle-agent-tools">
              <span>Research activity</span>
              {run.toolCalls.map((call) => call.toolName.replaceAll('_', ' ')).join(' · ')}
            </p>
          ) : null}

          {answer.actions.length && onAction ? (
            <div className="chronicle-agent-actions" aria-label="Map actions">
              {answer.actions.map((action, index) => (
                <button key={`${action.type}-${index}`} type="button" onClick={() => onAction(action)}>
                  {actionLabel(action)}
                </button>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}

      {run?.status === 'abstained' ? (
        <div className="chronicle-agent-abstention">
          <strong>Chronicle stopped short of an answer.</strong>
          <p>{run.abstentionReason ?? 'The reviewed corpus did not support a reliable response.'}</p>
        </div>
      ) : null}

      {failed ? (
        <div className="chronicle-agent-error" role="alert">
          <strong>The investigation did not finish.</strong>
          <p>{friendlyError(turn.error ?? run?.errorMessage)}</p>
          <button type="button" onClick={() => void retry(turn.id)}>Resume from the last safe stage</button>
        </div>
      ) : null}
    </article>
  )
}

function friendlyError(message?: string | null) {
  if (!message) return 'The local model run stopped unexpectedly. Resume from its last safe stage.'
  if (/timed out|timeout/i.test(message)) {
    return 'The local Qwen model took too long to finish this stage. Resume to retry from the last safe stage.'
  }
  if (/exhausted|schema|validation error|generating investigationplan/i.test(message)) {
    return 'Qwen could not assemble a valid bounded response on this attempt. Resume to retry from the last safe stage.'
  }
  if (/prompt is .*maximum|budget/i.test(message)) {
    return 'This question and its current context are too large for the local model. Narrow the map selection or ask a more focused question.'
  }
  return message
}

function actionLabel(action: AssistantAction) {
  switch (action.type) {
    case 'FOCUS_EVENT': return 'Show event on map'
    case 'FOCUS_LOCATION': return 'Focus location'
    case 'ACTIVATE_LENS': return 'Open suggested lens'
    case 'OPEN_SOURCE': return 'Open cited source'
    case 'OPEN_EVIDENCE': return 'Open evidence record'
    case 'RESET_VIEW': return 'Reset map view'
    default: return 'Apply to workspace'
  }
}
