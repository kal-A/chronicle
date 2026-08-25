import { useEffect, useMemo, useState } from 'react'
import { ATLANTIC_LABELS, ATLANTIC_VIEW } from './atlasGeography'
import { resolveAtlasDrawStages } from './atlasDrawStages'

type Position = [number, number]

type CoastlineGeometry =
  | { type: 'LineString'; coordinates: Position[] }
  | { type: 'MultiLineString'; coordinates: Position[][] }

type CoastlineCollection = {
  features: Array<{ geometry: CoastlineGeometry | null }>
}

function project([longitude, latitude]: Position): Position {
  const x =
    ((longitude - ATLANTIC_VIEW.west) / (ATLANTIC_VIEW.east - ATLANTIC_VIEW.west)) *
    ATLANTIC_VIEW.width
  const y =
    ((ATLANTIC_VIEW.north - latitude) / (ATLANTIC_VIEW.north - ATLANTIC_VIEW.south)) *
    ATLANTIC_VIEW.height
  return [x, y]
}

function lineToPath(line: Position[]): string {
  return line
    .map((position, index) => {
      const [x, y] = project(position)
      return `${index === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
}

function geometryToPaths(geometry: CoastlineGeometry | null): string[] {
  if (!geometry) return []
  if (geometry.type === 'LineString') return [lineToPath(geometry.coordinates)]
  return geometry.coordinates.map(lineToPath)
}

export function AtlanticAtlas({
  reveal = 0,
  drawProgress = 1,
}: {
  reveal?: number
  drawProgress?: number
}) {
  const [coastline, setCoastline] = useState<CoastlineCollection | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    void fetch('/maps/homepage/ne_50m_coastline.geojson', { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Coastline request failed: ${response.status}`)
        return response.json() as Promise<CoastlineCollection>
      })
      .then(setCoastline)
      .catch((error: unknown) => {
        if (!(error instanceof DOMException && error.name === 'AbortError')) {
          setCoastline(null)
        }
      })

    return () => controller.abort()
  }, [])

  const coastlinePaths = useMemo(
    () => coastline?.features.flatMap((feature) => geometryToPaths(feature.geometry)) ?? [],
    [coastline],
  )

  const drawStages = resolveAtlasDrawStages(drawProgress)
  const revealScale = (220 + Math.max(0, Math.min(1, reveal)) * 1540) / 1760

  return (
    <div className="atlas-field">
      <p className="sr-only">
        A modern-orientation physical coastline spans the North Atlantic and Caribbean. It is a
        geographic reference, not a claim about historical political boundaries.
      </p>
      <svg
        className="atlas-map"
        viewBox={`0 0 ${ATLANTIC_VIEW.width} ${ATLANTIC_VIEW.height}`}
        preserveAspectRatio="xMinYMid slice"
        aria-hidden="true"
      >
        <defs>
          <clipPath id="atlas-reveal-window">
            <rect
              className="atlas-reveal-window"
              x="-140"
              y="0"
              width="1760"
              height="900"
              style={{ transform: `scaleX(${revealScale})` }}
            />
          </clipPath>
          <filter id="atlas-soft-ink" x="-10%" y="-10%" width="120%" height="120%">
            <feGaussianBlur stdDeviation="0.7" />
          </filter>
        </defs>

        <g className="atlas-graticule" style={{ opacity: drawStages.graticule }}>
          {[-90, -75, -60, -45, -30, -15, 0, 15].map((longitude) => {
            const [x] = project([longitude, 0])
            return <line key={`longitude-${longitude}`} x1={x} y1="0" x2={x} y2="900" />
          })}
          {[0, 15, 30, 45, 60].map((latitude) => {
            const [, y] = project([0, latitude])
            return <line key={`latitude-${latitude}`} x1="0" y1={y} x2="1600" y2={y} />
          })}
        </g>

        <g
          className="atlas-coastline atlas-coastline--base"
          filter="url(#atlas-soft-ink)"
          style={{ opacity: drawStages.settledInk }}
        >
          {coastlinePaths.map((path, index) => (
            <path key={`base-${index}`} d={path} />
          ))}
        </g>

        <g className="atlas-coastline atlas-coastline--revealed" clipPath="url(#atlas-reveal-window)">
          {coastlinePaths.map((path, index) => (
            <path
              key={`revealed-${index}`}
              d={path}
              pathLength={1}
              style={{ strokeDashoffset: 1 - drawStages.coastline }}
            />
          ))}
        </g>

        <g className="atlas-physical-labels" style={{ opacity: drawStages.labels }}>
          {ATLANTIC_LABELS.map((label) => {
            const [x, y] = project([label.longitude, label.latitude])
            return (
              <text
                key={label.name}
                x={x}
                y={y}
                data-longitude={label.longitude}
                data-latitude={label.latitude}
              >
                {label.name}
              </text>
            )
          })}
        </g>
      </svg>

      <svg
        className="atlas-compass"
        viewBox="0 0 180 180"
        aria-hidden="true"
        style={{ opacity: drawStages.instruments * 0.42 }}
      >
        <circle cx="90" cy="90" r="67" />
        <circle cx="90" cy="90" r="52" />
        <path d="M90 17 100 80 163 90 100 100 90 163 80 100 17 90 80 80Z" />
        <path d="M90 43 95 85 137 90 95 95 90 137 85 95 43 90 85 85Z" />
      </svg>

      <p className="atlas-source-note" style={{ opacity: drawStages.instruments }}>
        Physical coastline · Natural Earth 1:50m · modern orientation
      </p>
    </div>
  )
}
