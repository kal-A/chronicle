import { useCallback, useEffect, useRef, useState } from 'react'
import {
  buildInvestigation,
  fetchAgentRun,
  isTerminalAgentStatus,
  resolveInvestigationScope,
  type AgentRunRecord,
  type CorpusBuildAccepted,
} from '../assistant/agentApi'

/**
 * The live Ask-generation flow behind AskEntryPage's no-match path. It calls the
 * real backend — propose a scope, then acquire sources + build a corpus + run
 * the four-agent investigation — and surfaces the real, honest outcome (a cited
 * answer or a principled abstention) inline. A generated corpus is passage-only,
 * so it cannot drive the map-first workspace (that is reserved for curated
 * investigations); the outcome is presented as text here. Acquisition + local
 * inference are minutes-scale on CPU, so the build request and the run poll are
 * deliberately patient.
 */

export interface EditableScope {
  topic: string
  /** Comma-separated in the form; split into a list on submit. */
  geographicScope: string
  dateEarliest: string
  dateLatest: string
}

export type AskGenerationState =
  | { phase: 'idle' }
  | { phase: 'resolving' }
  | { phase: 'scope'; scope: EditableScope; autoResolved: boolean; note?: string }
  | { phase: 'building' }
  | { phase: 'running'; run: AgentRunRecord | null; build: CorpusBuildAccepted }
  | { phase: 'result'; run: AgentRunRecord; build: CorpusBuildAccepted }
  | { phase: 'error'; message: string }

const POLL_INTERVAL_MS = 1_500

function messageFor(error: unknown): string {
  if (error instanceof Error && error.message) return error.message
  return 'Chronicle could not reach the local research service.'
}

function splitScope(value: string): string[] {
  return value
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean)
}

export interface AskGenerationController {
  state: AskGenerationState
  question: string
  /** Ask the backend to propose a scope for review. */
  proposeScope: (question: string) => Promise<void>
  /** Build + investigate from the reviewed scope, then stream the result. */
  generate: (scope: EditableScope) => Promise<void>
  reset: () => void
}

export function useAskGeneration(): AskGenerationController {
  const [state, setState] = useState<AskGenerationState>({ phase: 'idle' })
  const [question, setQuestion] = useState('')
  const pollRef = useRef<number | undefined>(undefined)

  const stopPolling = useCallback(() => {
    if (pollRef.current !== undefined) {
      window.clearInterval(pollRef.current)
      pollRef.current = undefined
    }
  }, [])

  useEffect(() => stopPolling, [stopPolling])

  const proposeScope = useCallback(async (submitted: string) => {
    const trimmed = submitted.trim()
    setQuestion(trimmed)
    setState({ phase: 'resolving' })
    try {
      const proposal = await resolveInvestigationScope(trimmed)
      setState({
        phase: 'scope',
        autoResolved: proposal.resolved,
        note: proposal.message ?? undefined,
        scope: {
          topic: proposal.topic ?? '',
          geographicScope: (proposal.geographicScope ?? []).join(', '),
          dateEarliest: proposal.dateEarliest ?? '',
          dateLatest: proposal.dateLatest ?? '',
        },
      })
    } catch (error) {
      setState({ phase: 'error', message: messageFor(error) })
    }
  }, [])

  const generate = useCallback(
    async (scope: EditableScope) => {
      stopPolling()
      setState({ phase: 'building' })
      let build: CorpusBuildAccepted
      try {
        build = await buildInvestigation({
          topic: scope.topic.trim(),
          question,
          geographicScope: splitScope(scope.geographicScope),
          dateEarliest: scope.dateEarliest,
          dateLatest: scope.dateLatest,
          terms: [],
        })
      } catch (error) {
        setState({ phase: 'error', message: messageFor(error) })
        return
      }
      setState({ phase: 'running', run: null, build })

      const poll = async () => {
        let run: AgentRunRecord
        try {
          run = await fetchAgentRun(build.run.runId)
        } catch (error) {
          stopPolling()
          setState({ phase: 'error', message: messageFor(error) })
          return
        }
        if (isTerminalAgentStatus(run.status)) {
          stopPolling()
          setState({ phase: 'result', run, build })
        } else {
          setState((current) =>
            current.phase === 'running' ? { ...current, run } : current,
          )
        }
      }

      void poll()
      pollRef.current = window.setInterval(() => void poll(), POLL_INTERVAL_MS)
    },
    [question, stopPolling],
  )

  const reset = useCallback(() => {
    stopPolling()
    setQuestion('')
    setState({ phase: 'idle' })
  }, [stopPolling])

  return { state, question, proposeScope, generate, reset }
}
