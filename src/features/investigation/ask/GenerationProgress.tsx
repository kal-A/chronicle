import { useEffect, useState } from 'react'
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

  useEffect(() => {
    if (completedCount >= GENERATION_STAGES.length) {
      onComplete()
      return
    }

    const delay = prefersReducedMotion ? REDUCED_MOTION_STEP_DELAY_MS : stepDelayMs
    const timer = window.setTimeout(() => setCompletedCount((count) => count + 1), delay)
    return () => window.clearTimeout(timer)
  }, [completedCount, onComplete, prefersReducedMotion, stepDelayMs])

  return (
    <div
      role="status"
      aria-label="Generation progress"
      className="flex flex-col gap-4 rounded-lg border border-neutral-300 bg-white p-5 dark:border-neutral-700 dark:bg-neutral-900"
    >
      <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-50">
        Preparing your investigation
      </h2>
      <ul className="flex flex-col gap-1.5 text-sm">
        {GENERATION_STAGES.map((stage, index) => {
          const isComplete = index < completedCount
          const isCurrent = index === completedCount
          return (
            <li
              key={stage.id}
              className={
                isComplete
                  ? 'text-neutral-700 dark:text-neutral-300'
                  : 'text-neutral-400 dark:text-neutral-600'
              }
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
