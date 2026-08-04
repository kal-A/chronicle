# Validation Status

Tracks the review/confidence state of historical content as a whole, distinct from the per-claim `review_status` field in the domain model. This document is a living register of what's been curated vs. reviewed vs. published, updated as Phase 0/1 content work proceeds — it is not the enforcement mechanism (that's `docs/architecture/provenance-and-review.md`), just the human-readable status board.

## Status Levels

- **Identified** — a source or claim has been noted as relevant but not yet examined in detail.
- **Curated** — a source has been added to the source register with evidentiary notes.
- **Passages extracted** — exact, locator-bearing passages have been pulled from an acquired document and recorded, per `docs/research/review-standard.md`, but have not passed independent (non-owner) review.
- **Prototype-curated** — a Claim/Relationship/KnownAtTime has passed the Plan 0 content-gate checks and owner review, sufficient for Phase 1 prototype display with an explicit prototype label, but has not passed the full `review-standard.md` bar.
- **Reviewed** — content meets the full bar in `review-standard.md` to be marked `reviewed` in the domain model and is eligible for publication in Explore.
- **Disputed** — content has passed traceability/review checks but credible disagreement is material to its interpretation; published with its disputed label and rationale intact.
- **Rejected** — content did not meet the bar; reviewer notes recorded.

## July Crisis — Current Status

| Area | Status |
|---|---|
| Source register (21 sources) | Drafted; mix of passages-extracted/acquired/identified entries |
| Chapter/scene outline | Drafted; four scenes, content review incomplete |
| Scene 2 content fixture (`docs/research/scene-2-content-fixture.md`) | `prototype-curated` — owner-reviewed against the Plan 0 gate on 2026-08-03; not independently reviewed; not eligible for anything beyond Phase 1 prototype display |
| Scene 2 primary passages (`jc-src-001-p1`, `jc-src-002-p1`, `jc-src-002-p2`, `jc-src-021-p1`) | Passages extracted, locator-bearing, sourced from public GHDI/BYU transcriptions of published documentary editions. `jc-src-021` (Franz Joseph's own letter) added 2026-08-03 to give the "blank cheque" moment its own request, not just Wilhelm's reply. |
| Scene 2 disputed-relationship sourcing (`jc-src-020-p1`, `jc-src-020-p2`) | Passages extracted from an open scholarly reference; stands in for direct `jc-src-016`/`jc-src-013` passages, which remain an acquisition gap |
| Actor "known at the time" reconstruction | Started for Scene 2 only (K1); Scenes 1/3/4 not started |
| Disputed-interpretation register (Fischer/Clark on the blank cheque) | Started for Scene 2 (Relationship R1); not started for other scenes |
| Place/geography records (period-accurate) | Started — Berlin/Vienna have city-precision records and coordinates |
| Scene 2 basemap (`docs/research/scene-2-map-source.md`) | Acquired, rights-cleared (public domain), limitations disclosed — Shepherd's *Historical Atlas* (1911) "Europe at the Present Time," via UT Austin PCL Map Collection. Not independently reviewed. Balkans/Ottoman boundaries on the plate predate the 1912–13 Balkan Wars (disclosed gap; irrelevant to Berlin/Vienna, which the default map view is scoped to). |

The initial artifacts are `july-crisis-source-register.md` and `phase-1-scene-outline.md`. Their existence does not confer `reviewed` status. Scene 2 has been selected for the first prototype slice; its Plan 0 content gate (per `phase-1-scene-outline.md`) is satisfied at `prototype-curated` level — see `docs/research/scene-2-content-fixture.md` for the full passage/claim/relationship chain and its disclosed gaps.

## Process Note

Do not mark anything `reviewed` in seed data (Phase 2) without it having actually reached `reviewed` status here first. Seed data quality is not exempt from the historical-integrity rules in `AGENTS.md` §3 just because it's for a prototype — Phase 1's mock data may be illustrative/simplified, but Phase 2 onward seed data is treated as real content and held to the full bar.
