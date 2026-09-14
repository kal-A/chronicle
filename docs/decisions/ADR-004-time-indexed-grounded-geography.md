# ADR-004: Time-Indexed, Grounded Geographic Model for the Generated Map

**Status:** Proposed

## Context

Slices 1–2 of the structured-extraction work (commits `f56514a`, `8a51a75`) gave
generated investigations a real, interactive map: the acquisition pipeline
extracts grounded, located events, and the workspace renders them as a MapLibre
GL circle layer over a bundled neutral physical basemap (Natural Earth), with
each marker's uncertainty sized by its `LocationPrecision`.

That map is a **locator** — "where did dated events happen." The product intent
(map-first historical investigation) needs it to be an **instrument** — a view of
the *geopolitical state* of the investigation and *how it changed over the event's
span*. Concretely, the map must eventually support:

1. **Labels** — place and polity names on the map itself, with the ability to
   turn classes of labels on/off.
2. **Territories** — areas of *control* and *influence* per polity (e.g., 2nd
   Punic War: Carthaginian vs. Roman control and spheres of influence), including
   *contested* areas — not just points.
3. **Change over time** — the investigation spans years (2nd Punic War, 218–201
   BC) or months (Franco-Prussian War, a trade crisis); the map state must evolve
   as the user scrubs a timeline tied to the event.
4. **Tandem with the LLM** — the map and the assistant share state, so the
   investigation drives the map and vice-versa.

