import { useSearchParams } from 'react-router-dom'

const LENS_PARAM = 'lens'

/** URL-persisted active lens id — deep-linkable, like Focus, but without the
 * feedback-loop source-tag machinery FocusValue needs (lens switches don't
 * have the same self-triggered-reaction problem a facet's own click does). */
export function useActiveLensId(defaultLensId: string): [string, (id: string) => void] {
  const [searchParams, setSearchParams] = useSearchParams()
  const activeLensId = searchParams.get(LENS_PARAM) ?? defaultLensId

  function setActiveLensId(id: string) {
    const next = new URLSearchParams(searchParams)
    next.set(LENS_PARAM, id)
    setSearchParams(next)
  }

  return [activeLensId, setActiveLensId]
}
