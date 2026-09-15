// Pure helpers for the generated map's TERRITORY layer (ADR-004 addendum, T4):
// turning grounded ControlState + sourced TerritoryGeometry records into the
// GeoJSON and legend model the GL layers render. Kept out of MapView.tsx so the
// component file only exports components (fast-refresh) and so this logic can be
// unit-tested under jsdom, where the WebGL canvas itself no-ops.
//
// The colour language (locked in the prototype): control = solid polity tint;
// influence = diagonal hatch; contested = two-colour stripe. The de jure/de facto
// `basis` refines control — occupied/administered territory is the controller's
// tint marked with an occupation hatch, so held-not-owned land never reads as a
// plain homeland.
import type { Feature, FeatureCollection, GeoJsonProperties, Geometry } from 'geojson'
import type { ControlState, TerritoryGeometry } from '../model/generatedInvestigation'
import type { HistoricalDate } from '../model/schema'

// Per-polity colours are assigned by first appearance, never by name — subject-agnostic.
export const TERRITORY_PALETTE = ['#d98cc4', '#e6b84c', '#7fb2e6', '#8fce7f', '#e8926f']

export function colorForIndex(index: number): string {
  return TERRITORY_PALETTE[index % TERRITORY_PALETTE.length]
}

/** Stable colour index per polity (order of first appearance across the states). */
export function polityColorIndex(controlStates: ControlState[]): Map<string, number> {
  const index = new Map<string, number>()
  for (const state of controlStates) {
    if (!index.has(state.polity)) index.set(state.polity, index.size)
  }
  return index
}

/** Signed year of a HistoricalDate: parses "…BC"/"…BCE" from the label first (ISO
 * dates can't express BC), else the ISO year. Returns null when neither yields one. */
export function historicalYear(date: HistoricalDate | undefined, bound: 'start' | 'end'): number | null {
  if (!date) return null
  const label = date.label ?? ''
  const bc = label.match(/(\d+)\s*(?:BC|BCE)\b/i)
  if (bc) return -Number(bc[1])
  const ce = label.match(/\b(\d{1,4})\s*(?:AD|CE)?\b/)
  const iso = bound === 'start' ? date.earliest : date.latest
  const isoYear = iso ? Number(iso.slice(0, 4)) : NaN
  if (!Number.isNaN(isoYear)) return isoYear
  return ce ? Number(ce[1]) : null
}

/** The control states in force at `year` — interval [validFrom, validTo] contains
 * it. `year == null` (no time cursor) returns them all. */
export function activeControlStates(controlStates: ControlState[], year: number | null): ControlState[] {
  if (year == null) return controlStates
  return controlStates.filter((state) => {
    const from = historicalYear(state.validFrom, 'start')
    const to = historicalYear(state.validTo, 'end')
    if (from == null || to == null) return true // undated interval: don't hide it
    return from <= year && year <= to
  })
}

export interface TerritoryProperties {
  id: string
  kind: ControlState['kind']
  basis?: ControlState['basis']
  polity: string
  polityName: string
  colorIndex: number
  /** contested only: the second claimant's colour index (for the stripe). */
  otherColorIndex?: number
  /** name of the fill-pattern GL image this feature needs (influence/contested). */
  pattern?: string
  attestedYear?: number
  sovereignPolity?: string
}

/** GL image name for a single-colour hatch (influence). */
export function hatchPatternName(colorIndex: number): string {
  return `terr-hatch-${colorIndex}`
}

/** GL image name for a two-colour stripe (contested); colours are ordered so a
 * pair maps to one image regardless of which claimant is listed first. */
export function stripePatternName(a: number, b: number): string {
  const [lo, hi] = a <= b ? [a, b] : [b, a]
  return `terr-stripe-${lo}-${hi}`
}

/** GL image name for the occupation overlay hatch (occupied/administered). */
export const OCCUPATION_PATTERN = 'terr-occupation'

type PolygonGeometry = { type: 'Polygon' | 'MultiPolygon'; coordinates: unknown }

/** Join active control states to their sourced geometry and split into the three
 * render bands. A state whose geometryRef doesn't resolve is dropped (never a
 * fabricated frontier). Contested bands pick a second colour from any *other*
 * control state on the same geometry, so the stripe blends the actual claimants. */
export function territoryFeatureCollections(
  controlStates: ControlState[],
  geometries: TerritoryGeometry[],
  year: number | null,
  colorIndex: Map<string, number>,
): { control: FeatureCollection; influence: FeatureCollection; contested: FeatureCollection } {
  const geometryById = new Map(geometries.map((geometry) => [geometry.id, geometry]))
  const active = activeControlStates(controlStates, year)

  const bands: Record<'control' | 'influence' | 'contested', Feature[]> = {
    control: [],
    influence: [],
    contested: [],
  }

  for (const state of active) {
    const geometry = geometryById.get(state.geometryRef)
    if (!geometry) continue // no sourced polygon -> not rendered
    const ci = colorIndex.get(state.polity) ?? 0
    const properties: TerritoryProperties = {
      id: state.id,
      kind: state.kind,
      basis: state.basis,
      polity: state.polity,
      polityName: state.polity,
      colorIndex: ci,
      attestedYear: geometry.attestedYear,
      sovereignPolity: state.sovereignPolity,
    }
    if (state.kind === 'influence') {
      properties.pattern = hatchPatternName(ci)
    } else if (state.kind === 'contested') {
      const other = active.find(
        (candidate) => candidate.geometryRef === state.geometryRef && candidate.polity !== state.polity,
      )
      const otherCi = other ? (colorIndex.get(other.polity) ?? 0) : ci
      properties.otherColorIndex = otherCi
      properties.pattern = stripePatternName(ci, otherCi)
    }
    const feature: Feature = {
      type: 'Feature',
      properties: properties as unknown as GeoJsonProperties,
      geometry: { type: (geometry as PolygonGeometry).type, coordinates: (geometry as PolygonGeometry).coordinates } as Geometry,
    }
    const band = state.kind === 'controlled' ? 'control' : state.kind
    bands[band].push(feature)
  }

  return {
    control: { type: 'FeatureCollection', features: bands.control },
    influence: { type: 'FeatureCollection', features: bands.influence },
    contested: { type: 'FeatureCollection', features: bands.contested },
  }
}

export interface LegendEntry {
  polity: string
  colorIndex: number
}

/** Polities present in the active states, for the docked legend rail. */
export function territoryLegend(
  controlStates: ControlState[],
  year: number | null,
  colorIndex: Map<string, number>,
): { polities: LegendEntry[]; hasControl: boolean; hasInfluence: boolean; hasContested: boolean } {
  const active = activeControlStates(controlStates, year)
  const polities: LegendEntry[] = []
  const seen = new Set<string>()
  for (const state of active) {
    if (seen.has(state.polity)) continue
    seen.add(state.polity)
    polities.push({ polity: state.polity, colorIndex: colorIndex.get(state.polity) ?? 0 })
  }
  return {
    polities,
    hasControl: active.some((s) => s.kind === 'controlled'),
    hasInfluence: active.some((s) => s.kind === 'influence'),
    hasContested: active.some((s) => s.kind === 'contested'),
  }
}
