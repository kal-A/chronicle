import { useCallback, useMemo, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import type { FocusSource, FocusUpdate, FocusValue } from '../model/focus'
import { decodeFocus, encodeFocus } from './serialization'

/**
 * URL-persisted Focus state (docs/design/map-timeline-graph-sync.md).
 *
 * `defaultFocus` is used whenever the URL carries no (or an invalid) focus —
 * this is the "invalid-ID fallback" behavior required by
 * plans/phase-1-static-prototype.md Plan 3, and it doubles as reload/deep-link
 * support since decoding runs from the URL on every render.
 *
 * Explicit `setFocus` calls push a new history entry (not replace), so
 * browser back/forward moves through the focus history a reader actually
 * created — this is what "preservation of narrative position" and "history
 * navigation" mean in practice.
 */
export function useFocusUrlState(defaultFocus: FocusValue) {
  const [searchParams, setSearchParams] = useSearchParams()

  const sourceRef = useRef<FocusSource>('url')
  const lastSetSearchRef = useRef<string | null>(null)

  const focus = useMemo<FocusValue>(
    () => decodeFocus(searchParams) ?? defaultFocus,
    [searchParams, defaultFocus],
  )

  const currentSearch = searchParams.toString()
  // Only trust the recorded source if the URL still matches exactly what we
  // last set ourselves. Any other change (typed URL, deep link, browser
  // back/forward landing on a different history entry) is treated as
  // externally sourced, per the feedback-loop rule in
  // docs/design/map-timeline-graph-sync.md.
  const source: FocusSource =
    lastSetSearchRef.current === currentSearch ? sourceRef.current : 'url'

  const setFocus = useCallback(
    (next: FocusValue, updateSource: FocusSource) => {
      const params = encodeFocus(next)
      sourceRef.current = updateSource
      lastSetSearchRef.current = params.toString()
      setSearchParams(params)
    },
    [setSearchParams],
  )

  const update = useMemo<FocusUpdate>(() => ({ focus, source }), [focus, source])

  return { focus, update, setFocus }
}
