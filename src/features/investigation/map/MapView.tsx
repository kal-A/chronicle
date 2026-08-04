import { useEffect, useRef } from 'react'
import type { Map as MapLibreMap, Marker } from 'maplibre-gl'
import type { Scene, PlaceEntity } from '../model/schema'
import type { FocusValue } from '../model/focus'

/**
 * When a scene ships a `mapLayer` (docs/research/scene-2-map-source.md
 * documents the Scene 2 source), this renders a real, pannable/zoomable
 * MapLibre map with that period-accurate image as its only basemap layer —
 * never a live modern-tile provider, so political geography is exactly what
 * the cited historical plate shows, not implied by a "border-suppressed"
 * style choice (docs/architecture/spatial-architecture.md). No network tile
 * fetch is involved; the image ships as a bundled app asset.
 *
 * Scenes without a curated `mapLayer` fall back to the schematic orientation
 * diagram below — a real map is a researched asset per scene/theatre (like a
 * Source), not something to fabricate a background for.
 *
 * The accessible location list is the first-class interaction in both cases,
 * not a hidden fallback (docs/design/accessibility.md) — canvas rendering is
 * a progressive enhancement that no-ops gracefully under jsdom/no-WebGL.
 */
export function MapView({
  scene,
  focus,
  onSelectFocus,
}: {
  scene: Scene
  focus: FocusValue
  onSelectFocus: (focus: FocusValue) => void
}) {
  const places = scene.entities.filter(
    (e): e is PlaceEntity => e.entityType === 'place',
  )

  return (
    <div className="flex flex-col gap-3">
      {scene.mapLayer ? (
        <HistoricalMap
          scene={scene}
          places={places}
          focus={focus}
          onSelectFocus={onSelectFocus}
        />
      ) : (
        <SchematicMap places={places} focus={focus} />
      )}

      <nav aria-label="Locations active in this scene">
        <ul className="flex flex-col gap-1">
          {places.map((place) => {
            const isFocused =
              focus.kind === 'entity' &&
              focus.entityId === place.id &&
              focus.entityType === 'place'
            const period = place.periodRecords[0]
            return (
              <li key={place.id}>
                <button
                  type="button"
                  aria-current={isFocused ? 'true' : undefined}
                  className={`w-full rounded-lg border p-2 text-left text-sm transition-colors ${
                    isFocused
                      ? 'border-blue-600 border-l-4 bg-blue-50 font-semibold dark:bg-blue-950/40'
                      : 'border-neutral-200 hover:bg-neutral-50 dark:border-neutral-800 dark:hover:bg-neutral-900'
                  }`}
                  onClick={() =>
                    onSelectFocus({
                      kind: 'entity',
                      entityId: place.id,
                      entityType: 'place',
                    })
                  }
                >
                  {place.canonicalName}
                  <span className="ml-2 text-xs font-normal text-neutral-500 dark:text-neutral-400">
                    city precision · {period?.controllingPolity}, {period?.periodLabel}
                  </span>
                </button>
              </li>
            )
          })}
        </ul>
      </nav>
    </div>
  )
}

