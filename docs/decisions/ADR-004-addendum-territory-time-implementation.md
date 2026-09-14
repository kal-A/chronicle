# ADR-004 Addendum: Territory + Time-Cursor — Implementation Plan

**Status:** Proposed — implementation plan for ADR-004 sequencing steps 2–3 (one time
cursor; territories). Does not change ADR-004's decision; it operationalizes it.

**Date:** 2026-09-13

## Why this addendum exists

ADR-004 fixed the *model* (map = a time-indexed join of LLM-grounded claims + sourced
geometry). Before touching the contract or the pipeline, we built a **throwaway visual
prototype** (a standalone harness, not production code) to lock the *visual and
interaction language* against real MapLibre GL rendering and against the user's
reference maps (a period Punic-War plate with hatched influence, Victoria 3, EU4). This
addendum records what that prototype settled and converts it into a concrete production
plan, so the expensive slices (contract, data, extraction) are executed against decisions
that are already validated on screen.

The prototype is a scratch artifact and is **not** part of the codebase; nothing here has
been committed to `src/` or `backend/`.

## What the prototype validated (now locked)

These are visual/interaction decisions; they do not depend on data source and carry into
production unchanged:

- **Coloration language.** `controlled` = solid polity tint (~0.5 fill) + thin crisp
  outline; `influence` = diagonal **hatch** in the polity color (+ a soft/blurred edge),
  never a flat blob; `contested` = two-color **stripe** blending the claimants.
- **Fluid, coastline-clipped fills.** Territory hugs the coast and never spills into the
  sea. In the prototype this was `turf.polygonSmooth` then intersect-with-land; in
  production the geometry comes pre-clean from a sourced boundary dataset (see below), so
  clipping is a fallback, not the main path.
- **Legend = docked rail *outside* the map geography** ("Style A"), never an in-map
  overlay — an overlay always covers some territory. The rail is generated from the data
  (polity swatches from a generic palette by index + control/influence/contested texture
  swatches).
- **One time cursor, discrete sourced snapshots, step-held.** Territory holds its last
  *sourced* extent until the next snapshot; we never morph-interpolate borders. Between
  keyframes the readout is explicit: "213 BC · as mapped 216 BC". This is the honesty
  rule made visible.
- **Subject-agnostic renderer.** It consumes a generic
  `{ polities, snapshots: [{ year, bands }] }` shape and colors polities by index; the
  same code drove a BC-era war and a synthetic CE-era 3-polity case with no event names.

## Prototype concept → production home

| Prototype (throwaway) | Production |
| --- | --- |
| hand-drawn `band.coordinates` | `ControlState.geometryRef` → polygon resolved from a sourced dataset |
| `snapshots: [{ year, bands }]` | `ControlState.validFrom/validTo` intervals; the cursor filters them |
| `turf` smooth + clip to land | usually unnecessary (sourced province geometry is already clean); kept only as a fallback |
| standalone renderer + slider | ported into `GeneratedMap` in `src/features/investigation/map/MapView.tsx`, driven by the workspace's single `currentTime` |
| generic palette by polity index | unchanged — stays index-based, never name-based |

## Contract additions (both stacks, in lockstep)

Backend `backend/src/chronicle/contracts/generated_investigation.py` and frontend
`src/features/investigation/model/generatedInvestigation.ts` (each has round-trip +
validation tests that must stay in parity):

- **`ControlState` record:** `{ id, polity, kind: controlled | influence | contested,
  basis?, sovereignPolity?, validFrom, validTo, geometryRef, precision, evidenceLinkIds,
  reviewStatus, visibility }`. Mirrors the discipline of every other generated record:
  PROPOSED, reviewable, passage-grounded. **Carries no geometry** — only a `geometryRef`.
  - **`basis` (optional, controlled only):** the de jure ↔ de facto nature of controlled
    territory — `sovereign` (a polity's own recognized homeland), `occupied` (another's
    land held by force), or `administered` (governed without homeland sovereignty: colony,
    protectorate, mandate, client/puppet). Left null when the sources don't classify it.
  - **`sovereignPolity` (optional):** the de jure owner, named only when control is not
    sovereign (basis `occupied`/`administered`) and different from the controller. This is
    what lets the map render held-not-owned land — e.g. German-occupied France — as the
    controller's colour **textured over the sovereign's**, rather than simply recoloured.
    The LLM classifies `basis` during extraction (T5) and abstains (null) when unclear;
    the renderer (T4) keys the sovereign-vs-occupied treatment off it.
- **Geometry model.** `geometryRef` resolves to a `Polygon`/`MultiPolygon` held in a new
  `territoryGeometries` collection, each tagged `{ sourceDataset, attestedYear, license }`.
  Geometry is attached by a deterministic resolver (below), referenced by id — keeping it
  out of the LLM's output and keeping the investigation JSON's geometry auditable and
  swappable. (Open question: inline vs. a referenced asset bundle — see Open Decisions;
  polygons are large.)
- **Capability/facet.** A `territory` facet flips ON exactly when ≥1 `ControlState`
  resolves to real geometry — same pattern as the Slice-1 `timeline` and Slice-2 `map`
  facet flips. Omitted otherwise.
- **Validation rules** (extend the existing cross-record rule set): every `ControlState`
  has ≥1 `evidenceLinkId`; `validFrom ≤ validTo`; `polity` and every referenced id exist;
  `geometryRef` resolves; `contested` names ≥2 polities; **`influence`/`contested` may not
  claim `building`/`city` precision** (only `region`/`approximate`). Honesty coupling
  (analog to the existing map/raster Rule 15): a `ControlState` renders a **firm-edged**
  control fill only when `kind = controlled` *and* its geometry is boundary-level from a
  sourced dataset; everything else renders fuzzy.

