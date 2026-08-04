import { useState } from 'react'
import type { Scene, Claim, Relationship, KnownAtTime } from '../model/schema'
import type { FocusValue } from '../model/focus'
import { formatHistoricalDate } from '../model/formatHistoricalDate'
import { SourceDetail } from './SourceDetail'

interface ResolvedEvidence {
  claims: Claim[]
  relationships: Relationship[]
  knownAtTimes: KnownAtTime[]
}

/**
 * Resolves evidence for the current Focus from explicitly curated
 * relationships (Event.relatedRecordIds), not fragile inference. Scene-level
 * focus shows everything curated so far; record/source/event/place focus is
 * scoped through explicit IDs and evidence links.
 */
function resolveEvidence(scene: Scene, focus: FocusValue): ResolvedEvidence {
  if (focus.kind === 'scene') {
    return {
      claims: scene.claims,
      relationships: scene.relationships,
      knownAtTimes: scene.knownAtTimes,
    }
  }

  let relatedIds = new Set<string>()

  if (focus.kind === 'event') {
    const event = scene.events.find((e) => e.id === focus.eventId)
    relatedIds = new Set(event?.relatedRecordIds ?? [])
  } else if (focus.kind === 'entity' && focus.entityType === 'place') {
    const eventsAtPlace = scene.events.filter((e) => e.placeId === focus.entityId)
    relatedIds = new Set(eventsAtPlace.flatMap((e) => e.relatedRecordIds))
  } else if (focus.kind === 'claim') {
    relatedIds = new Set([focus.claimId])
  } else if (focus.kind === 'relationship') {
    const relationship = scene.relationships.find(
      (candidate) => candidate.id === focus.relationshipId,
    )
    relatedIds = new Set(
      relationship
        ? [relationship.id, relationship.fromId, relationship.toId]
        : [],
    )
  } else if (focus.kind === 'source') {
    const documentIds = new Set(
      scene.documents
        .filter((document) => document.sourceId === focus.sourceId)
        .map((document) => document.id),
    )
    const passageIds = new Set(
      scene.passages
        .filter((passage) => documentIds.has(passage.documentId))
        .map((passage) => passage.id),
    )
    relatedIds = recordIdsLinkedToPassages(scene, passageIds)
  } else if (focus.kind === 'passage') {
    relatedIds = recordIdsLinkedToPassages(scene, new Set([focus.passageId]))
  }

  return {
    claims: scene.claims.filter((c) => relatedIds.has(c.id)),
    relationships: scene.relationships.filter(
      (r) => relatedIds.has(r.id) || relatedIds.has(r.fromId) || relatedIds.has(r.toId),
    ),
    knownAtTimes: scene.knownAtTimes.filter((k) => relatedIds.has(k.id)),
  }
}

function recordIdsLinkedToPassages(scene: Scene, passageIds: Set<string>) {
  const relatedIds = new Set<string>()
  for (const record of [
    ...scene.claims,
    ...scene.relationships,
    ...scene.knownAtTimes,
  ]) {
    if (record.evidenceLinks.some((link) => passageIds.has(link.passageId))) {
      relatedIds.add(record.id)
    }
  }
  return relatedIds
}

function passageFor(scene: Scene, passageId: string) {
  const passage = scene.passages.find((p) => p.id === passageId)
  if (!passage) return null
  const document = scene.documents.find((d) => d.id === passage.documentId)
  const source = document
    ? scene.sources.find((s) => s.id === document.sourceId)
    : undefined
  return { passage, document, source }
}

const ROLE_STYLE: Record<string, string> = {
  supporting: 'text-emerald-700 dark:text-emerald-400',
  counterevidence: 'text-rose-700 dark:text-rose-400',
  context: 'text-neutral-500 dark:text-neutral-400',
}

