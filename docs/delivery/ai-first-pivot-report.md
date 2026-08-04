# AI-First Pivot Task Report

## Outcome

The repository now documents Chronicle as an AI-powered historical investigation generator. The existing Blank Cheque frontend is preserved and reclassified as the renderer/evidence inspector and source for the first golden package. Active sequencing now begins with the versioned package contract and generic renderer, then a deterministic mock generation CLI.

## Files Created

### Product

- `docs/product/ai-first-product-definition.md`
- `docs/product/generation-first-user-experience.md`
- `docs/product/supported-domain-strategy.md`

### Architecture

- `docs/architecture/generated-investigation-contract.md`
- `docs/architecture/investigation-generation-pipeline.md`
- `docs/architecture/source-discovery-and-acquisition.md`
- `docs/architecture/source-assessment-methodology.md`
- `docs/architecture/claim-and-conclusion-methodology.md`
- `docs/architecture/timeline-generation.md`
- `docs/architecture/geographic-and-map-generation.md`
- `docs/architecture/investigation-assistant.md`
- `docs/architecture/verification-and-abstention.md`

### Delivery and Decision

- `docs/delivery/ai-first-pivot-plan.md`
- `docs/delivery/revised-development-phases.md`
- `docs/delivery/current-prototype-salvage.md`
- `docs/delivery/ai-first-pivot-report.md`
- `docs/decisions/ADR-ai-generation-is-the-product-core.md`

## Files Modified

- `AGENTS.md`
- `README.md`
- `plans/current-phase.md`
- `plans/phase-1-static-prototype.md`
- `docs/product/product-vision.md`
- `docs/product/product-principles.md`
- `docs/product/core-user-experience.md`
- `docs/product/explore-and-studio.md`
- `docs/product/investigation-assistant.md`
- `docs/architecture/system-overview.md`
- `docs/architecture/frontend-architecture.md`
- `docs/architecture/backend-architecture.md`
- `docs/architecture/ai-agent-architecture.md`
- `docs/architecture/deployment.md`
- `docs/delivery/development-phases.md`
- `docs/delivery/definition-of-done.md`
- `docs/delivery/risks-and-open-questions.md`
- `docs/delivery/context-handoff.md`
- `docs/decisions/ADR-001-explore-first.md`
- `docs/decisions/README.md`

## Current Code Preserved

No production or test code was edited. The React/Vite setup, Zod schemas, static provider, focus state, narrative/timeline/map/graph/evidence components, Blank Cheque fixture, map asset, accessibility behavior, and tests remain intact.

## Schemas Introduced in Design

The documentation defines the versioned `GeneratedInvestigation` package, InvestigationRequest/Scope, GenerationReport, workflow/stage runs, SourceCandidate and assessment decisions, ClaimEvidenceLedger, Perspective/Conflict/Uncertainty/ResearchGap, HistoricalMapAsset/MapScene, InteractionSpecification, and VerificationResult boundaries. Implementation is intentionally deferred to Phase B/C.

## Hard-Coded Assumptions

No hard-coded assumptions were removed in this documentation-only task. The salvage audit identifies direct July Crisis coupling in `InvestigationPage.tsx`, `staticProvider.ts`, fixture imports, tests, and asset paths. Phase B removes coupling from generic code while preserving fixture-specific historical assertions.

## Tests Updated

None. Existing tests were run as a regression baseline.

## Commands Run

- `npm run lint` — passed.
- `npm run typecheck` — passed.
- `npm test -- --run` — 8 files, 51 tests passed; jsdom emitted expected non-failing canvas `getContext` notices.
- `npm run build` — passed.
- `npm run test:e2e` — 5 Playwright tests passed.
- Local Markdown-link audit — passed.
- Required pivot-document presence check — all 16 requested documents present.

## Remaining Migration Risks

- Zod/Pydantic contract drift.
- Package normalization breaking focus or evidence resolution.
- Draft/review/publication state confusion.
- Backend/provider overengineering before mock end-to-end proof.
- Search metadata leaking into evidence.
- Rights, OCR, map-period, and georeferencing gaps producing fragile output.
- Generated prose overstating an imbalanced corpus.

## Exact Next Vertical Slice

Execute Phase B Plans 1–2 from `ai-first-pivot-plan.md`: baseline, implement package-level Zod validation, convert the Blank Cheque Scene to `fixtures/blank-cheque.golden-investigation.json`, load it through a generic package repository/route, remove July Crisis constants from generic renderer/provider code, and preserve all existing tests and accessibility behavior.

## Decisions Requiring Kamal Approval

1. Accept the AI-first ADR and Phase A–K sequencing.
2. Accept European diplomatic/political history, 1814–1914, as the initial supported domain.
3. Make Phase B the immediate gate instead of running the deferred five-person manual-content Gate 1 first.
4. Later, choose Python packaging/tooling for the deterministic CLI.
5. Decide whether labelled generated drafts may be shared privately before human historical review.

No commit or push occurred.
