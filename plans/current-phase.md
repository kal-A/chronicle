# Current Phase

**Phase:** AI-first pivot — Phase B complete; Phase C awaiting approval  
**Status:** The versioned package contract, golden JSON, generic renderer route, and preserved Explore facets are implemented and verified. No backend, live provider, database, retrieval, embeddings, or model calls exist.

## Phase B Delivered

- Added the `GeneratedInvestigation` Zod contract, supported schema version, generation report, interaction specification, historical map asset/map scene, claim ledger, normalized evidence-link records, and cross-reference validation.
- Enforced unsupported-version, reference, synthesis-ledger, published-evidence, relationship-evidence, verification, rights/period-fit, and location-precision failures.
- Migrated the full prototype content into `fixtures/blank-cheque.golden-investigation.json` without changing its historical assertions.
- Removed the legacy TypeScript scene and static Scene provider.
- Added a validated package repository with success, honest partial/empty, not-found, scene-not-found, and simulated-failure modes.
- Added `normalizeInvestigationScene`, keeping the existing narrative/timeline/map/graph/evidence components while making the package canonical.
- Replaced the hard-coded scene/page with `/investigations/:packageId/scenes/:sceneId`; `/` redirects using registered default-package metadata.
- Added first-class claim, relationship, source, and passage focus alongside scene, event, entity, and time-range focus.
- Preserved keyboard, accessibility, URL focus, cross-facet, map, evidence, loading, empty, and failure foundations.

## Evidence and Source-Enrichment Invariant

New historical sources can be added to any period or event through package-level Source, Document, Passage, and EvidenceLink records. They influence conclusions or prose only when a supported Claim/Relationship/KnownAtTime is created or revised and a material NarrativeBlock explicitly references that record. A Source record by itself never mutates narrative text. Phase K will route these effects through immutable impact review and human acceptance before publication.

## Verification Recorded 2026-08-03

- `npm run lint` — passed.
- `npm run typecheck` — passed.
- `npm test -- --run` — 10 files, 72 tests passed; jsdom emits the known canvas-not-implemented diagnostic while accessible fallbacks are exercised.
- `npm run build` — passed; Vite reports the existing large MapLibre chunk advisory.
- `npm run test:e2e` — 5 Playwright browser journeys passed.
- Hard-coding acceptance search found no July Crisis/Blank Cheque/package fixture constants in non-test generic renderer, provider, or route files.
- Manual `agent-browser` walkthrough — passed root redirect, package-driven title, timeline/narrative/evidence sync, map place focus, graph claim and relationship focus, source and passage focus, browser-back restoration, and visible limitation/counterevidence checks.
- Browser QA found a stale event-specific HTML title; a failing regression assertion was added, the title became package-driven, and both the targeted test and live-browser reload passed.

## Phase B Closure

- The manual browser flow was walked on 2026-08-03 with `agent-browser` 0.33.2 and its managed Chrome runtime.
- The Phase B Codex feature-diff/historical-integrity handoff is available in `docs/delivery/phase-b-implementation-report.md`.
- No commit or push was performed.

## Next Vertical Slice — Phase C

After explicit approval of Python packaging/tooling:

1. Add Pydantic mirrors and shared JSON contract tests.
2. Add persisted workflow/stage records and deterministic mock providers.
3. Implement `chronicle generate`, `resume`, and `inspect`.
4. Produce and render a second mock package, proving event/domain genericity.

Do not add live search, downloads, embeddings, database infrastructure, or model calls in the Phase C skeleton. Do not commit or push without separate explicit approval.
