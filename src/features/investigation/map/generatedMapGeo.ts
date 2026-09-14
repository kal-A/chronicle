import type { EventRecord, PlaceEntity } from '../model/schema'

/** A place that has a resolved coordinate — the only kind the generated map plots. */
export type LocatedPlace = PlaceEntity & { coordinates: { lat: number; lng: number } }

/** Located places as a GeoJSON point layer — rendered ON the GL canvas (same
 * pass as the basemap, so points stay welded to the geography) and carrying each
 * place's LocationPrecision so the marker can size its uncertainty honestly.
 *
 * Each place also carries its count of currently-visible events and an `active`
 * flag (≥1 visible event). This is how the generated map answers the single time
 * cursor: as the workspace's temporal rail narrows `visibleEvents`, places whose
 * events aren't in the window yet render dormant (faded, no halo) and light up
 * when the cursor reaches them — the same dormant/active treatment HistoricalMap
 * already gives its markers, so both maps respond to time identically.
 *
 * Lives in its own module (not MapView.tsx) so the component file only exports
 * components — sharing this pure builder from there breaks React fast-refresh. */
export function placesToGeoJSON(
  located: LocatedPlace[],
  focusedId: string | undefined,
  visibleEvents: EventRecord[],
) {
  return {
    type: 'FeatureCollection' as const,
    features: located.map((place) => {
      const eventCount = visibleEvents.filter((event) => event.placeId === place.id).length
      return {
        type: 'Feature' as const,
        properties: {
          id: place.id,
          name: place.canonicalName,
          // periodRecords is min-length 1 (contract); default defensively anyway.
          precision: place.periodRecords[0]?.precision ?? 'approximate',
          focused: place.id === focusedId,
          eventCount,
          active: eventCount > 0,
        },
        geometry: {
          type: 'Point' as const,
          coordinates: [place.coordinates.lng, place.coordinates.lat] as [number, number],
        },
      }
    }),
  }
}
