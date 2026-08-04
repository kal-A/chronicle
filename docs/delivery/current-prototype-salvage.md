# Current Prototype Salvage Report

## Audit Date and State

Audited 2026-08-03. Contrary to the earlier documentation-only handoff, the repository now contains a working frontend prototype. There is no backend, database, generation CLI, provider adapter, live model, or generated-investigation package yet. Git still has no commit and all files are untracked.

## Current Structure

```text
src/app/                         app shell and routing
src/content/july-crisis/         hard-coded Blank Cheque Scene fixture
src/features/investigation/
  data/                          static Scene provider
  model/                         Zod schema and graph validation
  focus/                         centralized URL focus contract
  narrative/ timeline/ map/
  graph/ evidence/               renderer facets
src/test/                        test/a11y utilities
tests/e2e/                       Playwright journeys
public/maps/july-crisis/         curated period map asset
```

## Reusable Components

- React/Vite/TypeScript/Tailwind app and scripts.
- Zod historical date, provenance, claim, relationship, evidence, entity, event, map-layer, and Scene validation.
- Whole-fixture referential validator.
- Async provider interface with loading/empty/failure behavior.
- URL-persisted Focus and feedback-loop-safe synchronization.
- Narrative, timeline, MapLibre/schematic map, Cytoscape/accessible graph, and evidence renderers.
- Accessible list alternatives, keyboard behaviors, axe checks, and Playwright foundation.
- Curated Blank Cheque evidence and period map as a golden reference case.

## Event-Specific Hard Coding

- `src/content/july-crisis/scene-2-blank-cheque.ts` is a TypeScript Scene object, not a generic package fixture.
- `InvestigationPage.tsx` hard-codes `SCENE_ID` and “July Crisis of 1914.”
- `staticProvider.ts` imports the July Crisis module and derives empty data from it.
- Several unit/E2E tests import or assert Blank Cheque, Berlin, Vienna, 1914, and Scene 2 directly.
- Map asset path and map-source comments are July Crisis-specific.
- Focus entity type is currently reused for claim-node selection in the graph, showing that the renderer contract needs a first-class claim focus.

Historical content inside the fixture is allowed; coupling in renderer/provider code is the migration target.

## Current Domain Model

The frontend schema already models HistoricalDate, Source, Document, Passage, Entity, Event, Claim, Relationship, EvidenceLink, KnownAtTime, NarrativeBlock, Scene, and HistoricalMapLayer with strong integrity refinements. It lacks the top-level request/scope/package/version/generation report, workflow records, candidate source/assessment, claim ledger, communication/decision detail, conflict/uncertainty/gap records, map-scene interaction contract, and verification result types required by the pivot.

## Test Coverage

Coverage includes schema/refinement failures, fixture references, provider success/empty/failure, focus serialization/history, cross-facet synchronization, accessibility, keyboard navigation, and a Gate 1 journey. Pivot baseline on 2026-08-03: 8 Vitest files / 51 tests passed; 5 Playwright journeys passed; lint, typecheck, and production build passed.

## What Must Be Preserved

- Historical integrity and passage-level provenance.
- No certainty-implying schema defaults.
- Disputed relationship counterevidence.
- Time-role and location-precision semantics.
- Curated map rights/georeference notes.
- Loading, empty, failure, keyboard, screen-reader, and reduced-motion behavior.
- URL focus/back-forward behavior.
- Existing tests until equivalent package-driven tests replace them.

## Conversion Risks

- Creating a second backend schema that drifts from Zod.
- Treating the golden JSON as manually trusted instead of schema-validated.
- Flattening Scene-local arrays into a package without stable references/versioning.
- Breaking cross-facet focus while adding package-level targets.
- Letting generation reports or partial packages overwhelm the reader UX.
- Confusing generated draft, prototype-curated, reviewed, and published states.
- Expanding backend/provider complexity before the mock end-to-end contract works.

## Likely Implementation Changes

- Add `fixtures/blank-cheque.golden-investigation.json`.
- Extend/refactor `src/features/investigation/model/schema.ts` into package schemas.
- Replace direct content imports in `staticProvider.ts` with a package repository/loader.
- Make `InvestigationPage` route/package-driven.
- Normalize package data for current facet props or adapt facets incrementally.
- Update tests to load the golden JSON and add invalid-package/version cases.
- Later add `backend/` with Pydantic mirrors and contract fixtures.

## Phase B Disposition

This report is the pre-migration baseline. Phase B subsequently completed each listed migration: the TypeScript scene and static provider were removed; the golden JSON, package validator, normalizer, package repository, package-driven route, and first-class record/source focus types now replace them. See `phase-b-implementation-report.md` for the current state.
