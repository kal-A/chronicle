import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useNavigate } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import type { FocusValue } from '../model/focus'
import { useFocusReaction } from './useFocusReaction'
import { useFocusUrlState } from './useFocusUrlState'

const defaultFocus: FocusValue = {
  kind: 'scene',
  sceneId: 'scene-2-blank-cheque',
}

const otherFocus: FocusValue = {
  kind: 'entity',
  entityId: 'person-wilhelm-ii',
  entityType: 'person',
}

function Harness({
  onMapReaction,
}: {
  onMapReaction: (focus: FocusValue) => void
}) {
  const { focus, update, setFocus } = useFocusUrlState(defaultFocus)
  const navigate = useNavigate()

  // The 'map' facet reacts to every focus update it did not itself cause.
  useFocusReaction('map', update, onMapReaction)

  return (
    <div>
      <div data-testid="focus">{JSON.stringify(focus)}</div>
      <div data-testid="source">{update.source}</div>
      <button onClick={() => setFocus(otherFocus, 'narrative')}>
        select-from-narrative
      </button>
      <button onClick={() => setFocus(otherFocus, 'map')}>
        select-from-map
      </button>
      <button onClick={() => navigate(-1)}>back</button>
    </div>
  )
}

function renderHarness() {
  const reactions: FocusValue[] = []
  render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route
          path="/"
          element={<Harness onMapReaction={(f) => reactions.push(f)} />}
        />
      </Routes>
    </MemoryRouter>,
  )
  return reactions
}

describe('useFocusUrlState', () => {
  it('falls back to the default focus when the URL carries none (reload/deep-link support)', () => {
    renderHarness()
    expect(screen.getByTestId('focus')).toHaveTextContent(
      JSON.stringify(defaultFocus),
    )
  })

  it('updates focus via setFocus and reflects it in state', async () => {
    const user = userEvent.setup()
    renderHarness()
    await user.click(screen.getByText('select-from-narrative'))
    expect(screen.getByTestId('focus')).toHaveTextContent(
      JSON.stringify(otherFocus),
    )
  })

  it('feedback-loop suppression: a facet does not react to a focus change it caused itself', async () => {
    const user = userEvent.setup()
    const reactions = renderHarness()

    // Mounting itself produces one reaction (a facet must sync to the
    // initial focus, e.g. the map centering on load) — that one is
    // source: 'url', not self-caused, so it's expected here.
    const afterMount = reactions.length
    expect(afterMount).toBe(1)

    await user.click(screen.getByText('select-from-map'))
    // The map facet caused this change itself — it must not react to it.
    expect(reactions).toHaveLength(afterMount)

    await user.click(screen.getByText('select-from-narrative'))
    // A different facet caused this one — the map facet must react.
    expect(reactions).toHaveLength(afterMount + 1)
    expect(reactions.at(-1)).toEqual(otherFocus)
  })

  it('supports browser back/forward: history navigation reverts focus', async () => {
    const user = userEvent.setup()
    renderHarness()

    await user.click(screen.getByText('select-from-narrative'))
    expect(screen.getByTestId('focus')).toHaveTextContent(
      JSON.stringify(otherFocus),
    )

    await user.click(screen.getByText('back'))
    expect(screen.getByTestId('focus')).toHaveTextContent(
      JSON.stringify(defaultFocus),
    )
    // Landing here via back navigation, not an explicit setFocus call —
    // source must be attributed to 'url', not stale-tagged to whichever
    // facet last called setFocus.
    expect(screen.getByTestId('source')).toHaveTextContent('url')
  })
})
