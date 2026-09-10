export type AgentStageName = 'planner' | 'retrieval' | 'analyst' | 'critic' | 'guide'

export type AgentRunStatus =
  | 'created'
  | 'running'
  | 'analysis_ready'
  | 'answer_ready'
  | 'partial'
  | 'abstained'
  | 'cancelled'
  | 'interrupted'
  | 'failed'

export interface SelectedRecordInput {
  recordType:
    | 'claim'
    | 'relationship'
    | 'event'
    | 'entity'
    | 'knowledge_state'
    | 'source'
    | 'document'
    | 'passage'
    | 'place'
    | 'map_scene'
  recordId: string
}

export interface WorkspaceContextInput {
  sceneId?: string
  selectedLensId?: string
  selectedDateRange?: { earliest?: string; latest?: string }
  selectedRecords: SelectedRecordInput[]
}

export interface AgentRunEvent {
  sequence: number
  runId: string
  type:
    | 'run_started'
    | 'stage_started'
    | 'stage_completed'
    | 'run_completed'
    | 'run_abstained'
    | 'run_failed'
    | 'run_cancelled'
  stage?: AgentStageName
  round: number
  message: string
  occurredAt: string
}

export interface AnswerCitation {
  statementId: string
  citation: {
    toolCallId: string
    evidenceLinkId?: string | null
    passageId?: string | null
    sourceId?: string | null
    targetType?: string | null
    targetId?: string | null
    role?: 'supporting' | 'counterevidence' | 'context' | null
  }
}

export interface AssistantAction {
  type: string
  [key: string]: unknown
}

export interface AgentAnswer {
  status: 'answered' | 'partial' | 'abstained'
  directAnswer: string
  keyPoints: Array<{ statementId: string; text: string }>
  disagreements: Array<{ statementId: string; text: string }>
  limitations: string[]
  citations: AnswerCitation[]
  suggestedQuestions: string[]
  actions: AssistantAction[]
}

export interface AgentRunRecord {
  runId: string
  status: AgentRunStatus
  stages: Array<{
    stageName: AgentStageName
    status: string
    errors: string[]
  }>
  finalAnswer: AgentAnswer | null
  abstentionReason: string | null
  errorMessage: string | null
  warnings: string[]
  toolCalls: Array<{
    toolName: string
    status: string
    resultCount: number | null
  }>
}

export interface AgentRunAccepted {
  runId: string
  status: AgentRunStatus
  statusUrl: string
  eventsUrl: string
}

export class AgentApiError extends Error {
  readonly status?: number

  constructor(
    message: string,
    status?: number,
  ) {
    super(message)
    this.name = 'AgentApiError'
    this.status = status
  }
}

const apiBase = (import.meta.env.VITE_CHRONICLE_API_BASE ?? '').replace(/\/$/, '')

export function resolveAgentApiUrl(path: string) {
  if (/^https?:\/\//.test(path)) return path
  return `${apiBase}${path.startsWith('/') ? path : `/${path}`}`
}

export async function submitInvestigationQuestion(
  corpusId: string,
  question: string,
  workspaceContext: WorkspaceContextInput,
  conversationSummary?: string,
): Promise<AgentRunAccepted> {
  return requestJson<AgentRunAccepted>(
    `/api/investigations/${encodeURIComponent(corpusId)}/questions`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        workspaceContext,
        conversationSummary: conversationSummary || null,
      }),
    },
  )
}

export interface ProposedScopeResponse {
  resolved: boolean
  topic?: string | null
  interpretedQuestion?: string | null
  geographicScope?: string[] | null
  dateEarliest?: string | null
  dateLatest?: string | null
  terms?: string[] | null
  message?: string | null
}

export interface TopicBuildSubmission {
  topic: string
  question: string
  geographicScope: string[]
  dateEarliest: string
  dateLatest: string
  terms?: string[]
  maxSources?: number
}

export interface CorpusBuildAccepted {
  corpusId: string
  alreadyBuilt: boolean
  discovered: number
  acquired: number
  passages: number
  run: AgentRunAccepted
  corpusUrl: string
}

/** Propose an acquisition scope from a bare question, for the user to review. */
export function resolveInvestigationScope(question: string) {
  return requestJson<ProposedScopeResponse>('/api/investigations/resolve-scope', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })
}

/** Acquire free/local sources for a topic, build a corpus, and start a run. */
export function buildInvestigation(submission: TopicBuildSubmission) {
  return requestJson<CorpusBuildAccepted>('/api/investigations/build', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(submission),
  })
}

export function fetchAgentRun(runId: string) {
  return requestJson<AgentRunRecord>(`/api/agent-runs/${encodeURIComponent(runId)}`)
}

export function resumeAgentRun(runId: string) {
  return requestJson<AgentRunAccepted>(`/api/agent-runs/${encodeURIComponent(runId)}/resume`, {
    method: 'POST',
  })
}

export function isTerminalAgentStatus(status: AgentRunStatus) {
  return ['answer_ready', 'abstained', 'cancelled', 'failed'].includes(status)
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(resolveAgentApiUrl(path), init)
  } catch {
    throw new AgentApiError(
      'Chronicle could not reach the local research service. Start the backend and try again.',
    )
  }
  if (!response.ok) {
    let detail = `Chronicle’s research service returned ${response.status}.`
    try {
      const body = (await response.json()) as { detail?: unknown }
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      // Preserve the bounded status-based message when the body is not JSON.
    }
    throw new AgentApiError(detail, response.status)
  }
  return (await response.json()) as T
}
