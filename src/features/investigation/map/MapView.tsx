import { useEffect, useRef, useState } from 'react'
import type {
  ExpressionSpecification,
  GeoJSONSource,
  Map as MapLibreMap,
  Marker,
  Popup,
} from 'maplibre-gl'
import type { EventRecord, Scene, PlaceEntity } from '../model/schema'
import type { FocusValue } from '../model/focus'
import { formatHistoricalDate } from '../model/formatHistoricalDate'

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
  placeIds,
  eventIds,
}: {
  scene: Scene
  focus: FocusValue
  onSelectFocus: (focus: FocusValue) => void
  /** Phase D workspace: restrict to the active lens's visible places. Omitted (Inspector) shows every place in the scene, unchanged. */
  placeIds?: Set<string>
  /** Workspace-only temporal window. Events after the selected moment are withheld from the map. */
  eventIds?: Set<string>
}) {
  const places = scene.entities.filter(
    (e): e is PlaceEntity =>
      e.entityType === 'place' && (!placeIds || placeIds.has(e.id)),
  )
  const visibleEvents = scene.events.filter((event) => !eventIds || eventIds.has(event.id))
  const isTemporalWorkspace = eventIds !== undefined
  const hasCoordinates = places.some((place) => place.coordinates)

  return (
    <div className="chronicle-map-view">
      {scene.mapLayer ? (
        <HistoricalMap
          scene={scene}
          places={places}
          focus={focus}
          onSelectFocus={onSelectFocus}
          visibleEvents={visibleEvents}
          isTemporalWorkspace={isTemporalWorkspace}
        />
      ) : hasCoordinates ? (
        <GeneratedMap places={places} focus={focus} visibleEvents={visibleEvents} />
      ) : (
        <SchematicMap places={places} focus={focus} visibleEvents={visibleEvents} />
      )}

      <nav className="chronicle-location-index" aria-label="Locations active in this scene">
        <p aria-hidden="true">
          Locations in this frame · {visibleEvents.length} event{visibleEvents.length === 1 ? '' : 's'} visible
        </p>
        <ul>
          {places.map((place) => {
            const placeEvents = visibleEvents.filter((event) => event.placeId === place.id)
            const isFocused =
              (focus.kind === 'entity' &&
                focus.entityId === place.id &&
                focus.entityType === 'place') ||
              (focus.kind === 'event' &&
                placeEvents.some((event) => event.id === focus.eventId))
            const period = place.periodRecords[0]
            return (
              <li key={place.id}>
                <button
                  type="button"
                  aria-current={isFocused ? 'true' : undefined}
                  className={`chronicle-location ${isFocused ? 'is-focused' : ''}`}
                  onClick={() =>
                    onSelectFocus({
                      kind: 'entity',
                      entityId: place.id,
                      entityType: 'place',
                    })
                  }
                >
                  {place.canonicalName}
                  <span>
                    {isTemporalWorkspace
                      ? `${placeEvents.length} visible event${placeEvents.length === 1 ? '' : 's'} · ${period?.nameAtTime}`
                      : `city precision · ${period?.controllingPolity}, ${period?.periodLabel}`}
                  </span>
                </button>
                {isTemporalWorkspace && placeEvents.length > 0 ? (
                  <ol className="chronicle-location-events">
                    {placeEvents.map((event) => (
                      <li key={event.id}>
                        <button
                          type="button"
                          aria-current={focus.kind === 'event' && focus.eventId === event.id ? 'true' : undefined}
                          onClick={() => onSelectFocus({ kind: 'event', eventId: event.id })}
                        >
                          <span>{formatHistoricalDate(event.eventTime)}</span>
                          {event.title}
                        </button>
                      </li>
                    ))}
                  </ol>
                ) : null}
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
  visibleEvents,
  isTemporalWorkspace,
}: {
  scene: Scene
  places: PlaceEntity[]
  focus: FocusValue
  onSelectFocus: (focus: FocusValue) => void
  visibleEvents: EventRecord[]
  isTemporalWorkspace: boolean
}) {
  const placesRef = useRef(places)
  placesRef.current = places
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MapLibreMap | null>(null)
  const markersRef = useRef<Map<string, Marker>>(new Map())
  const onSelectFocusRef = useRef(onSelectFocus)
  onSelectFocusRef.current = onSelectFocus
  const visibleEventsRef = useRef(visibleEvents)
  visibleEventsRef.current = visibleEvents
  const temporalWorkspaceRef = useRef(isTemporalWorkspace)
  temporalWorkspaceRef.current = isTemporalWorkspace

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
                paint: {
                  'raster-fade-duration': 0,
                  'raster-opacity': 0.86,
                  'raster-saturation': -0.48,
                  'raster-contrast': 0.18,
                  'raster-brightness-min': 0.05,
                  'raster-brightness-max': 0.72,
                },
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
          el.className = 'chronicle-map-marker'
          const count = document.createElement('span')
          count.setAttribute('aria-hidden', 'true')
          el.append(count)
          el.addEventListener('click', () => {
            const placeEvents = visibleEventsRef.current.filter((event) => event.placeId === place.id)
            const latestEvent = placeEvents[placeEvents.length - 1]
            if (temporalWorkspaceRef.current && latestEvent) {
              onSelectFocusRef.current({ kind: 'event', eventId: latestEvent.id })
              return
            }
            onSelectFocusRef.current({ kind: 'entity', entityId: place.id, entityType: 'place' })
          })
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
    const activeEventPlaceId =
      focus.kind === 'event'
        ? places.find((place) =>
            visibleEvents.some(
              (event) => event.id === focus.eventId && event.placeId === place.id,
            ),
          )?.id
        : undefined

    for (const [placeId, marker] of markersRef.current) {
      const isFocused =
        (focus.kind === 'entity' && focus.entityId === placeId && focus.entityType === 'place') ||
        activeEventPlaceId === placeId
      const eventCount = visibleEvents.filter((event) => event.placeId === placeId).length
      const el = marker.getElement()
      el.className = `chronicle-map-marker ${isFocused ? 'is-focused' : ''} ${
        eventCount === 0 ? 'is-dormant' : ''
      }`
      const count = el.querySelector('span')
      if (count) count.textContent = eventCount > 0 ? String(eventCount) : ''
    }
  }, [focus, places, visibleEvents])

  return (
    <div className="chronicle-historical-map-frame">
      {/* Progressive enhancement, not the first-class interaction (like
          GraphView's canvas) — its real pan/zoom controls can't coexist
          with an img/image role, so it's removed from the accessibility
          tree entirely; the location list below is what assistive tech
          and keyboard users rely on. */}
      <div
        ref={containerRef}
        aria-hidden="true"
        className="chronicle-historical-map"
      />
      {scene.mapLayer && (
        <details className="chronicle-map-citation">
          <summary>Map provenance &amp; limitations</summary>
          <p>
            {scene.mapLayer.periodLabel} — {scene.mapLayer.sourceCitation} (
            {scene.mapLayer.attribution}, {scene.mapLayer.license})
          </p>
          <p>{scene.mapLayer.georeferencingNote}</p>
        </details>
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
  visibleEvents,
}: {
  places: PlaceEntity[]
  focus: FocusValue
  visibleEvents: EventRecord[]
}) {
  const hasTwoPlaces = places.length === 2

  return (
    <svg
      role="img"
      aria-label="Schematic orientation map (no period-accurate basemap curated for this scene yet)"
      viewBox="0 0 240 140"
      className="chronicle-schematic-map"
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
            className="fill-neutral-500 text-xs dark:fill-neutral-400"
          >
            diplomatic communication
          </text>
        </>
      )}
      {places.map((place, index) => {
        const x = 60 + index * 120
        const placeEvents = visibleEvents.filter((event) => event.placeId === place.id)
        const isFocused =
          (focus.kind === 'entity' &&
            focus.entityId === place.id &&
            focus.entityType === 'place') ||
          (focus.kind === 'event' && placeEvents.some((event) => event.id === focus.eventId))
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
              className="fill-neutral-900 text-sm font-semibold dark:fill-neutral-100"
            >
              {place.canonicalName}
            </text>
            {placeEvents.length > 0 ? (
              <text x={x} y={112} textAnchor="middle" className="chronicle-schematic-event-count">
                {placeEvents.length} event{placeEvents.length === 1 ? '' : 's'} visible
              </text>
            ) : null}
          </g>
        )
      })}
    </svg>
  )
}

// --- Generated map -----------------------------------------------------------
// A map BUILT from the investigation's own extracted coordinates, not a found
// raster plate. It is the SAME MapLibre GL canvas as HistoricalMap (pannable/
// zoomable, real lng/lat markers) so generated and curated investigations share
// one interaction model — the difference is the basemap: instead of a
// georeferenced raster image, a bundled neutral PHYSICAL basemap (Natural Earth
// 1:110m land / coastlines / rivers / lakes, public domain, served from the app)
// under a generated lat/lng graticule. No tiles, no network, and NO political
// borders or labels — only period-stable physical geography — so the map asserts
// only what the evidence locates and never implies period-inaccurate borders
// (docs/architecture/geographic-and-map-generation.md: "Rendering cannot exceed
// the evidence's precision"; period-accurate boundaries/place-names are the
// later OpenHistoricalMap slice, which layers into this same canvas). Like
// HistoricalMap the WebGL canvas is an aria-hidden progressive enhancement that
// no-ops under jsdom/no-WebGL; the accessible location list below stays the
// first-class interaction.

const _MIN_SPAN_DEG = 1.2 // a single point (or coincident points) still gets a readable frame
// Bundled Natural Earth physical layers, served from the app itself (public/).
const BASEMAP_BASE = `${import.meta.env.BASE_URL}basemap`

/** A "nice" 1/2/5×10ⁿ graticule step giving ~`target` gridlines across `span`. */
function niceStep(span: number, target = 4): number {
  const raw = Math.max(span, 1e-6) / Math.max(target, 1)
  const mag = Math.pow(10, Math.floor(Math.log10(raw)))
  const norm = raw / mag
  const step = norm >= 5 ? 5 : norm >= 2 ? 2 : 1
  return step * mag
}

function gridlines(min: number, max: number, step: number): number[] {
  const lines: number[] = []
  const start = Math.ceil(min / step) * step
  for (let v = start; v <= max + 1e-9; v += step) {
    lines.push(Math.round(v / step) * step) // kill FP drift so labels read cleanly
  }
  return lines
}

interface Bounds {
  minLat: number
  maxLat: number
  minLng: number
  maxLng: number
}

/** Padded bounding box of the located places (a single point still frames). */
function boundsOf(located: { coordinates: { lat: number; lng: number } }[]): Bounds {
  const lats = located.map((p) => p.coordinates.lat)
  const lngs = located.map((p) => p.coordinates.lng)
  const padLat = Math.max((Math.max(...lats) - Math.min(...lats)) * 0.25, _MIN_SPAN_DEG / 2)
  const padLng = Math.max((Math.max(...lngs) - Math.min(...lngs)) * 0.25, _MIN_SPAN_DEG / 2)
  return {
    minLat: Math.min(...lats) - padLat,
    maxLat: Math.max(...lats) + padLat,
    minLng: Math.min(...lngs) - padLng,
    maxLng: Math.max(...lngs) + padLng,
  }
}

/** Meridian/parallel LineStrings across the bounds — the whole generated basemap. */
function graticuleGeoJSON(b: Bounds) {
  const features: {
    type: 'Feature'
    properties: Record<string, never>
    geometry: { type: 'LineString'; coordinates: [number, number][] }
  }[] = []
  for (const lng of gridlines(b.minLng, b.maxLng, niceStep(b.maxLng - b.minLng))) {
    features.push({
      type: 'Feature',
      properties: {},
      geometry: {
        type: 'LineString',
        coordinates: [
          [lng, b.minLat],
          [lng, b.maxLat],
        ],
      },
    })
  }
  for (const lat of gridlines(b.minLat, b.maxLat, niceStep(b.maxLat - b.minLat))) {
    features.push({
      type: 'Feature',
      properties: {},
      geometry: {
        type: 'LineString',
        coordinates: [
          [b.minLng, lat],
          [b.maxLng, lat],
        ],
      },
    })
  }
  return { type: 'FeatureCollection' as const, features }
}

type LocatedPlace = PlaceEntity & { coordinates: { lat: number; lng: number } }

/** The place currently in focus (selected place, or the place of a focused event). */
function focusedPlaceId(
  located: LocatedPlace[],
  focus: FocusValue,
  visibleEvents: EventRecord[],
): string | undefined {
  if (focus.kind === 'entity' && focus.entityType === 'place') return focus.entityId
  if (focus.kind === 'event') {
    return located.find((place) =>
      visibleEvents.some((event) => event.id === focus.eventId && event.placeId === place.id),
    )?.id
  }
  return undefined
}

/** Located places as a GeoJSON point layer — rendered ON the GL canvas (same
 * pass as the basemap, so points stay welded to the geography) and carrying each
 * place's LocationPrecision so the marker can size its uncertainty honestly. */
function placesToGeoJSON(located: LocatedPlace[], focusedId: string | undefined) {
  return {
    type: 'FeatureCollection' as const,
    features: located.map((place) => ({
      type: 'Feature' as const,
      properties: {
        id: place.id,
        name: place.canonicalName,
        // periodRecords is min-length 1 (contract); default defensively anyway.
        precision: place.periodRecords[0]?.precision ?? 'approximate',
        focused: place.id === focusedId,
      },
      geometry: {
        type: 'Point' as const,
        coordinates: [place.coordinates.lng, place.coordinates.lat] as [number, number],
      },
    })),
  }
}

// Uncertainty-disc radius (screen px) by evidence precision: coarser location →
// larger, softer halo, so the marker never implies more spatial precision than
// the evidence supports ("Rendering cannot exceed the evidence's precision").
const _PRECISION_RADIUS: ExpressionSpecification = [
  'match',
  ['get', 'precision'],
  'building',
  4,
  'city',
  8,
  'region',
  14,
  'approximate',
  20,
  12,
]

function GeneratedMap({
  places,
  focus,
  visibleEvents,
}: {
  places: PlaceEntity[]
  focus: FocusValue
  visibleEvents: EventRecord[]
}) {
  const located = places.filter(
    (place): place is PlaceEntity & { coordinates: { lat: number; lng: number } } =>
      place.coordinates != null,
  )
  const [labelsOn, setLabelsOn] = useState(true)
  const locatedRef = useRef(located)
  locatedRef.current = located
  const focusRef = useRef(focus)
  focusRef.current = focus
  const visibleEventsRef = useRef(visibleEvents)
  visibleEventsRef.current = visibleEvents
  const labelsOnRef = useRef(labelsOn)
  labelsOnRef.current = labelsOn
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MapLibreMap | null>(null)

  useEffect(() => {
    let cancelled = false
    let localMap: MapLibreMap | null = null
    let localPopup: Popup | null = null
    const current = locatedRef.current
    if (current.length === 0) return

    async function init() {
      if (!containerRef.current) return
      try {
        const maplibregl = await import('maplibre-gl')
        await import('maplibre-gl/dist/maplibre-gl.css')
        if (cancelled || !containerRef.current) return

        const bounds = boundsOf(current)
        const map = new maplibregl.Map({
          container: containerRef.current,
          style: {
            version: 8,
            // Bundled OFL font glyphs (Noto Sans, in public/basemap/fonts/) power
            // the on-map name labels. Like the basemap they are served from the
            // app — no external font/tile fetch.
            glyphs: `${BASEMAP_BASE}/fonts/{fontstack}/{range}.pbf`,
            // Basemap = a bundled neutral PHYSICAL layer (Natural Earth 1:110m
            // land / rivers / lakes, public domain) + a generated graticule. No
            // tiles, no political borders: only period-stable physical geography,
            // all served from the app itself, so nothing external is fetched.
            sources: {
              land: { type: 'geojson', data: `${BASEMAP_BASE}/ne_110m_land.geojson` },
              lakes: { type: 'geojson', data: `${BASEMAP_BASE}/ne_110m_lakes.geojson` },
              rivers: {
                type: 'geojson',
                data: `${BASEMAP_BASE}/ne_110m_rivers_lake_centerlines.geojson`,
              },
              graticule: { type: 'geojson', data: graticuleGeoJSON(bounds) },
              // Located places are DATA on the GL canvas, not DOM overlays: a
              // circle layer in the same render pass as the basemap stays exactly
              // registered to the geography (no pan/zoom drift) and scales.
              places: {
                type: 'geojson',
                data: placesToGeoJSON(
                  current,
                  focusedPlaceId(current, focusRef.current, visibleEventsRef.current),
                ),
              },
            },
            layers: [
              { id: 'ocean', type: 'background', paint: { 'background-color': '#0b2231' } },
              { id: 'land', type: 'fill', source: 'land', paint: { 'fill-color': '#17313d' } },
              {
                id: 'coastline',
                type: 'line',
                source: 'land',
                paint: { 'line-color': 'rgba(155,198,207,0.55)', 'line-width': 0.7 },
              },
              { id: 'lakes', type: 'fill', source: 'lakes', paint: { 'fill-color': '#0b2231' } },
              {
                id: 'rivers',
                type: 'line',
                source: 'rivers',
                paint: { 'line-color': 'rgba(102,170,190,0.5)', 'line-width': 0.5 },
              },
              {
                id: 'graticule-lines',
                type: 'line',
                source: 'graticule',
                paint: { 'line-color': 'rgba(155,198,207,0.12)', 'line-width': 0.5 },
              },
              {
                // Uncertainty halo, sized by the place's evidence precision.
                id: 'place-halo',
                type: 'circle',
                source: 'places',
                paint: {
                  'circle-radius': _PRECISION_RADIUS,
                  'circle-color': [
                    'case',
                    ['get', 'focused'],
                    'rgba(59,130,246,0.30)',
                    'rgba(155,198,207,0.16)',
                  ],
                },
              },
              {
                // Crisp centre dot marking the representative coordinate.
                id: 'place-core',
                type: 'circle',
                source: 'places',
                paint: {
                  'circle-radius': 3.5,
                  'circle-color': ['case', ['get', 'focused'], '#3b82f6', '#e2e8f0'],
                  'circle-stroke-color': '#0b2231',
                  'circle-stroke-width': 1.2,
                },
              },
              {
                // On-map name labels. text-optional + collision (allow-overlap
                // off) means crowded labels drop out rather than overprint — a
                // natural "some labels off" at density, before the explicit toggle.
                id: 'place-labels',
                type: 'symbol',
                source: 'places',
                layout: {
                  'text-field': ['get', 'name'],
                  'text-font': ['NotoSans-Regular'],
                  'text-size': 11,
                  'text-anchor': 'left',
                  'text-offset': [0.8, 0],
                  'text-optional': true,
                  visibility: labelsOnRef.current ? 'visible' : 'none',
                },
                paint: {
                  'text-color': '#e9dec5',
                  'text-halo-color': '#0b2231',
                  'text-halo-width': 1.2,
                },
              },
            ],
          },
          attributionControl: false,
        })
        localMap = map
        mapRef.current = map
        map.getCanvas().setAttribute('tabindex', '-1') // keep the aria-hidden canvas out of tab order

        map.fitBounds(
          [
            [bounds.minLng, bounds.minLat],
            [bounds.maxLng, bounds.maxLat],
          ],
          // Cap zoom-in: 1:110m geography reads as a map at regional scale but
          // blocky if you zoom past it, so a single located place lands on a
          // regional frame rather than a coarse close-up (honest to the basemap
          // precision; period city detail is the later OHM slice).
          { padding: 28, maxZoom: 6, duration: 0 },
        )

        // A name label on hover — closeOnMove hides it during pan/zoom, so no
        // overlay drifts against the basemap. The accessible location list below
        // remains the first-class, always-available naming.
        const popup = new maplibregl.Popup({
          closeButton: false,
          closeOnMove: true,
          offset: 12,
          className: 'chronicle-generated-map-popup',
        })
        localPopup = popup
        map.on('mouseenter', 'place-core', (event) => {
          const feature = event.features?.[0]
          if (!feature || feature.geometry.type !== 'Point') return
          const [lng, lat] = feature.geometry.coordinates as [number, number]
          popup.setLngLat([lng, lat]).setText(String(feature.properties?.name ?? '')).addTo(map)
        })
        map.on('mouseleave', 'place-core', () => popup.remove())
      } catch {
        // WebGL is a progressive enhancement only; jsdom/no-WebGL falls back to
        // the accessible location list, which is the first-class interaction.
      }
    }

    void init()
    return () => {
      cancelled = true
      localPopup?.remove()
      localMap?.remove()
    }
  }, [places])

  // Focus changes only rewrite the point source's data — no map rebuild, and the
  // points stay on the GL canvas (no drift).
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const source = map.getSource('places') as GeoJSONSource | undefined
    if (!source || typeof source.setData !== 'function') return
    source.setData(placesToGeoJSON(located, focusedPlaceId(located, focus, visibleEvents)))
  }, [focus, located, visibleEvents])

  // Toggle the label layer's visibility. If the style isn't ready yet, init reads
  // labelsOnRef so the layer lands in the right state on load.
  useEffect(() => {
    const map = mapRef.current
    try {
      if (map?.getLayer('place-labels')) {
        map.setLayoutProperty('place-labels', 'visibility', labelsOn ? 'visible' : 'none')
      }
    } catch {
      /* style not ready */
    }
  }, [labelsOn])

  return (
    <div className="chronicle-generated-map-frame">
      <div className="chronicle-generated-map-toolbar">
        <button
          type="button"
          className="chronicle-map-toggle"
          aria-pressed={labelsOn}
          onClick={() => setLabelsOn((on) => !on)}
        >
          {labelsOn ? 'Hide place labels' : 'Show place labels'}
        </button>
      </div>
      <div ref={containerRef} aria-hidden="true" className="chronicle-generated-map" />
      <p className="chronicle-generated-map-note">
        Generated map — {located.length} located place{located.length === 1 ? '' : 's'} on a neutral
        physical basemap (Natural Earth coastlines &amp; rivers; no period-specific borders).
      </p>
    </div>
  )
}
