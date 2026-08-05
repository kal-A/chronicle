import type { GeneratedInvestigation } from '../model/generatedInvestigation'

/**
 * No live generation pipeline is wired to the frontend yet (the Python
 * backend is CLI-only; live model/search calls are deferred past Phase C —
 * docs/decisions/ADR-002-map-first-workspace.md). Rather than pretending to
 * generate a new investigation, the Ask entry surface matches a typed
 * question against the investigations that actually exist, scored against
 * their own real InvestigationExperiencePlan.opening content — no separate,
 * hand-maintained keyword list to fall out of sync with real content.
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
