# Generated-map physical basemap source

The generated map (`src/features/investigation/map/MapView.tsx`, `GeneratedMap`)
draws its located places over a **bundled neutral physical basemap**, not a live
tile provider and not a found raster plate. This documents that basemap's source
and the historicity reasoning, in the same spirit as
`docs/research/scene-2-map-source.md`.

## Source

- **Dataset:** Natural Earth, 1:110m physical vectors.
- **Files (in `public/basemap/`):**
  - `ne_110m_land.geojson` — land polygons (rendered as land fill + a coastline
    stroke of the polygon outline).
  - `ne_110m_lakes.geojson` — lakes (rendered as water, same colour as ocean).
  - `ne_110m_rivers_lake_centerlines.geojson` — major river centrelines.
- **Retrieved from:** the official Natural Earth vector repository,
  `https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/`
  (the canonical GeoJSON conversion of the Natural Earth shapefiles).
- **Licence:** Public domain. Natural Earth places no restrictions on use and
  requires no attribution ("no permission is needed to use Natural Earth. Crediting
  the authors is unnecessary"). We credit it anyway in the map's provenance note.

## Why physical, 1:110m, no borders

- **Historicity.** The basemap carries **no political borders or place labels** —
  only physical geography (coastlines, rivers, lakes), which is period-stable over
  the centuries Chronicle investigates. It therefore never asserts a modern or
  anachronistic boundary. This satisfies the hard requirement that the map be
  accurate to the event's period rather than to a modern political basemap
  (`docs/architecture/geographic-and-map-generation.md`: "Rendering cannot exceed
  the evidence's precision").
- **Offline / free.** The GeoJSON is served from the app itself (`public/`), so the
  map needs no network and no external tile provider — consistent with the
  frontend's existing no-live-tile-provider stance and the free-development
  constraint (`AGENTS.md` §5).
- **1:110m.** Chosen for size (~213 KB for all three files combined) and because it
  reads clearly as a map at regional/continental zoom. It is deliberately coarse at
  single-city zoom, so the map's `fitBounds` clamps zoom-in (`maxZoom: 6`) — a lone
  located place lands on a regional frame rather than a blocky close-up, which is
  honest to the basemap's precision.

## Deferred (later slice)

Period-accurate boundaries and place-names at city zoom come from an
OpenHistoricalMap date-filtered layer that composes into this same MapLibre canvas
on top of the physical basemap, scoped to the investigation's viewport and date.
A higher-resolution physical set (1:50m) is an option if closer offline detail is
wanted before then.
