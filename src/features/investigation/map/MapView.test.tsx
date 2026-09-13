import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { MapView } from './MapView'
import type { Scene, PlaceEntity } from '../model/schema'
import type { FocusValue } from '../model/focus'

// MapView only reads scene.entities / scene.events / scene.mapLayer, so these
// tests construct just those fields rather than a whole schema-valid Scene.
function sceneWith(entities: PlaceEntity[]): Scene {
  return {
    id: 's1',
    title: 'Test scene',
    entities,
    events: [],
    mapLayer: undefined,
  } as unknown as Scene
}

function place(id: string, name: string, coordinates?: { lat: number; lng: number }): PlaceEntity {
  return {
    id,
    entityType: 'place',
    canonicalName: name,
    periodRecords: [
      { periodLabel: '1666', nameAtTime: name, controllingPolity: 'Unreviewed', precision: 'city' },
    ],
    reviewStatus: 'proposed',
    coordinates,
  }
}

const NEUTRAL_FOCUS: FocusValue = { kind: 'scene', sceneId: 's1' }
const noop = () => {}

describe('MapView generated-map fallback', () => {
  it('renders the generated MapLibre map when places have coordinates and there is no raster mapLayer', () => {
    const scene = sceneWith([place('p1', 'London', { lat: 51.507, lng: -0.128 })])

    render(<MapView scene={scene} focus={NEUTRAL_FOCUS} onSelectFocus={noop} />)

    // The WebGL canvas is a progressive enhancement that no-ops under jsdom, so
    // we assert the always-present provenance note that marks the generated-map
    // branch, and that the toy schematic fallback is NOT used.
    expect(screen.getByText(/Generated map — 1 located place\b/i)).toBeInTheDocument()
    expect(screen.queryByRole('img', { name: /schematic orientation map/i })).not.toBeInTheDocument()
  })

  it('falls back to the schematic map when no place has coordinates', () => {
    const scene = sceneWith([place('p1', 'Somewhere', undefined)])

    render(<MapView scene={scene} focus={NEUTRAL_FOCUS} onSelectFocus={noop} />)

    expect(screen.getByRole('img', { name: /schematic orientation map/i })).toBeInTheDocument()
    expect(screen.queryByText(/Generated map —/i)).not.toBeInTheDocument()
  })

  it('offers an accessible labels toggle that flips its pressed state', () => {
    const scene = sceneWith([place('p1', 'London', { lat: 51.507, lng: -0.128 })])

    render(<MapView scene={scene} focus={NEUTRAL_FOCUS} onSelectFocus={noop} />)

    const toggle = screen.getByRole('button', { name: /place labels/i })
    expect(toggle).toHaveAttribute('aria-pressed', 'true') // labels on by default
    expect(toggle).toHaveTextContent(/hide place labels/i)

    fireEvent.click(toggle)

    expect(toggle).toHaveAttribute('aria-pressed', 'false')
    expect(toggle).toHaveTextContent(/show place labels/i)
  })
})
