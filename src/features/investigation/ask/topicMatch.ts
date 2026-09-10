import type { GeneratedInvestigation } from '../model/generatedInvestigation'

/**
 * Routes a typed question to a *curated* investigation when one matches, so the
 * two hand-authored topics open their rich map-first workspace. A match is
 * scored against each investigation's own real InvestigationExperiencePlan.opening
 * content — no separate, hand-maintained keyword list to fall out of sync.
 *
 * A non-match is no longer a dead-end: AskEntryPage routes it to the live
 * generation path (useAskGeneration), which acquires free/public sources, builds
 * a corpus, runs the four-agent investigation, and presents the real cited
 * answer or honest abstention inline. A generated corpus is passage-only, so it
 * does not drive the map workspace — that stays reserved for curated content.
 */

const STOPWORDS = new Set([
  'a', 'an', 'the', 'of', 'in', 'on', 'at', 'to', 'and', 'or', 'did', 'do',
  'does', 'how', 'what', 'when', 'where', 'why', 'who', 'was', 'were', 'is',
  'are', 'be', 'been', 'it', 'its', 'this', 'that', 'with', 'for', 'by',
  'as', 'from', 'about',
])

function significantWords(text: string): Set<string> {
  return new Set(
    text
      .toLowerCase()
      .split(/[^a-z0-9]+/)
      .filter((word) => word.length > 2 && !STOPWORDS.has(word)),
  )
}

function score(questionWords: Set<string>, investigation: GeneratedInvestigation): number {
  const plan = investigation.experiencePlan
  if (!plan) return 0

  const corpus = significantWords(
    `${plan.opening.question} ${plan.opening.scopeSummary} ${investigation.presentation.title}`,
  )

  let matches = 0
  for (const word of questionWords) {
    if (corpus.has(word)) matches += 1
  }
  return matches
}

const MINIMUM_MATCH_SCORE = 2

export function matchInvestigationToQuestion(
  question: string,
  investigations: GeneratedInvestigation[],
): GeneratedInvestigation | null {
  const questionWords = significantWords(question)
  if (questionWords.size === 0) return null

  let best: GeneratedInvestigation | null = null
  let bestScore = 0

  for (const investigation of investigations) {
    const candidateScore = score(questionWords, investigation)
    if (candidateScore > bestScore) {
      best = investigation
      bestScore = candidateScore
    }
  }

  return bestScore >= MINIMUM_MATCH_SCORE ? best : null
}
