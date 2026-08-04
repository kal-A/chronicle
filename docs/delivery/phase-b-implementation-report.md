# Phase B Implementation Report

## Outcome

Phase B converts the working prototype from an event-specific TypeScript Scene into a generic renderer for validated, versioned `GeneratedInvestigation` JSON. The current historical experience is preserved, but the frontend now receives package data through the same interchange boundary intended for the future generation pipeline.

## Runtime Flow

`fixtures/blank-cheque.golden-investigation.json` is registered by the content fixture registry, validated by the package contract, loaded by package/scene ID, normalized into a derived `Scene` view, and passed to the existing Explore facets. Generic page, route, repository, and facet code contains no July Crisis or Blank Cheque constants.

Package evidence is canonical and normalized: Claims, Relationships, Events, and KnownAtTime records reference top-level EvidenceLinks by ID. The Scene adapter rehydrates the embedded link arrays used by the preserved UI. Material synthesis resolves to structured records, major claim findings require a claim ledger with a supporting Passage, and displayed maps require usable rights/period-fit decisions with marker precision no greater than the Place evidence.

## Source Extensibility

Any investigation can add Sources, Documents, Passages, and EvidenceLinks without changing renderer code. New material can affect explanatory text only through an explicit evidence chain and a NarrativeBlock reference to the affected Claim, Relationship, or KnownAtTime record. This provides more context and accounting while preventing an upload or newly discovered source from silently rewriting an active narrative. Human impact review and immutable publication revisions remain Phase K work.

## Main Files

- `fixtures/blank-cheque.golden-investigation.json`
- `src/features/investigation/model/generatedInvestigation.ts`
- `src/features/investigation/model/normalizeInvestigation.ts`
- `src/content/investigationFixtures.ts`
- `src/features/investigation/data/investigationRepository.ts`
- `src/features/investigation/InvestigationPage.tsx`
- `src/app/routes.tsx`
- focus, graph, evidence, and SourceDetail files under `src/features/investigation/`

The removed legacy files were `src/content/july-crisis/scene-2-blank-cheque.ts` and `src/features/investigation/data/staticProvider.ts` plus its test.

## Tests Added or Expanded

- Package schema and reference validation, including version, unsupported synthesis, published evidence, map rights, and precision failures.
- Golden package validation and historical-content preservation assertions.
- Package-to-Scene normalization and evidence-link rehydration.
- Package repository success, partial/empty, failure, not-found, and route metadata.
- Focus serialization for claim, relationship, source, and passage.
- Package-driven page route/not-found behavior.
- Package-driven browser-tab metadata, added after browser QA exposed a stale event-specific HTML title.
- Cross-facet claim, relationship, source, and passage selection.

## Manual Browser Walkthrough

On 2026-08-03, `agent-browser` 0.33.2 attached to a controlled local Chrome-for-Testing session and walked the application from `/`. The flow verified the generic redirect and package title; timeline-to-narrative/evidence focus; Vienna map focus; claim and disputed-relationship graph focus; source detail and passage focus; URL serialization; browser-back restoration; prototype-review labeling; supporting/counterevidence display; and source limitations. A full-page screenshot was visually inspected in both the rendered graph and evidence/source-detail state.

The walkthrough found one stale browser-tab title in `index.html`. A regression assertion first failed against the stale title, then passed after the static title became generic and `InvestigationPage` set package-driven metadata. A live reload returned `The German Assurance and Vienna’s Posture, 4–10 July 1914 · Chronicle`.

## Known Limitations

- The package is a migrated human-curated draft, not model output and not independently peer-reviewed history.
- AI record/stage provenance, Pydantic parity, workflow persistence, and deterministic generation CLI begin in Phase C.
- Decision, Communication, Perspective, Conflict, Uncertainty, and ResearchGap collections are present at the interchange boundary but are not rendered by the current golden package.
- MapLibre remains the largest production chunk; this is an existing performance advisory, not a Phase B correctness failure.
- Five Playwright journeys and the separate agent-browser walkthrough pass.
- Git still has no initial commit; no commit or push was performed.

## Codex Handoff: Phase B Generated-Investigation Contract and Generic Renderer

Feature or phase: Phase B — Generated-Investigation Contract and Generic Renderer  
User problem: Chronicle’s working Explore prototype was coupled to one hard-coded historical Scene and could not accept generation-pipeline output or reusable source enrichment.  
Expected user outcome: The same Explore experience loads a validated package/scene route, preserves evidence/map/graph/timeline behavior, and can accept additional investigations and sources without renderer changes.  
Relevant product documents: `docs/product/ai-first-product-definition.md`, `docs/product/generation-first-user-experience.md`, `docs/product/supported-domain-strategy.md`  
Relevant architecture documents: `docs/architecture/generated-investigation-contract.md`, `docs/architecture/domain-model.md`, `docs/architecture/frontend-architecture.md`, `docs/architecture/provenance-and-review.md`  
Files changed: See “Main Files” and the current working tree; all repository files remain untracked because no initial commit exists.  
Database changes: None.  
API changes: None; frontend route added at `/investigations/:packageId/scenes/:sceneId`.  
Tests added: Generated package contract, golden fixture, normalizer, repository, expanded focus serialization, package route, and cross-facet record/source focus tests.  
Commands run: `npm run lint`, `npm run typecheck`, `npm test -- --run`, `npm run build`, `npm run test:e2e`, hard-coding searches with `rg`, and the manual `agent-browser` walkthrough.  
Known limitations: Human-curated golden package only; no backend/model pipeline; existing MapLibre chunk advisory; jsdom canvas diagnostic; no initial Git commit.  
Risks: Zod/Pydantic drift once Phase C starts; future generators bypassing the validator; public status being assigned before review; adding duplicate narrative truth outside referenced records; incomplete future schemas for currently empty extension collections.  
Acceptance criteria: Golden JSON validates and reproduces current behavior; generic code has no event constants/imports; loader supports success/partial/failure; first-class record/source focus works; preserved unit/accessibility/E2E checks pass.  
Specific areas requiring independent review: Cross-record validation completeness; published-evidence gate; canonical EvidenceLink-to-Scene adapter; map rights/precision checks; focus URL compatibility; whether Phase C should strengthen provenance/extension schemas before producing its second fixture.