function HistoricalMap({
  scene,
  places,
  focus,
  onSelectFocus,
}: {
  scene: Scene
  places: PlaceEntity[]
  focus: FocusValue
  onSelectFocus: (focus: FocusValue) => void
}) {
  const placesRef = useRef(places)
  placesRef.current = places
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MapLibreMap | null>(null)
  const markersRef = useRef<Map<string, Marker>>(new Map())
  const onSelectFocusRef = useRef(onSelectFocus)
  onSelectFocusRef.current = onSelectFocus

  useEffect(() => {
    let cancelled = false
    let localMap: MapLibreMap | null = null
    const localMarkers = new Map<string, Marker>()
    markersRef.current = localMarkers
    const mapLayer = scene.mapLayer
    if (!mapLayer) return

    async function init() {
      if (!containerRef.current || !mapLayer) return
      try {
        const maplibregl = await import('maplibre-gl')
        await import('maplibre-gl/dist/maplibre-gl.css')
        if (cancelled || !containerRef.current) return

        const { topLeft, topRight, bottomRight, bottomLeft } = mapLayer.bounds

        const map = new maplibregl.Map({
          container: containerRef.current,
          style: {
            version: 8,
            sources: {
              'period-basemap': {
                type: 'image',
                url: mapLayer.imagePath,
                coordinates: [
                  [topLeft.lng, topLeft.lat],
                  [topRight.lng, topRight.lat],
                  [bottomRight.lng, bottomRight.lat],
                  [bottomLeft.lng, bottomLeft.lat],
                ],
              },
            },
            layers: [
              {
                id: 'period-basemap-layer',
                type: 'raster',
                source: 'period-basemap',
                paint: { 'raster-fade-duration': 0 },
              },
            ],
          },
          center: [mapLayer.defaultView.center.lng, mapLayer.defaultView.center.lat],
          zoom: mapLayer.defaultView.zoom,
          attributionControl: false,
        })
        localMap = map
        mapRef.current = map

        // The whole map is aria-hidden (below) since it's a progressive
        // enhancement over the accessible location list, not the primary
        // interaction. MapLibre's canvas is focusable (tabindex="0") by
        // default regardless — force it out of the tab order so nothing
        // focusable is left inside an aria-hidden subtree. Mouse-based
        // drag/scroll-zoom still work; no on-screen zoom control is added,
        // since that would reintroduce the same problem via its buttons.
        map.getCanvas().setAttribute('tabindex', '-1')

        for (const place of placesRef.current) {
          if (!place.coordinates) continue
          // A plain div, not a button: this marker is a decorative,
          // progressive-enhancement duplicate of the accessible location
          // list below, which is the real interaction target. MapLibre's
          // Marker.addTo() stamps role="button" onto its element unless one
          // is already present, which would fail axe's
          // nested-interactive-control check inside the role="img"
          // container even with aria-hidden — pre-setting role="presentation"
          // heads that off.
          const el = document.createElement('div')
          el.setAttribute('role', 'presentation')
          el.setAttribute('aria-hidden', 'true')
          el.className =
            'h-4 w-4 rounded-full border-2 border-white shadow cursor-pointer bg-neutral-700'
          el.addEventListener('click', () =>
            onSelectFocusRef.current({ kind: 'entity', entityId: place.id, entityType: 'place' }),
          )
          const marker = new maplibregl.Marker({ element: el })
            .setLngLat([place.coordinates.lng, place.coordinates.lat])
            .addTo(map)
          localMarkers.set(place.id, marker)
        }
      } catch {
        // Canvas/WebGL rendering is a progressive enhancement only — jsdom
        // (tests) and any environment without WebGL support fall back
        // gracefully to the accessible list, which is the first-class
        // interaction.
      }
    }

    void init()
    return () => {
      cancelled = true
      for (const marker of localMarkers.values()) marker.remove()
      localMarkers.clear()
      localMap?.remove()
    }
  }, [scene])

  useEffect(() => {
    for (const [placeId, marker] of markersRef.current) {
      const isFocused =
        focus.kind === 'entity' && focus.entityId === placeId && focus.entityType === 'place'
      const el = marker.getElement()
      el.className = `h-4 w-4 rounded-full border-2 border-white shadow cursor-pointer ${
        isFocused ? 'bg-blue-600 scale-125' : 'bg-neutral-700'
      }`
    }
  }, [focus])

  return (
    <div className="flex flex-col gap-1">
      {/* Progressive enhancement, not the first-class interaction (like
          GraphView's canvas) — its real pan/zoom controls can't coexist
          with an img/image role, so it's removed from the accessibility
          tree entirely; the location list below is what assistive tech
          and keyboard users rely on. */}
      <div
        ref={containerRef}
        aria-hidden="true"
        className="h-72 w-full overflow-hidden rounded-lg border border-neutral-200 bg-neutral-100 dark:border-neutral-800 dark:bg-neutral-900"
      />
      {scene.mapLayer && (
        <p className="text-[11px] text-neutral-500 dark:text-neutral-400">
          {scene.mapLayer.periodLabel} — {scene.mapLayer.sourceCitation} (
          {scene.mapLayer.attribution}, {scene.mapLayer.license})
        </p>
      )}
    </div>
  )
}

/**
 * Fallback for scenes without a curated `mapLayer` yet — the original
 * border-suppressed local schematic. A dashed connecting line stands in for
 * "communication happened between these two places," not a real route.
 */
function SchematicMap({
  places,
  focus,
}: {
  places: PlaceEntity[]
  focus: FocusValue
}) {
  const hasTwoPlaces = places.length === 2

  return (
    <svg
      role="img"
      aria-label="Schematic orientation map (no period-accurate basemap curated for this scene yet)"
      viewBox="0 0 240 140"
      className="w-full rounded-lg border border-neutral-200 bg-gradient-to-b from-neutral-50 to-neutral-100 dark:border-neutral-800 dark:from-neutral-950 dark:to-neutral-900"
    >
      {hasTwoPlaces && (
        <>
          <line
            x1={60}
            y1={70}
            x2={180}
            y2={70}
            className="stroke-amber-500 dark:stroke-amber-600"
            strokeWidth={2}
            strokeDasharray="6 5"
          />
          <text
            x={120}
            y={58}
            textAnchor="middle"
            className="fill-neutral-500 text-[9px] dark:fill-neutral-400"
          >
            diplomatic communication
          </text>
        </>
      )}
      {places.map((place, index) => {
        const x = 60 + index * 120
        const isFocused =
          focus.kind === 'entity' &&
          focus.entityId === place.id &&
          focus.entityType === 'place'
        return (
          <g key={place.id}>
            <circle
              cx={x}
              cy={70}
              r={isFocused ? 11 : 9}
              className={
                isFocused ? 'fill-blue-600' : 'fill-neutral-600 dark:fill-neutral-400'
              }
            />
            {isFocused && (
              <circle
                cx={x}
                cy={70}
                r={16}
                className="fill-none stroke-blue-600"
                strokeWidth={1.5}
              />
            )}
            <text
              x={x}
              y={95}
              textAnchor="middle"
              className="fill-neutral-900 text-[13px] font-semibold dark:fill-neutral-100"
            >
              {place.canonicalName}
            </text>
          </g>
        )
      })}
    </svg>
  )
}
