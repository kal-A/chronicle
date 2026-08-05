# Spatial Architecture

## Principle

Geography in Chronicle is historical, not present-day. A `Place` entity is not a single point on a modern map — it's a canonical place with one or more `PlacePeriodRecord`s describing its name, political control, and administrative status across different historical periods (`docs/architecture/domain-model.md`). The map renders whichever period record applies to the current investigation's/scene's time range.

## Precision Model

Every geographic reference carries a precision tag: `building` / `city` / `region` / `approximate`. The map UI renders precision honestly — a `city`-precision event gets a city-level marker/area, never a building-level pin implied by false precision (`AGENTS.md` §12). Precision is set at data-entry/extraction time from what the source actually establishes, not inferred from having *a* coordinate available.

## Rendering Approach

MapLibre GL JS on the frontend. Base map layers are tagged with the historical period(s) they are valid for; a modern reference basemap may be shown as a subdued, explicitly labelled orientation layer. Period political boundaries are rendered only when sourced historical geometry exists. When it does not, Chronicle uses a neutral/border-suppressed base rather than substituting modern political borders (`historical-methodology.md`).

## MapScope (Phase D)

Starting Phase D, every investigation's map-first workspace opens to a bounded `MapScope` (`docs/product/map-first-workspace-instructions.md` §3, `docs/decisions/ADR-002-map-first-workspace.md`) — `bounds`, `focusRegions`, `contextRegions`, an `initialViewport`/zoom range, a `geographicRationale`, the `representedPeriod`, and disclosed `unavailableHistoricalBoundaries`/`geographicLimitations`. The map must never default to a whole-world view: it includes the locations required to understand the investigation plus enough surrounding geography for orientation, and excludes irrelevant global space. This is generated content on the `InvestigationExperiencePlan`, validated the same way every other package reference is (rule additions to `validateGeneratedInvestigation`/`validate_generated_investigation`), not client-computed from raw scene bounds — consistent with this document's existing precision/period-fit discipline, just applied one level up (workspace viewport, not just individual place markers).

## Scope for July Crisis (Phase 1–3)

The July Crisis spans a small number of capitals and specific sites over five weeks in 1914. Phase 1–3 does not require political polygons to test city-level movement between scenes. A small hand-curated set of period-accurate place records, correctly named and labelled for 1914, is sufficient; the map uses a border-suppressed orientation base. Complex historical or disputed-geography polygons are explicitly out of scope until an investigation requires them (`AGENTS.md` §12).

## PostGIS

Not adopted in Phase 2. Point/simple-area geography (lat/lng + precision tag, stored as plain columns or a lightweight `geography` column) is sufficient for the July Crisis scope. PostGIS is introduced only if a later investigation's spatial queries (e.g., "what changed hands within this disputed region over time") genuinely require it — a justified addition, not a default (`AGENTS.md` §5).

## Testing

Spatial rendering is covered by the frontend's Playwright journeys (map reflects current focus) and a backend contract test asserting place-period resolution picks the correct period record for a given investigation/scene time range.
