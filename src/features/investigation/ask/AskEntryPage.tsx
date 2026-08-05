import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { investigationFixtures } from '../../../content/investigationFixtures'
import type { GeneratedInvestigation } from '../model/generatedInvestigation'
import { GenerationProgress } from './GenerationProgress'
import { ScopeReviewCard } from './ScopeReviewCard'
import { matchInvestigationToQuestion } from './topicMatch'

type AskState = { step: 'ask' } | { step: 'no-match' } | { step: 'scope-review' | 'generating'; investigation: GeneratedInvestigation }

const investigationsWithAPlan = investigationFixtures
  .map((fixture) => fixture.investigation)
  .filter((investigation) => investigation.experiencePlan)

/**
 * map-first-workspace-instructions.md §4-6's initial interaction surface,
 * mounted at `/` (src/app/routes.tsx). No live generation pipeline is wired
 * to the frontend yet, so submitting a question matches against the
 * investigations that actually exist rather than pretending to generate a
 * new one — see topicMatch.ts's docstring for why.
 */
export function AskEntryPage({
  generationStepDelayMs,
}: {
  /** Test-only override for GenerationProgress's per-stage delay. */
  generationStepDelayMs?: number
} = {}) {
  const [state, setState] = useState<AskState>({ step: 'ask' })
  const [question, setQuestion] = useState('')
  const navigate = useNavigate()

  function submit(submittedQuestion: string) {
    const match = matchInvestigationToQuestion(submittedQuestion, investigationsWithAPlan)
    setQuestion(submittedQuestion)
    setState(match ? { step: 'scope-review', investigation: match } : { step: 'no-match' })
  }

  function handleGenerationComplete(investigation: GeneratedInvestigation) {
    navigate(
      `/investigations/${encodeURIComponent(investigation.packageId)}/scenes/${encodeURIComponent(
        investigation.interactionSpec.defaultSceneId,
      )}`,
    )
  }

  return (
    <main className="mx-auto flex min-h-svh max-w-2xl flex-col gap-6 px-4 py-16">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-neutral-900 dark:text-neutral-50">
          Chronicle
        </h1>
        <p className="mt-2 text-lg text-neutral-700 dark:text-neutral-300">
          What would you like to investigate?
        </p>
      </div>

      {state.step === 'ask' || state.step === 'no-match' ? (
        <AskForm
          question={question}
          onQuestionChange={setQuestion}
          onSubmit={submit}
          noMatch={state.step === 'no-match'}
        />
      ) : null}

      {state.step === 'scope-review' ? (
        <ScopeReviewCard
          opening={state.investigation.experiencePlan!.opening}
          onGenerate={() => setState({ step: 'generating', investigation: state.investigation })}
          onAskSomethingElse={() => setState({ step: 'ask' })}
        />
      ) : null}

      {state.step === 'generating' ? (
        <GenerationProgress
          onComplete={() => handleGenerationComplete(state.investigation)}
          stepDelayMs={generationStepDelayMs}
        />
      ) : null}
    </main>
  )
}

function AskForm({
  question,
  onQuestionChange,
  onSubmit,
  noMatch,
}: {
  question: string
  onQuestionChange: (value: string) => void
  onSubmit: (question: string) => void
  noMatch: boolean
}) {
  return (
    <div className="flex flex-col gap-4">
      <form
        onSubmit={(event) => {
          event.preventDefault()
          onSubmit(question)
        }}
        className="flex gap-2"
      >
        <label htmlFor="ask-entry-question" className="sr-only">
          Ask a historical question
        </label>
        <input
          id="ask-entry-question"
          type="text"
          value={question}
          onChange={(event) => onQuestionChange(event.target.value)}
          placeholder="Ask a historical question…"
          className="flex-1 rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 dark:border-neutral-700 dark:bg-neutral-950 dark:text-neutral-100"
        />
        <button
          type="submit"
          className="rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white hover:bg-neutral-700 dark:bg-neutral-100 dark:text-neutral-900 dark:hover:bg-neutral-300"
        >
          Ask
        </button>
      </form>

      {noMatch ? (
        <p role="alert" className="text-sm text-neutral-700 dark:text-neutral-300">
          This prototype only has investigations for the topics below — nothing curated matches
          that question yet.
        </p>
      ) : null}

      <div>
        <h2 className="text-sm font-medium text-neutral-600 dark:text-neutral-400">
          Suggested starting points
        </h2>
        <ul className="mt-2 flex flex-col gap-1.5">
          {investigationsWithAPlan.map((investigation) => {
            const startingQuestion = investigation.experiencePlan!.opening.question
            return (
              <li key={investigation.packageId}>
                <button
                  type="button"
                  onClick={() => onSubmit(startingQuestion)}
                  className="text-left text-sm text-blue-700 underline hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  {startingQuestion}
                </button>
              </li>
            )
          })}
        </ul>
      </div>
    </div>
  )
}
