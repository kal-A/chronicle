# Scene 2 Map Source — "Europe at the Present Time" (Shepherd, 1911)

Documents the period-accurate basemap used by Scene 2's map facet, per `docs/architecture/spatial-architecture.md`'s requirement that geography be historical, not present-day, and Kamal's explicit direction (2026-08-03) that a scene's map show the political geography relevant to its event/theatre, not a modern basemap with borders suppressed. This is the first map sourced under that pattern; future scenes/investigations (e.g. Civil War Anaconda Plan, Haitian Revolution) source their own period-appropriate plate the same way and register it here-equivalent.

## Source

- **Plate:** "Europe at the Present Time," pp. 166–167.
- **Atlas:** William R. Shepherd, *Historical Atlas* (New York: Henry Holt and Company, 1911).
- **Digitized by:** Perry–Castañeda Library (PCL) Map Collection, University of Texas Libraries — `https://maps.lib.utexas.edu/maps/historical/shepherd/europe_1911.jpg`.
- **Rights:** Public domain (US publication, 1911; well past any copyright term). PCL states most of its scanned maps are public domain and freely usable.
- **Stored at:** `public/maps/july-crisis/shepherd-europe-1911.jpg` (bundled app asset — no runtime network fetch).

## Why this plate

Shows the German Empire, Austria-Hungary, Russia, France, and Italy with an explicit "Triple Alliance" / "Dual Alliance" legend — the exact alliance system Scene 2 concerns — and labels both Berlin and Vienna. Depicts political boundaries as they stood in 1911, which is what "period-accurate for July 1914" means for Germany and Austria-Hungary specifically (see gap below for where this stops being true).

## Georeferencing method (disclosed approximation)

The plate carries its own printed graticule (latitude/longitude gridlines at 5° intervals, visible along all four edges). Corner coordinates for `Scene.mapLayer.bounds` in `src/content/july-crisis/scene-2-blank-cheque.ts` were read directly off that printed graticule and fitted as a simple rectangle:

| Corner | Lat | Lng |
|---|---|---|
| Top-left | 72°N | 30°W |
| Top-right | 72°N | 75°E |
| Bottom-right | 33°N | 75°E |
| Bottom-left | 33°N | 30°W |

This is a rectangular approximation of the plate's actual (non-equirectangular) projection, not a survey-grade transform — the plate's true projection curves longitude lines slightly toward the poles, which this fit ignores. It is adequate for scene-level orientation, not for precise spatial analysis. Berlin (52.52°N, 13.405°E) and Vienna (48.2082°N, 16.3738°E) both fall well within the plate's least-distorted central region, so the approximation error at the markers themselves is small.

## Explicit Gap — do not silently resolve

**The Balkans/Ottoman boundaries shown on this plate predate the First and Second Balkan Wars (1912–13) and do not reflect the borders as they stood in July 1914.** Serbia's territory, in particular, changed substantially between this plate's 1911 boundaries and July 1914. Germany's and Austria-Hungary's own boundaries are unaffected (unchanged 1911→1914), which is all Scene 2's events (Berlin, Vienna) require — but displaying the full plate necessarily also shows the outdated Balkan/Ottoman region if a user pans there.

**Mitigation:** `Scene.mapLayer.defaultView` centers and zooms the map on Germany/Austria-Hungary by default, not the Balkans. The gap is disclosed here and in `Scene.mapLayer.georeferencingNote` rather than hidden; it is not fixed by re-drawing boundaries, which is out of scope for a Phase 1 prototype map.

## Status

Recorded here as `passages-extracted`-equivalent for a map asset: acquired, rights-cleared, and its limitations disclosed, but not independently reviewed. See `docs/research/validation-status.md`.