export function EvidencePanel({
  scene,
  focus,
  onSelectFocus,
}: {
  scene: Scene
  focus: FocusValue
  onSelectFocus: (focus: FocusValue) => void
}) {
  const evidence = resolveEvidence(scene, focus)
  const [selectedSource, setSelectedSource] = useState<{
    sourceId: string
    passageId: string
  } | null>(null)
  const hasAnything =
    evidence.claims.length > 0 ||
    evidence.relationships.length > 0 ||
    evidence.knownAtTimes.length > 0

  return (
    <section aria-labelledby="evidence-heading" className="flex flex-col gap-3">
      <h2
        id="evidence-heading"
        className="text-xs font-bold uppercase tracking-wider text-neutral-500 dark:text-neutral-400"
      >
        Evidence
      </h2>

      {!hasAnything && (
        <p className="rounded-lg border border-dashed border-neutral-300 p-3 text-sm text-neutral-500 dark:border-neutral-700 dark:text-neutral-400">
          No reviewed or prototype-curated evidence is linked to this
          selection yet.
        </p>
      )}

      {evidence.claims.map((claim) => (
        <div
          key={claim.id}
          className="rounded-lg border border-neutral-200 bg-white p-3 text-sm dark:border-neutral-800 dark:bg-neutral-900"
        >
          <p className="font-medium text-neutral-900 dark:text-neutral-50">
            {claim.statement}
          </p>
          <p className="mt-1 text-xs text-neutral-500 dark:text-neutral-400">
            {claim.directOrInferred === 'direct' ? 'Direct' : 'Inferred'} claim ·{' '}
            {claim.reviewStatus}
          </p>
          <ul className="mt-2 flex flex-col gap-2">
            {claim.evidenceLinks.map((link) => {
              const resolved = passageFor(scene, link.passageId)
              if (!resolved) return null
              return (
                <li
                  key={link.passageId}
                  className="border-l-2 border-neutral-200 pl-2 dark:border-neutral-700"
                >
                  <p
                    className={`text-[11px] font-semibold uppercase tracking-wide ${
                      ROLE_STYLE[link.role] ?? ''
                    }`}
                  >
                    {link.role}
                  </p>
                  <p className="italic text-neutral-700 dark:text-neutral-300">
                    “{resolved.passage.excerpt}”
                  </p>
                  <p className="text-xs text-neutral-500 dark:text-neutral-400">
                    {resolved.passage.locator}
                    {resolved.document && ` — ${resolved.document.editionCitation}`}
                    {resolved.source && ` — ${resolved.source.title}`}
                  </p>
                  {resolved.source && (
                    <button
                      type="button"
                      className="mt-1 text-xs font-semibold text-blue-700 hover:underline dark:text-blue-400"
                      onClick={() =>
                        {
                          setSelectedSource({
                            sourceId: resolved.source!.id,
                            passageId: resolved.passage.id,
                          })
                          onSelectFocus({
                            kind: 'source',
                            sourceId: resolved.source!.id,
                          })
                        }
                      }
                    >
                      View source →
                    </button>
                  )}
                </li>
              )
            })}
          </ul>
        </div>
      ))}

      {evidence.relationships.map((rel) => (
        <div
          key={rel.id}
          className="rounded-lg border border-dashed border-amber-400 bg-amber-50/60 p-3 text-sm dark:border-amber-700 dark:bg-amber-950/20"
        >
          <p className="font-bold uppercase tracking-wide text-amber-700 dark:text-amber-400">
            {rel.evidenceClassification.replace('_', ' ')}
          </p>
          <p className="text-xs text-neutral-600 dark:text-neutral-400">
            {rel.relationshipType}
          </p>
          <ul className="mt-2 flex flex-col gap-2">
            {rel.evidenceLinks.map((link) => {
              const resolved = passageFor(scene, link.passageId)
              if (!resolved) return null
              return (
                <li
                  key={link.passageId}
                  className="border-l-2 border-neutral-200 pl-2 dark:border-neutral-700"
                >
                  <p
                    className={`text-[11px] font-semibold uppercase tracking-wide ${
                      ROLE_STYLE[link.role] ?? ''
                    }`}
                  >
                    {link.role}
                  </p>
                  <p className="italic text-neutral-700 dark:text-neutral-300">
                    “{resolved.passage.excerpt}”
                  </p>
                  {link.reviewerNote && (
                    <p className="text-xs text-neutral-500 dark:text-neutral-400">
                      {link.reviewerNote}
                    </p>
                  )}
                  {resolved.source && (
                    <button
                      type="button"
                      className="mt-1 text-xs font-semibold text-blue-700 hover:underline dark:text-blue-400"
                      onClick={() =>
                        {
                          setSelectedSource({
                            sourceId: resolved.source!.id,
                            passageId: resolved.passage.id,
                          })
                          onSelectFocus({
                            kind: 'source',
                            sourceId: resolved.source!.id,
                          })
                        }
                      }
                    >
                      View source →
                    </button>
                  )}
                </li>
              )
            })}
          </ul>
        </div>
      ))}

      {evidence.knownAtTimes.map((kat) => (
        <div
          key={kat.id}
          className="rounded-lg border border-neutral-200 bg-white p-3 text-sm dark:border-neutral-800 dark:bg-neutral-900"
        >
          <p className="text-neutral-800 dark:text-neutral-200">
            Known as of{' '}
            <strong className="text-neutral-900 dark:text-neutral-50">
              {formatHistoricalDate(kat.asOfDate)}
            </strong>
            : {kat.fact}
          </p>
        </div>
      ))}

      {selectedSource && (
        <SourceDetail
          scene={scene}
          sourceId={selectedSource.sourceId}
          highlightPassageId={selectedSource.passageId}
          onSelectPassage={(passageId) =>
            onSelectFocus({ kind: 'passage', passageId })
          }
          onClose={() => setSelectedSource(null)}
        />
      )}
    </section>
  )
}
