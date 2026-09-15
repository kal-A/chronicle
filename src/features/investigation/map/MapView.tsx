import { useEffect, useMemo, useRef, useState } from 'react'
import type { FeatureCollection } from 'geojson'
import type {
  ExpressionSpecification,
  GeoJSONSource,
  LayerSpecification,
  Map as MapLibreMap,
  Marker,
  Popup,
} from 'maplibre-gl'
import type { EventRecord, Scene, PlaceEntity } from '../model/schema'
import type { FocusValue } from '../model/focus'
import { formatHistoricalDate } from '../model/formatHistoricalDate'
import { placesToGeoJSON, type LocatedPlace } from './generatedMapGeo'
import type { ControlState, TerritoryGeometry } from '../model/generatedInvestigation'
import {
  OCCUPATION_PATTERN,
  TERRITORY_PALETTE,
  colorForIndex,
  hatchPatternName,
  polityColorIndex,
  stripePatternName,
  territoryFeatureCollections,
  territoryLegend,
} from './territory'

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
  controlStates,
  territoryGeometries,
  currentYear,
}: {
  scene: Scene
  focus: FocusValue
  onSelectFocus: (focus: FocusValue) => void
  /** Phase D workspace: restrict to the active lens's visible places. Omitted (Inspector) shows every place in the scene, unchanged. */
  placeIds?: Set<string>
  /** Workspace-only temporal window. Events after the selected moment are withheld from the map. */
  eventIds?: Set<string>
  /** Time-indexed territory (ADR-004), rendered on the generated map. */
  controlStates?: ControlState[]
  territoryGeometries?: TerritoryGeometry[]
  /** Signed year of the time cursor (for the territory layer). */
  currentYear?: number | null
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
        <GeneratedMap
          places={places}
          focus={focus}
          visibleEvents={visibleEvents}
          controlStates={controlStates}
          territoryGeometries={territoryGeometries}
          currentYear={currentYear}
        />
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

// --- Territory fill patterns (canvas -> GL images). Browser-only: canvas has no
// 2D context under jsdom, so these run only inside the map init, itself wrapped in
// the WebGL try/catch; they return null when no context is available. ---
type PatternImage = { width: number; height: number; data: Uint8Array } | null
function _diagonalHatch(
  color: string,
  { spacing = 7, width = 1.6, back = false }: { spacing?: number; width?: number; back?: boolean } = {},
): PatternImage {
  const size = 16
  const ratio = 2
  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = size * ratio
  const ctx = canvas.getContext('2d')
  if (!ctx) return null
  ctx.scale(ratio, ratio)
  ctx.strokeStyle = color
  ctx.lineWidth = width
  ctx.lineCap = 'round'
  ctx.beginPath()
  for (let i = -size; i < size * 2; i += spacing) {
    if (back) {
      ctx.moveTo(i, size)
      ctx.lineTo(i + size, 0)
    } else {
      ctx.moveTo(i, 0)
      ctx.lineTo(i + size, size)
    }
  }
  ctx.stroke()
  const image = ctx.getImageData(0, 0, size * ratio, size * ratio)
  return { width: size * ratio, height: size * ratio, data: new Uint8Array(image.data) }
}
function _twoColorStripe(colorA: string, colorB: string): PatternImage {
  const size = 14
  const ratio = 2
  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = size * ratio
  const ctx = canvas.getContext('2d')
  if (!ctx) return null
  ctx.scale(ratio, ratio)
  ctx.fillStyle = colorA
  ctx.fillRect(0, 0, size, size)
  ctx.strokeStyle = colorB
  ctx.lineWidth = size / 2.6
  ctx.beginPath()
  for (let i = -size; i < size * 2; i += size / 1.4) {
    ctx.moveTo(i, 0)
    ctx.lineTo(i + size, size)
  }
  ctx.stroke()
  const image = ctx.getImageData(0, 0, size * ratio, size * ratio)
  return { width: size * ratio, height: size * ratio, data: new Uint8Array(image.data) }
}

// Data-driven control fill colour, keyed off each feature's polity colour index.
const _TERRITORY_FILL_COLOR = [
  'match',
  ['get', 'colorIndex'],
  ...TERRITORY_PALETTE.flatMap((color, index) => [index, color]),
  TERRITORY_PALETTE[0],
] as unknown as ExpressionSpecification

/** Register the fill-pattern images the current territory features reference:
 * a hatch per influence colour, a stripe per contested colour-pair, and the shared
 * occupation overlay. Idempotent (skips images already added). */
function _registerTerritoryPatterns(
  map: MapLibreMap,
  collections: ReturnType<typeof territoryFeatureCollections>,
): void {
  const add = (name: string, image: PatternImage) => {
    if (image && !map.hasImage(name)) map.addImage(name, image, { pixelRatio: 2 })
  }
  for (const feature of collections.influence.features) {
    const index = Number((feature.properties as { colorIndex?: number })?.colorIndex ?? 0)
    add(hatchPatternName(index), _diagonalHatch(colorForIndex(index)))
  }
  for (const feature of collections.contested.features) {
    const props = feature.properties as { colorIndex?: number; otherColorIndex?: number }
    const a = Number(props?.colorIndex ?? 0)
    const b = Number(props?.otherColorIndex ?? a)
    add(stripePatternName(a, b), _twoColorStripe(colorForIndex(a), colorForIndex(b)))
  }
  add(OCCUPATION_PATTERN, _diagonalHatch('rgba(9,20,28,0.6)', { spacing: 5, width: 2.4, back: true }))
}

function GeneratedMap({
  places,
  focus,
  visibleEvents,
  controlStates,
  territoryGeometries,
  currentYear,
}: {
  places: PlaceEntity[]
  focus: FocusValue
  visibleEvents: EventRecord[]
  /** Time-indexed territory (ADR-004). Rendered when both are present. */
  controlStates?: ControlState[]
  territoryGeometries?: TerritoryGeometry[]
  /** Signed year of the time cursor; territory in force at this year renders. */
  currentYear?: number | null
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

  // Territory (ADR-004): the JOIN of control states + sourced geometry, filtered by
  // the time cursor. Colours are assigned per polity by first appearance.
  const territoryOn = (controlStates?.length ?? 0) > 0 && (territoryGeometries?.length ?? 0) > 0
  const colorIndex = useMemo(() => polityColorIndex(controlStates ?? []), [controlStates])
  const legend = useMemo(
    () => territoryLegend(controlStates ?? [], currentYear ?? null, colorIndex),
    [controlStates, currentYear, colorIndex],
  )
  const territoryRef = useRef({ controlStates, territoryGeometries, currentYear, colorIndex })
  territoryRef.current = { controlStates, territoryGeometries, currentYear, colorIndex }

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
                  visibleEventsRef.current,
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
                // Shown only for places active at the current time cursor (or the
                // focused one); dormant places drop their halo so scrubbing the
                // timeline visibly lights places up as their events arrive.
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
                  'circle-opacity': [
                    'case',
                    ['any', ['get', 'active'], ['get', 'focused']],
                    1,
                    0,
                  ],
                },
              },
              {
                // Crisp centre dot marking the representative coordinate. Dormant
                // places (no event visible yet at the cursor) render smaller, muted
                // and semi-transparent — present but clearly not-yet-in-play.
                id: 'place-core',
                type: 'circle',
                source: 'places',
                paint: {
                  'circle-radius': [
                    'case',
                    ['any', ['get', 'active'], ['get', 'focused']],
                    3.5,
                    2.5,
                  ],
                  'circle-color': [
                    'case',
                    ['get', 'focused'],
                    '#3b82f6',
                    ['get', 'active'],
                    '#e2e8f0',
                    '#7c8b95',
                  ],
                  'circle-opacity': [
                    'case',
                    ['any', ['get', 'active'], ['get', 'focused']],
                    1,
                    0.5,
                  ],
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
                  // Dim labels for places not yet in play at the cursor.
                  'text-opacity': ['case', ['any', ['get', 'active'], ['get', 'focused']], 1, 0.4],
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

        // Territory layers: control (solid polity tint), influence (hatch),
        // contested (two-colour stripe), plus an occupation overlay marking
        // de-facto-held (occupied/administered) land. Added UNDER the place markers
        // (before 'place-halo') so places stay on top. Always added — empty when
        // there is no territory — so the update effect below can just setData.
        const addTerritory = () => {
          const state = territoryRef.current
          const collections = territoryFeatureCollections(
            state.controlStates ?? [],
            state.territoryGeometries ?? [],
            state.currentYear ?? null,
            state.colorIndex,
          )
          _registerTerritoryPatterns(map, collections)
          map.addSource('territory-influence', { type: 'geojson', data: collections.influence })
          map.addSource('territory-control', { type: 'geojson', data: collections.control })
          map.addSource('territory-contested', { type: 'geojson', data: collections.contested })
          const before = 'place-halo'
          const layers: LayerSpecification[] = [
            { id: 'territory-influence-fill', type: 'fill', source: 'territory-influence',
              paint: { 'fill-pattern': ['get', 'pattern'], 'fill-opacity': 0.6 } },
            { id: 'territory-control-fill', type: 'fill', source: 'territory-control',
              paint: { 'fill-color': _TERRITORY_FILL_COLOR, 'fill-opacity': 0.45 } },
            { id: 'territory-control-line', type: 'line', source: 'territory-control',
              paint: { 'line-color': _TERRITORY_FILL_COLOR, 'line-width': 1.1, 'line-opacity': 0.85 } },
            { id: 'territory-occupation', type: 'fill', source: 'territory-control',
              filter: ['any', ['==', ['get', 'basis'], 'occupied'], ['==', ['get', 'basis'], 'administered']],
              paint: { 'fill-pattern': OCCUPATION_PATTERN, 'fill-opacity': 0.85 } },
            { id: 'territory-contested-fill', type: 'fill', source: 'territory-contested',
              paint: { 'fill-pattern': ['get', 'pattern'], 'fill-opacity': 0.9 } },
            { id: 'territory-contested-line', type: 'line', source: 'territory-contested',
              paint: { 'line-color': 'rgba(244,236,217,0.7)', 'line-width': 0.8, 'line-dasharray': [2, 2] } },
          ] as unknown as LayerSpecification[]
          for (const layer of layers) map.addLayer(layer, before)
        }
        if (map.isStyleLoaded()) addTerritory()
        else map.once('load', addTerritory)
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
      mapRef.current = null // don't leave a torn-down map behind for the effects below
    }
  }, [places])

  // Focus/time changes only rewrite the point source's data — no map rebuild, and
  // the points stay on the GL canvas (no drift). Guarded like the labels effect:
  // getSource throws if the style isn't loaded yet (or the map was just torn down
  // during a StrictMode remount) rather than returning undefined; on load, init
  // seeds the source with the current data, so skipping here is safe.
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    try {
      const source = map.getSource('places') as GeoJSONSource | undefined
      if (!source || typeof source.setData !== 'function') return
      source.setData(
        placesToGeoJSON(located, focusedPlaceId(located, focus, visibleEvents), visibleEvents),
      )
    } catch {
      /* style not ready / map torn down — init seeds the source on load */
    }
  }, [focus, located, visibleEvents])

  // Territory redraws when the time cursor or the data changes: register any new
  // fill patterns, then setData on the three territory sources. Guarded like the
  // places effect (getSource throws before the style/sources exist).
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    try {
      const collections = territoryFeatureCollections(
        controlStates ?? [],
        territoryGeometries ?? [],
        currentYear ?? null,
        colorIndex,
      )
      _registerTerritoryPatterns(map, collections)
      const set = (id: string, data: FeatureCollection) => {
        const source = map.getSource(id) as GeoJSONSource | undefined
        if (source && typeof source.setData === 'function') source.setData(data)
      }
      set('territory-influence', collections.influence)
      set('territory-control', collections.control)
      set('territory-contested', collections.contested)
    } catch {
      /* style/sources not ready — init seeds them on load */
    }
  }, [controlStates, territoryGeometries, currentYear, colorIndex])

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
        {territoryOn && (
          <div
            className="chronicle-territory-legend"
            role="group"
            aria-label="Territory legend"
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '4px 12px',
              alignItems: 'center',
              fontSize: '.72rem',
              color: '#9bc6cf',
              marginLeft: 12,
            }}
          >
            {legend.polities.map((entry) => (
              <span key={entry.polity} style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                <i
                  aria-hidden="true"
                  style={{
                    width: 14,
                    height: 10,
                    borderRadius: 2,
                    background: colorForIndex(entry.colorIndex),
                    display: 'inline-block',
                  }}
                />
                {entry.polity}
              </span>
            ))}
            {legend.hasControl && <span>· solid = control</span>}
            {legend.hasInfluence && <span>· hatch = influence</span>}
            {legend.hasContested && <span>· stripe = contested</span>}
          </div>
        )}
      </div>
      <div ref={containerRef} aria-hidden="true" className="chronicle-generated-map" />
      <p className="chronicle-generated-map-note">
        Generated map — {located.length} located place{located.length === 1 ? '' : 's'} on a neutral
        physical basemap (Natural Earth coastlines &amp; rivers; no period-specific borders).
      </p>
    </div>
  )
}
