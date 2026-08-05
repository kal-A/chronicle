import { useEffect, useState } from 'react'

const QUERY = '(prefers-reduced-motion: reduce)'

/**
 * JS-side reduced-motion check for the generation-progress timer (D0.1's
 * definition-of-done criterion). src/index.css already zeroes CSS
 * animation/transition durations globally, but a JS setTimeout sequence
 * needs its own check — nothing else in this codebase drives a timed
 * animation from JS yet.
 */
export function usePrefersReducedMotion(): boolean {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(
    () => typeof window !== 'undefined' && window.matchMedia(QUERY).matches,
  )

  useEffect(() => {
    const mediaQueryList = window.matchMedia(QUERY)
    const onChange = () => setPrefersReducedMotion(mediaQueryList.matches)
    mediaQueryList.addEventListener('change', onChange)
    return () => mediaQueryList.removeEventListener('change', onChange)
  }, [])

  return prefersReducedMotion
}
