import { useEffect, useRef, useState } from 'react'
import { GENERATION_STAGES } from './stageNames'
import { usePrefersReducedMotion } from './useReducedMotion'

const STEP_DELAY_MS = 350
const REDUCED_MOTION_STEP_DELAY_MS = 20

/**
 * map-first-workspace-instructions.md §6.1: structured workflow state, not
 * private model reasoning. Ticks through the real 8-stage pipeline sequence
 * on a short timer, then calls onComplete — this is presentation timing over
 * a package that already exists (see topicMatch.ts's docstring), not a real
 * generation run.
 */
export function GenerationProgress({
  onComplete,
  stepDelayMs = STEP_DELAY_MS,
}: {
  onComplete: () => void
  /** Test-only override — production callers rely on the default. */
  stepDelayMs?: number
}) {
  const [completedCount, setCompletedCount] = useState(0)
  const prefersReducedMotion = usePrefersReducedMotion()
  const onCompleteRef = useRef(onComplete)
  onCompleteRef.current = onComplete

  useEffect(() => {
    if (completedCount >= GENERATION_STAGES.length) {
      onCompleteRef.current()
      return
    }

    const delay = prefersReducedMotion ? REDUCED_MOTION_STEP_DELAY_MS : stepDelayMs
    const timer = window.setTimeout(() => setCompletedCount((count) => count + 1), delay)
    return () => window.clearTimeout(timer)
  }, [completedCount, prefersReducedMotion, stepDelayMs])

  return (
    <div
      role="status"
      aria-label="Generation progress"
      className="chronicle-generation-card"
    >
      <p className="chronicle-eyebrow">Building the workspace</p>
      <h2>Preparing your investigation</h2>
      <ul>
        {GENERATION_STAGES.map((stage, index) => {
          const isComplete = index < completedCount
          const isCurrent = index === completedCount
          return (
            <li
              key={stage.id}
              className={isComplete ? 'is-complete' : isCurrent ? 'is-current' : ''}
            >
              <span aria-hidden="true">{isComplete ? '✔' : isCurrent ? '…' : ' '} </span>
              {stage.label}
            </li>
          )
        })}
      </ul>
    </div>
  )
}
