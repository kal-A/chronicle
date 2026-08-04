import { useContext } from 'react'
import { FocusContext } from './focusContextObject'

/** Read the current Focus, its last update (with source), and a setter — must be used within a FocusProvider. */
export function useFocus() {
  const ctx = useContext(FocusContext)
  if (!ctx) {
    throw new Error('useFocus must be used within a FocusProvider')
  }
  return ctx
}
