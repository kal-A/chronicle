import { useEffect, useState } from 'react'
import { usePrefersReducedMotion } from './useReducedMotion'

const HEADLINE_INTERVAL_MS = 42
const INTRO_INTERVAL_MS = 16
const BETWEEN_LINES_MS = 180

export function useHeroIntro(headline: string, intro: string) {
  const prefersReducedMotion = usePrefersReducedMotion()
  const shouldSkipAnimation = prefersReducedMotion || import.meta.env.MODE === 'test'
  const [headlineLength, setHeadlineLength] = useState(shouldSkipAnimation ? headline.length : 0)
  const [introLength, setIntroLength] = useState(shouldSkipAnimation ? intro.length : 0)

  useEffect(() => {
    if (shouldSkipAnimation) {
      setHeadlineLength(headline.length)
      setIntroLength(intro.length)
      return
    }

    let headlineTimer: number | undefined
    let introTimer: number | undefined
    let betweenTimer: number | undefined

    headlineTimer = window.setInterval(() => {
      setHeadlineLength((length) => {
        if (length >= headline.length) {
          if (headlineTimer) window.clearInterval(headlineTimer)
          betweenTimer = window.setTimeout(() => {
            introTimer = window.setInterval(() => {
              setIntroLength((introCharacters) => {
                if (introCharacters >= intro.length) {
                  if (introTimer) window.clearInterval(introTimer)
                  return introCharacters
                }
                return introCharacters + 1
              })
            }, INTRO_INTERVAL_MS)
          }, BETWEEN_LINES_MS)
          return length
        }
        return length + 1
      })
    }, HEADLINE_INTERVAL_MS)

    return () => {
      if (headlineTimer) window.clearInterval(headlineTimer)
      if (introTimer) window.clearInterval(introTimer)
      if (betweenTimer) window.clearTimeout(betweenTimer)
    }
  }, [headline, intro, shouldSkipAnimation])

  const totalCharacters = headline.length + intro.length
  const typedCharacters = headlineLength + introLength

  return {
    headlineText: headline.slice(0, headlineLength),
    introText: intro.slice(0, introLength),
    headlineProgress: headline.length === 0 ? 1 : headlineLength / headline.length,
    introProgress: intro.length === 0 ? 1 : introLength / intro.length,
    progress: totalCharacters === 0 ? 1 : typedCharacters / totalCharacters,
    isComplete: typedCharacters >= totalCharacters,
  }
}
