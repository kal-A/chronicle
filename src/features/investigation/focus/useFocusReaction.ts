import { useEffect, useRef } from 'react'
import type { FocusSource, FocusUpdate, FocusValue } from '../model/focus'

/**
 * Subscribes a facet to Focus updates, skipping updates the facet itself
 * caused — the feedback-loop rule in docs/design/map-timeline-graph-sync.md.
 * E.g. clicking a map pin updates focus with source: 'map'; the map facet's
 * own reaction should not then re-run and re-ease its camera in response to
 * the update it just caused.
 */
export function useFocusReaction(
  facet: FocusSource,
  update: FocusUpdate,
  reaction: (focus: FocusValue) => void,
) {
  const reactionRef = useRef(reaction)
  reactionRef.current = reaction

  useEffect(() => {
    if (update.source === facet) return
    reactionRef.current(update.focus)
  }, [update, facet])
}