## Data sources (free/offline-first, per AGENTS.md §5)

- **Bundled historical-boundaries dataset** for area geometry — e.g.
  `historical-basemaps` (world polities at snapshot years), shipped as offline GeoJSON in
  `public/` alongside the Natural Earth basemap. License must be verified and download
  approved before use.
- **Gazetteers (existing: Wikidata + World Historical Gazetteer)** continue to supply
  point coordinates and label names.
- **OpenHistoricalMap (date-filtered)** remains an *optional*, higher-fidelity **networked**
  layer with a later CSP/network decision — not required for the first territory build.

## Deterministic geometry resolver (not the LLM)

A resolver in the `acquisition` package maps a grounded `ControlState` (named polity +
time interval) to a polygon: match the polity name against the bundled dataset and pick
the **nearest snapshot year ≤ the interval**, tagging `attestedYear`. **No match ⇒ no
geometry**: the `ControlState` stays as a non-rendered claim rather than inventing a
frontier. This is the load-bearing honesty boundary and is fully deterministic.

## Extraction pipeline (new stage)

- New module `backend/src/chronicle/acquisition/control_state.py` — inside the
  **already-guard-scanned** `acquisition` package (`SCANNED_PACKAGES` in
  `backend/tests/ai/tools/test_no_topic_branching_guard.py`), so no event names, no
  polity-name branches. `extract_control_states(passages, period, polities)` returns
  grounded `ControlState` claims (abstain-not-fabricate; every claim cites passages; drop
  ungrounded/anachronistic), exactly like `extraction.extract_events`.
- `assembly.assemble_enrichment` gains `control_states`; `corpus_builder` merges them and
  flips the `territory` facet.
- Gated behind the existing opt-in env flag `CHRONICLE_ENABLE_EXTRACTION` (as Slice 1).
- The geometry resolver is wired via `defaults.py`, deterministic, separate from the LLM.

## Frontend (React port of the locked prototype)

- Port the renderer into `GeneratedMap` (`MapView.tsx`): canvas hatch/stripe pattern
  generation → `map.addImage`; layer stack `influence → control → contested → labels`;
  the docked **legend rail** as a component. Drop `turf` clipping unless a source proves
  to need it (keep the bundle lean).
- **Unify on one cursor.** Consume the workspace's existing `currentTime`
  (`TemporalMapRail.tsx` / `timeVisibleEventIds`) as the single time cursor; territory
  layers filter `ControlState` by interval, stepping to the nearest snapshot; surface
  "as of ~Y" in the UI.
- Tests in `MapView.test.tsx`: territory facet renders the legend + provenance + honest
  "as of" note; jsdom can't render GL, so assert the accessible fallbacks and honesty text
  as the Slice-2/3 tests already do.

## Sequencing (slices, smallest-complete-first)

Maps onto ADR-004 steps 2–4. Each is its own vertical slice, its own commit (with fresh
per-instance permission), and leaves the suite green.

1. **T1 — one `currentTime` cursor over existing markers** (ADR-004 step 2). Generalize
   the temporal rail into `GeneratedMap`; event markers filter by `currentTime`. No new
   contract; independent; ships first.
2. **T2 — contract:** `ControlState` + `territoryGeometries` + validation rules + facet,
   both stacks in parity, no rendering yet (fixtures prove validation).
3. **T3 — bundled boundaries dataset + deterministic geometry resolver** (name + year →
   polygon; no-match → omit), offline.
4. **T4 — frontend territory rendering:** port the prototype renderer + legend rail,
   time-filtered, honest labels.
5. **T5 — LLM control-state extraction stage** (`acquisition/control_state.py`) behind the
   env gate; live-verify on ≥2 subjects (Punic + one modern) to prove generality and
   abstention on thin coverage.
6. **T6 — deeper LLM/map tandem** (shared `currentTime`/`focus`) — ADR-004 step 4.

## Verification

- **Backend:** validation unit tests for the new rules; resolver unit tests (match,
  nearest-year, no-match → omit); extraction tests (grounded, abstain, anachronism drop);
  anti-topic-branching guard green; full suite green.
- **Frontend:** schema round-trip + validation parity tests; `MapView` tests; typecheck,
  lint, build.
- **Live (network + Ollama):** ≥2 subjects including one non-Punic; territory renders
  **only** where sourced geometry exists; an out-of-coverage era falls back to markers with
  no fabricated frontier.

## Open decisions (resolve at or before the relevant slice)

- **Boundaries dataset + license.** Which historical-boundaries dataset, and its license —
  needs verification and a download approval (like Natural Earth / the glyphs).
- **Geometry storage.** Inline in the investigation JSON vs. a referenced asset bundle;
  polygons are large, so lean toward referenced to keep the payload light.
- **Polity-name matching.** How extracted polity strings reconcile to dataset polity names
  (aliases, spelling, period names) **without** per-event branching — a generic
  alias/fuzzy-match table, driven by data, not code.
- **Client-side clipping.** Probably unnecessary in production if sourced geometry is
  province-clean; confirm and drop `turf` if so.
- **OHM networked layer / CSP.** Deferred, as in ADR-004.

## References

- ADR-004 (the decision this plan implements).
- Slice 1–3 commits `f56514a`, `8a51a75`, `fd7b564` (extraction, generated map, labels).
- `docs/architecture/geographic-and-map-generation.md` (precision honesty),
  `timeline-generation.md`, `source-to-narrative-enrichment.md`.
- `docs/research/generated-map-basemap-source.md` (the Slice-2 physical basemap pattern
  the boundaries dataset will follow).
- `backend/tests/ai/tools/test_no_topic_branching_guard.py` (`SCANNED_PACKAGES`).
