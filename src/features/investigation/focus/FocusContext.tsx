import type { ReactNode } from 'react'
import { FocusContext } from './focusContextObject'
import { useFocusUrlState } from './useFocusUrlState'
import type { FocusValue } from '../model/focus'

export function FocusProvider({
  defaultFocus,
  children,
}: {
  defaultFocus: FocusValue
  children: ReactNode
}) {
  const { focus, update, setFocus } = useFocusUrlState(defaultFocus)
  return (
    <FocusContext.Provider value={{ focus, update, setFocus }}>
      {children}
    </FocusContext.Provider>
  )
}
