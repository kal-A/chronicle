import { createContext } from 'react'
import type { FocusSource, FocusUpdate, FocusValue } from '../model/focus'

export interface FocusContextValue {
  focus: FocusValue
  update: FocusUpdate
  setFocus: (focus: FocusValue, source: FocusSource) => void
}

export const FocusContext = createContext<FocusContextValue | null>(null)
