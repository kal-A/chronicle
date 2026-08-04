import { useEffect, useRef } from 'react'
import type { Scene } from '../model/schema'
import { formatHistoricalDate } from '../model/formatHistoricalDate'

/**
 * Chronicle only ever stores short attributed excerpts, never a source's
 * full text (AGENTS.md short-excerpt discipline) — so "highlight the
 * evidence within the source" means showing the source's full bibliographic
 * record and every passage Chronicle has actually extracted from it, with
 * the triggering passage visually anchored, rather than pretending to show
 * full scanned pages Chronicle doesn't hold.
 */
export function SourceDetail({
  scene,
  sourceId,
  highlightPassageId,
  onSelectPassage,
  onClose,
}: {
  scene: Scene
  sourceId: string
  highlightPassageId: string
  onSelectPassage: (passageId: string) => void
  onClose: () => void
}) {
  const highlightRef = useRef<HTMLLIElement>(null)

  useEffect(() => {
    const highlightedPassage = highlightRef.current
    if (typeof highlightedPassage?.scrollIntoView === 'function') {
      highlightedPassage.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }
  }, [highlightPassageId])

  const source = scene.sources.find((s) => s.id === sourceId)
  const documents = scene.documents.filter((d) => d.sourceId === sourceId)
  const documentIds = new Set(documents.map((d) => d.id))
  const passages = scene.passages.filter((p) => documentIds.has(p.documentId))

  if (!source) return null

  return (
    <div
      role="dialog"
      aria-labelledby="source-detail-heading"
      className="flex flex-col gap-3 rounded-lg border border-neutral-200 bg-white p-3 text-sm dark:border-neutral-800 dark:bg-neutral-900"
    >
      <div className="flex items-start justify-between gap-2">
        <h3 id="source-detail-heading" className="font-bold text-neutral-900 dark:text-neutral-50">
          {source.title}
        </h3>
        <button
          type="button"
          onClick={onClose}
          className="rounded border border-neutral-300 px-2 py-1 text-xs font-medium text-neutral-700 hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
        >
          Close
        </button>
      </div>

      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-xs text-neutral-600 dark:text-neutral-400">
        <dt className="font-semibold">Origin</dt>
        <dd>{source.authorOrOrigin}</dd>
        <dt className="font-semibold">Date</dt>
        <dd>{formatHistoricalDate(source.dateOfSource)}</dd>
        <dt className="font-semibold">Rights</dt>
        <dd>{source.rightsStatus.replace('-', ' ')}</dd>
        <dt className="font-semibold">Status</dt>
        <dd>{source.curationStatus.replace('-', ' ')}</dd>
        <dt className="font-semibold">Known limitations</dt>
        <dd>{source.knownLimitations}</dd>
        <dt className="font-semibold">Location</dt>
        <dd className="break-all">{source.linkOrLocation}</dd>
      </dl>

      {documents.map((document) => (
        <p key={document.id} className="text-xs text-neutral-500 dark:text-neutral-400">
          Edition: {document.editionCitation}
          {document.translationCredit && ` — translated by ${document.translationCredit}`}
        </p>
      ))}

      <div>
        <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
          Passages Chronicle has extracted from this source
        </h4>
        <ul className="mt-2 flex flex-col gap-2">
          {passages.map((passage) => {
            const isHighlighted = passage.id === highlightPassageId
            return (
              <li
                key={passage.id}
                ref={isHighlighted ? highlightRef : undefined}
                className={`rounded-lg border p-2 ${
                  isHighlighted
                    ? 'border-blue-600 border-l-4 bg-blue-50 dark:bg-blue-950/40'
                    : 'border-neutral-200 dark:border-neutral-800'
                }`}
              >
                <button
                  type="button"
                  className="w-full rounded text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
                  onClick={() => onSelectPassage(passage.id)}
                >
                  <span className="block italic text-neutral-700 dark:text-neutral-300">
                    “{passage.excerpt}”
                  </span>
                  <span className="mt-1 block text-xs text-neutral-500 dark:text-neutral-400">
                    {passage.locator}
                  </span>
                </button>
              </li>
            )
          })}
        </ul>
      </div>
    </div>
  )
}
