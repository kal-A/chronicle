import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { investigationFixtures } from '../../../content/investigationFixtures'
import type { GeneratedInvestigation } from '../model/generatedInvestigation'
import { AtlanticAtlas } from './AtlanticAtlas'
import { CartographicTransition } from './CartographicTransition'
import { GenerationProgress } from './GenerationProgress'
import { ScopeReviewCard } from './ScopeReviewCard'
import { matchInvestigationToQuestion } from './topicMatch'
import { useHeroIntro } from './useHeroIntro'
import { usePrefersReducedMotion } from './useReducedMotion'

const HERO_HEADLINE = 'Where do you want to begin?'
const HERO_INTRO =
  'Follow an event through the places, people, sources, and arguments that shaped it.'
const TRANSITION_DELAY_MS = 900

type AskState =
  | { step: 'ask' }
  | { step: 'no-match' }
  | {
      step: 'scope-review' | 'generating' | 'transitioning'
      investigation: GeneratedInvestigation
    }

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
  const prefersReducedMotion = usePrefersReducedMotion()
  const heroIntro = useHeroIntro(HERO_HEADLINE, HERO_INTRO)
  const atlasDrawProgress = Math.min(
    1,
    heroIntro.headlineProgress * 0.72 + heroIntro.introProgress * 0.28,
  )

  function submit(submittedQuestion: string) {
    const normalizedQuestion = submittedQuestion.trim()
    if (!normalizedQuestion) return

    const match = matchInvestigationToQuestion(normalizedQuestion, investigationsWithAPlan)
    setQuestion(normalizedQuestion)
    setState(match ? { step: 'scope-review', investigation: match } : { step: 'no-match' })
  }

  function handleGenerationComplete(investigation: GeneratedInvestigation) {
    const destination = `/investigations/${encodeURIComponent(
      investigation.packageId,
    )}/scenes/${encodeURIComponent(investigation.interactionSpec.defaultSceneId)}`

    if (prefersReducedMotion) {
      navigate(destination, { state: { enteredFromAsk: true, question } })
      return
    }

    setState({ step: 'transitioning', investigation })
    window.setTimeout(
      () => navigate(destination, { state: { enteredFromAsk: true, question } }),
      generationStepDelayMs === undefined ? TRANSITION_DELAY_MS : 10,
    )
  }

  return (
    <main className={`chronicle-home ${state.step === 'transitioning' ? 'is-transitioning' : ''}`}>
      <section className="chronicle-hero" aria-labelledby="chronicle-home-heading">
        <AtlanticAtlas
          reveal={1}
          drawProgress={atlasDrawProgress}
        />

        <header className="chronicle-header">
          <a className="chronicle-brand" href="/" aria-label="Chronicle home">
            <h1>Chronicle</h1>
          </a>
          <nav aria-label="Primary navigation">
            <a href="#starting-points">Explore</a>
            <a href="#how-chronicle-works">About</a>
          </nav>
        </header>

        <div className="chronicle-task-plane">
          <h2 id="chronicle-home-heading" aria-label={HERO_HEADLINE}>
            <span aria-hidden="true">{heroIntro.headlineText}</span>
            <span
              className={`chronicle-type-caret ${heroIntro.isComplete ? 'is-complete' : ''}`}
              aria-hidden="true"
            />
          </h2>
          <p className="chronicle-intro">
            <span className="sr-only">{HERO_INTRO}</span>
            <span aria-hidden="true">{heroIntro.introText}</span>
          </p>

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
        </div>

        <a className="chronicle-scroll-cue" href="#how-chronicle-works">
          <span>How Chronicle works</span>
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="m7 10 5 5 5-5" />
          </svg>
        </a>
      </section>

      {state.step === 'transitioning' ? (
        <CartographicTransition investigation={state.investigation} question={question} />
      ) : null}

      <section id="how-chronicle-works" className="chronicle-workflow" aria-labelledby="workflow-title">
        <div className="chronicle-workflow-heading">
          <h2 id="workflow-title">An investigation, not an answer box.</h2>
        </div>
        <ol>
          <li><span>1</span><div><h3>Frame the question</h3><p>Define the event, period, or historical problem you want to pursue.</p></div></li>
          <li><span>2</span><div><h3>Review the scope</h3><p>See the proposed timeframe, geography, and current evidence coverage.</p></div></li>
          <li><span>3</span><div><h3>Enter the workspace</h3><p>Move through the map, timeline, sources, and connected claims.</p></div></li>
        </ol>
      </section>
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
    <div id="starting-points" className="chronicle-ask">
      <form
        onSubmit={(event) => {
          event.preventDefault()
          onSubmit(question)
        }}
        className="chronicle-question-form"
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
          autoComplete="off"
          className="chronicle-question-input"
        />
        <button
          type="submit"
          aria-label="Ask"
          disabled={!question.trim()}
          className="chronicle-ask-button"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M5 12h14M13 6l6 6-6 6" />
          </svg>
        </button>
        <span className="chronicle-action-caption">Begin an investigation</span>
      </form>

      {noMatch ? (
        <p role="alert" className="chronicle-no-match">
          This prototype only has investigations for the topics below — nothing curated matches
          that question yet.
        </p>
      ) : null}

      <div className="chronicle-starters">
        <div className="chronicle-starters-heading">
          <h3>Suggested starting points</h3>
          <p>This prototype searches two curated investigations.</p>
        </div>
        <ul>
          {investigationsWithAPlan.map((investigation) => {
            const startingQuestion = investigation.experiencePlan!.opening.question
            return (
              <li key={investigation.packageId}>
                <button
                  type="button"
                  onClick={() => onSubmit(startingQuestion)}
                  className="chronicle-starter"
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <circle cx="10" cy="10" r="5.5" />
                    <path d="m14 14 5 5" />
                  </svg>
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