The hard constraint is the one that governs the whole system: **historicity and
honesty**. A control/influence map is trivially easy to fabricate and trivially
easy to overstate. We must not invent geometry, assert modern borders as
historical, imply crisp frontiers where the sources are fuzzy, or show more
temporal precision than the evidence supports ("Rendering cannot exceed the
evidence's precision" — `docs/architecture/geographic-and-map-generation.md`).

## Decision

**Model the generated map as a JOIN of three separately-sourced responsibilities,
indexed by a single time cursor.** Each party does only what it can do honestly:

1. **The LLM extracts grounded who / what / when** — passage-grounded, PROPOSED,
   reviewable claims. This includes existing records (events with `eventTime`,
   places with `PlacePeriodRecord.controllingPolity`, relationships) plus a **new
   `ControlState` record**: `{ polity, kind: controlled | influence | contested,
   validFrom, validTo, geometryRef, precision, evidenceLinkIds }`. The LLM asserts
   *that* a polity controlled/influenced a named region during a time interval,
   citing passages. **The LLM never produces geometry.**

2. **Sourced datasets provide geometry (the "where")** — never the model:
   - **Points:** period-aware gazetteers (already: Wikidata + World Historical
     Gazetteer), returning a representative coordinate + precision.
   - **Areas:** historical-boundary datasets — OpenHistoricalMap (date-filtered,
     where covered) and/or a bundled public-domain historical-boundaries dataset
     (e.g. `historical-basemaps`, world polities at snapshot years). A
     `ControlState.geometryRef` resolves to a polygon *from a dataset*, tagged with
     the attested year it came from.
   - **Labels:** place/polity names from the same records, rendered as a GL
     `symbol` layer once font glyphs are bundled.

3. **A single `currentTime` cursor drives what renders** — the map at time *t* =
   { events at/through *t*, `ControlState`s whose interval contains *t*, labels }.
   Every time-aware layer filters against this one cursor (extending the workspace's
   existing `TemporalMapRail` / `timeVisibleEventIds`). Territory geometry steps to
   the nearest attested snapshot ≤ *t*, labeled "as of ~Y"; the gaps between
   snapshots are inference, shown as uncertainty, never as hard transitions.

**The map and the assistant share `currentTime` and `focus`**, making the map a
bidirectional control surface (scrub the timeline → the assistant can narrate that
moment; ask a question → it can move the map/time).

### Honesty guardrails (binding)

- Geometry is **only** ever from a sourced dataset or gazetteer, never LLM-drawn.
- Every control/influence assertion is a passage-grounded `ControlState` (has
  `evidenceLinkIds`), PROPOSED, reviewable — same discipline as any claim.
- `influence` and `contested` render **fuzzy** (faded / hatched / overlapping),
  because spheres of influence had no crisp lines; only `controlled` with a sourced
  boundary renders a firm edge.
- Where no period-accurate geometry exists for a region/era, render **nothing or an
  explicit approximation**, never a fabricated frontier. Coverage is uneven —
  antiquity (Punic War) is coarser than the 19th century — and the map says so.
- Temporal interpolation between attested snapshots is uncertainty and is shown as
  such ("as of ~Y").

## Consequences

- **Contract additions.** A `ControlState` record (grounded, time-valid, geometry
  by reference) and a time-aware map-layer model beyond today's raster
  `mapAssets`/`mapScenes`. These are additive and reviewable like every other
  generated record; existing packages stay valid without them.
- **New bundled/free data.** Font glyphs (for labels) and at least one
  historical-boundaries dataset, both offline/public-domain, consistent with the
  free-development constraint (`AGENTS.md` §5). OHM (networked) is an optional
  higher-fidelity layer with a later CSP decision.
- **Extraction pipeline.** Gains a geopolitical-state stage producing
  `ControlState` claims — an extension of the documented stages 9 (timeline), 10
  (relationships), 12 (geography), not a new spec direction.
- **Frontend.** Unifies on one `currentTime` cursor; the generated map becomes a
  set of time-filtered GL layers (physical basemap → territories → graticule →
  markers → labels); assistant/map share state.
- **Honesty surface grows.** More ways to overstate ⇒ the uncertainty rendering
  above is not optional polish; it is the feature that keeps the map truthful.

### Sequencing (each its own slice, smallest-complete-first)

1. **Labels** — bundle glyphs; `symbol` layer for place/polity names; a label
   on/off (and rank-based) toggle. Independent of the rest; ships first.
2. **One time cursor** — generalize the temporal rail so the generated map's
   existing event markers respond to a scrubbed `currentTime`.
3. **Territories (`ControlState`)** — the grounded control/influence record + a
   bundled historical-boundaries dataset + time-sliced fill rendering. The
   research-heavy slice; delivers the Carthage/Rome-style view.
4. **Deeper LLM tandem** — shared `currentTime`/`focus` between map and assistant.

## Alternatives Considered

- **Found raster period plates** (today's `mapAssets`). Rejected as the *primary*
  generated map: it is found-not-generated (contra ADR-002's map-first, generated
  direction), can't move with the timeline, and one plate can't represent an
  evolving multi-year event. Retained only for curated corpora that genuinely have
  a rights-cleared, period-fit plate.
- **LLM-drawn polygons** (ask the model for boundary geometry). Rejected: fabricated
  geography, the exact historicity failure this project exists to avoid.
- **Modern political vector tiles, border-suppressed.** Rejected: modern borders are
  anachronistic even when faded; physical + sourced-historical is the honest base.
- **A single static (non-temporal) territory map.** Rejected: it cannot show change
  over the event, which is the whole point — and it would imply a fixed geopolitical
  state that most investigated events do not have.

## Addendum

- [ADR-004 Addendum: Territory + Time-Cursor — Implementation Plan](ADR-004-addendum-territory-time-implementation.md)
  — the concrete build plan for sequencing steps 2–3 (one time cursor; territories),
  written after a throwaway visual prototype locked the coloration/interaction language.

## References

- `docs/architecture/geographic-and-map-generation.md`, `timeline-generation.md`,
  `source-to-narrative-enrichment.md`, `investigation-generation-pipeline.md`.
- ADR-002 (map-first workspace), ADR-003 (LLM-agent system is the product core).
- `docs/research/generated-map-basemap-source.md` (the Slice-2 physical basemap).
