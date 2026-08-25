import { useCallback, useEffect, useRef, useState } from 'react'
import {
  fetchAgentRun,
  isTerminalAgentStatus,
  resolveAgentApiUrl,
  resumeAgentRun,
  submitInvestigationQuestion,
  type AgentRunAccepted,
  type AgentRunEvent,
  type AgentRunRecord,
  type WorkspaceContextInput,
} from './agentApi'

export interface InvestigationTurn {
  id: string
  question: string
  runId?: string
  run?: AgentRunRecord
  events: AgentRunEvent[]
  error?: string
}

export interface InvestigationAssistantController {
  turns: InvestigationTurn[]
  active: boolean
  ask: (question: string) => Promise<void>
  retry: (turnId: string) => Promise<void>
}

const TERMINAL_EVENTS = ['run_completed', 'run_abstained', 'run_failed', 'run_cancelled'] as const
const ALL_EVENTS = [
  'run_started',
  'stage_started',
  'stage_completed',
  ...TERMINAL_EVENTS,
] as const

export function useInvestigationAssistant({
  corpusId,
  workspaceContext,
  initialQuestion,
}: {
  corpusId: string
  workspaceContext: WorkspaceContextInput
  initialQuestion?: string
}): InvestigationAssistantController {
  const [turns, setTurns] = useState<InvestigationTurn[]>([])
  const turnsRef = useRef(turns)
  const contextRef = useRef(workspaceContext)
  const watchersRef = useRef(new Map<string, () => void>())
  const initialQuestionRef = useRef(initialQuestion?.trim())

  useEffect(() => {
    turnsRef.current = turns
  }, [turns])

  useEffect(() => {
    contextRef.current = workspaceContext
  }, [workspaceContext])

  const updateTurn = useCallback((turnId: string, update: Partial<InvestigationTurn>) => {
    setTurns((current) =>
      current.map((turn) => (turn.id === turnId ? { ...turn, ...update } : turn)),
    )
  }, [])

  const watchRun = useCallback(
    (turnId: string, accepted: AgentRunAccepted) => {
      watchersRef.current.get(turnId)?.()
      let closed = false
      let source: EventSource | undefined

      const finish = () => {
        if (closed) return
        closed = true
        source?.close()
        window.clearInterval(pollId)
        watchersRef.current.delete(turnId)
      }

      const sync = async () => {
        try {
          const run = await fetchAgentRun(accepted.runId)
          updateTurn(turnId, { run, error: undefined })
          if (isTerminalAgentStatus(run.status)) finish()
        } catch (error) {
          updateTurn(turnId, {
            error: error instanceof Error ? error.message : 'The run could not be refreshed.',
          })
        }
      }

      const pollId = window.setInterval(() => void sync(), 1_500)
      void sync()

      if (typeof EventSource !== 'undefined') {
        source = new EventSource(resolveAgentApiUrl(accepted.eventsUrl))
        const receive = (raw: MessageEvent<string>) => {
          const event = JSON.parse(raw.data) as AgentRunEvent
          setTurns((current) =>
            current.map((turn) =>
              turn.id === turnId && !turn.events.some((item) => item.sequence === event.sequence)
                ? { ...turn, events: [...turn.events, event] }
                : turn,
            ),
          )
          if (TERMINAL_EVENTS.includes(event.type as (typeof TERMINAL_EVENTS)[number])) {
            void sync()
          }
        }
        ALL_EVENTS.forEach((type) => source?.addEventListener(type, receive as EventListener))
        source.onerror = () => source?.close()
      }

      watchersRef.current.set(turnId, finish)
    },
    [updateTurn],
  )

  const ask = useCallback(
    async (rawQuestion: string) => {
      const question = rawQuestion.trim()
      if (!question || turnsRef.current.some((turn) => turn.run && !isTerminalAgentStatus(turn.run.status))) {
        return
      }
      const turnId = `turn-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
      setTurns((current) => [...current, { id: turnId, question, events: [] }])
      try {
        const summary = conversationSummary(turnsRef.current)
        const accepted = await submitInvestigationQuestion(
          corpusId,
          question,
          contextRef.current,
          summary,
        )
        updateTurn(turnId, { runId: accepted.runId })
        watchRun(turnId, accepted)
      } catch (error) {
        updateTurn(turnId, {
          error: error instanceof Error ? error.message : 'Chronicle could not start this investigation.',
        })
      }
    },
    [corpusId, updateTurn, watchRun],
  )

  const retry = useCallback(
    async (turnId: string) => {
      const turn = turnsRef.current.find((candidate) => candidate.id === turnId)
      if (!turn?.runId) {
        if (turn) await ask(turn.question)
        return
      }
      updateTurn(turnId, { error: undefined, events: [] })
      try {
        const accepted = await resumeAgentRun(turn.runId)
        watchRun(turnId, accepted)
      } catch (error) {
        updateTurn(turnId, {
          error: error instanceof Error ? error.message : 'Chronicle could not resume this run.',
        })
      }
    },
    [ask, updateTurn, watchRun],
  )

  useEffect(() => {
    const question = initialQuestionRef.current
    if (question) {
      initialQuestionRef.current = undefined
      void ask(question)
    }
  }, [ask])

  useEffect(
    () => () => {
      watchersRef.current.forEach((close) => close())
      watchersRef.current.clear()
    },
    [],
  )

  return {
    turns,
    active: turns.some(
      (turn) => !turn.error && (!turn.run || !isTerminalAgentStatus(turn.run.status)),
    ),
    ask,
    retry,
  }
}

function conversationSummary(turns: InvestigationTurn[]) {
  const summary = turns
    .filter((turn) => turn.run?.finalAnswer)
    .slice(-3)
    .map((turn) => `User: ${turn.question}\nChronicle: ${turn.run?.finalAnswer?.directAnswer}`)
    .join('\n\n')
  return summary.slice(0, 2_000) || undefined
}
