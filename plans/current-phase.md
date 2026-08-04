# Current Phase

**Phase:** AI-first pivot — Phase B complete; Phase C0/C1/C2/C3 complete  
**Status:** The versioned package contract, golden JSON, generic renderer route, and preserved Explore facets are implemented and verified. `chronicle generate <any topic>` runs 9 deterministic mock providers through the resumable pipeline and produces an actual `GeneratedInvestigation` package that passes the same validator the frontend uses — for arbitrary topics, with clearly-synthetic, disclosed-as-mock content. A second, real curated provider set (`--provider-set concert-of-europe`) now proves the same pipeline carries genuinely researched content: a second, independently sourced package is registered in the frontend and rendered by the same generic route/components as the hand-authored blank-cheque package. No live provider, database, retrieval, embeddings, or model calls exist yet.

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

## Completed: Phase C0 — Python Foundation and Contract Parity

Kamal supplied an adjusted Phase C plan (`chronicle_phase_c_adjusted_plan.md`) covering the full deterministic-generation phase plus a roadmap through Phase I. Per `CLAUDE.md`'s smallest-complete-vertical-slice rule, Phase C was broken into four sub-plans (C0–C3, mirroring how Phase 1's Plans 0–5 were sequenced and approved one at a time). **Only C0 is built; C1–C3 are sequenced but not started.**

**Assumptions stated and not yet separately confirmed** (per `CLAUDE.md` rule 4 — flagged here, not silently decided): Python tooling is plain `venv` + `pip` + `pyproject.toml` (setuptools) + `pytest`, no `poetry`/`uv` — this was an explicitly open decision in the adjusted plan's own text.

**Built, on a new `phase-c-python-foundation` branch (not merged):**
- `backend/` — a Pydantic v2 package (`chronicle.contracts`) mirroring `src/features/investigation/model/generatedInvestigation.ts` and its `schema.ts` dependencies field-for-field: every enum, every nested type, the exact same optional/required/min-length constraints, and the same two `HistoricalDate`/`NarrativeBlock` cross-field refinements Zod enforces.
- `backend/src/chronicle/contracts/validation.py` — a line-for-line port of `validateGeneratedInvestigation()`'s 20 imperative cross-record rules (ID uniqueness, every reference chain, evidence-role requirements, disputed-relationship counterevidence, map-marker precision vs. Place evidence, published-package gates), numbered and ordered to match the TS source so the two can be diffed by eye.
- `fixtures/contracts/invalid/*.json` — 5 new shared fixtures, each a minimal mutation of the existing golden package targeting one structurally distinct validator rule (unsupported version, dangling evidence reference, claim missing supporting evidence, disputed relationship missing counterevidence, map marker precision exceeding its Place's evidence).
- Cross-language parity proven both directions: Python's `pytest` suite loads `fixtures/blank-cheque.golden-investigation.json` directly (no duplication) and accepts it, and rejects all 5 invalid fixtures for the expected reason; a new TS test block in `generatedInvestigation.test.ts` loads the same 5 invalid fixtures and asserts `validateGeneratedInvestigation()` rejects them too.

**Verification:** Python — 8/8 pytest passed. Frontend — `npm run typecheck`, `npm run lint`, `npx vitest run` (77/77, up from 72), `npm run build`, `npm run test:e2e` (5/5) all pass clean, no regressions.

**Explicitly not in C0:** no workflow engine, no stage-run persistence, no CLI, no providers, no second package, no live calls.

## Completed: Phase C1 — Workflow Engine, File-Based Run Storage, CLI Skeleton

Still on `phase-c-python-foundation`, not merged. Proves the deterministic, resumable workflow engine's *mechanics* before any real (even mocked) domain-provider logic exists (C2).

**Stage taxonomy** (from the adjusted plan §4, used verbatim, not "mock"-prefixed so it stays valid once C2+ replace the stubs): `SCOPE_PROPOSED → DISCOVERY_QUERIES_PREPARED → SOURCE_CANDIDATES_DISCOVERED → SOURCES_ASSESSED → CORPUS_PREPARED → HISTORICAL_MODEL_ASSEMBLED → INVESTIGATION_COMPOSED → VERIFIED`, ending in one of `ready | partial | abstained | failed`.

**Built:**
- `backend/src/chronicle/workflow/` — `RunRecord`/`StageRecord` Pydantic models (fields per the adjusted plan §7), and `engine.py`'s `generate()`/`resume()`/`run_pipeline()`/`run_stage()`. Reuse-vs-rerun is decided per stage by comparing the current input's hash against the hash on that stage's last `PASSED` attempt — since each stage's input is exactly the previous stage's output, a changed upstream result automatically produces a different hash at the next stage, so downstream invalidation needs no separate bookkeeping pass.
- `backend/src/chronicle/storage/run_store.py` — file-based persistence (`backend/runs/<run-id>/run.json`, `stages/NN-<stage>.json`, `output/<stage>.json`), gitignored.
- `backend/src/chronicle/cli/` — `chronicle generate <topic> [--fail-at STAGE]`, `resume <run-id>`, `inspect <run-id>`, `validate <package-path>` (the last is a thin wrapper around C0's `validate_generated_investigation()`, independent of the workflow system). Registered as a console script.
- C1's 8 stage functions are deliberate, clearly-commented deterministic stubs (not real historical content) — their only job is proving the engine works. `--fail-at <stage>` is an explicit, documented flag (not a hidden magic string) for exercising the `FAILED`/retry/resume-after-failure path honestly.
- **A real circular import was hit and fixed during implementation**, not shipped: `workflow/__init__.py` eagerly re-exporting from `engine.py` (which imports `RunStore` from `storage`, which imports from `workflow.stages`/`state`) created a cycle depending on import order. Fixed by having `workflow/__init__.py` only re-export the cycle-free `stages`/`state` modules; consumers import `chronicle.workflow.engine` directly.

**Verification:** 30/30 pytest passed (8 contract + 6 storage + 9 CLI + 7 workflow-engine), including: fresh run completes all 8 stages `READY`; unchanged resume reuses every stage (attempt counts stay at 1, confirmed by inspecting persisted records, not just final status); a changed topic invalidates and reruns every stage; `--fail-at` produces `FAILED` with correct partial completion and attempt count; resuming a failed run without the induced fault succeeds and doesn't re-execute stages that already passed; two runs with identical input produce identical stage output hashes. Manually smoke-tested the actual CLI end-to-end (not just the test suite) for all four commands, including `validate` against both the real golden fixture and a C0 invalid fixture. Frontend — typecheck/lint/`npx vitest run` (77/77, unchanged) all pass; C1 touches no frontend files.

**Explicitly not in C1:** no real historical content, no domain provider logic, no second package, no live calls, no `PARTIAL`/`ABSTAINED` semantics (those need real corpus/evidence-quality judgment that only exists once C2 lands — deliberate deferral, not an oversight).

## Completed: Phase C2 — Deterministic Mock Providers, Assembler, Verifier

Still on `phase-c-python-foundation`, not merged. `chronicle generate <topic>` now produces a real, schema-valid `GeneratedInvestigation` package for *any* topic string. Per Kamal's explicit choice, content is **generic and topic-agnostic** — clearly-synthetic, deterministically-templated, disclosed as mock — proving the pipeline mechanically assembles a valid package end to end. Real historical curation for "The Concert of Europe and Revolutionary Intervention" is C3's job, researched the way Scene 2 actually was, not templated.

**Built, replacing C1's stubs without any change to `engine.py`'s stage-execution contract:**
- `backend/src/chronicle/providers/mock/` — the 9 providers from the adjusted plan §8 (scope, discovery-query, source-candidate, source-assessment, a deterministic — not "mock" — corpus assembler, historical-extraction, timeline, relationship, geography), composed in `providers/registry.py`'s `MOCK_STAGE_FNS` onto C1's existing 8 `StageName`s (no `STAGE_ORDER` change; extraction+timeline+relationship+geography all compose into `HISTORICAL_MODEL_ASSEMBLED`).
- `backend/src/chronicle/providers/verification.py` — the `VERIFIED` stage: runs the composed draft through C0's `validate_generated_investigation()` (deterministic software, never a "provider", per `AGENTS.md` §4) and returns the validated, re-serialized package as the pipeline's final output.
- **Genuine, non-contrived `PARTIAL` coverage:** the geography provider honestly has no real geography for a synthetic topic, so it produces no map asset — package `status` and `generationReport.outcome` both come out `"partial"`, with the omission disclosed in both places. Real coverage of validator rule 19 and the `PARTIAL` terminal state, not a contrived flag. `ABSTAINED` stays deferred.
- Determinism: every provider is a pure function; the composed package uses a fixed sentinel timestamp (not wall-clock) so two `generate()` calls with the same topic produce byte-identical packages.
- **A real bug was caught during manual smoke-testing, not shipped**: `run_stage()`'s reuse check compares `providerVersion`, but it was hardcoded regardless of which `stage_fns` were actually passed in — meaning resuming a run with a *different* provider set (e.g. C1 stubs → C2 real providers) would have wrongly reused stale output instead of re-running. Fixed by threading `provider_set_version` explicitly through `generate()`/`resume()`/`run_pipeline()`/`run_stage()`, tied to `run.providerSetVersion`; added a regression test.
- `stage_fns` is now a required (not defaulted) argument on `generate()`/`resume()`/`run_pipeline()` — the CLI passes `MOCK_STAGE_FNS`, engine-mechanics tests explicitly pass C1's `DEFAULT_STAGE_FNS` to keep mechanics isolated from content. `RunRecord.outputPackagePath`/`generationReportPath` (defined in C1, unused until now) are populated; the package and report are persisted to `output/package.json` / `output/generation-report.json`.

**Verification:** 49/49 pytest passed (8 contract + 6 storage + 9 CLI + 8 workflow-engine, incl. the new reuse regression test + 18 new provider tests). Manually smoke-tested the full CLI end-to-end, including feeding the CLI's own `output/package.json` back through `chronicle validate` — confirmed valid. Frontend — typecheck/lint/`npx vitest run` (77/77, unchanged) all pass; C2 touches no frontend files.

**Explicitly not in C2:** no real historical content (that's C3), no `ABSTAINED` scenario, no live calls, no frontend changes.

**No commit, no push, no merge** on C0, C1, or C2 — per `AGENTS.md` §9 and the adjusted plan's own instruction, that needs separate explicit approval.

## Completed: Phase C3 — Concert of Europe: Real Curated Package, Frontend Integration, Genericity Proof

Still on `phase-c-python-foundation`, not merged. A second, real, hand-researched investigation — "The Concert of Europe and Revolutionary Intervention, 1814-1822" (the Congress of Vienna, the Troppau Protocol, the Congress of Laibach and the Austrian intervention in Naples, and the Congress of Verona's authorization of French intervention in Spain) — generated end-to-end via `chronicle generate --provider-set concert-of-europe`, registered in the frontend fixture registry alongside the hand-authored blank-cheque package, and proven to render through the exact same generic route/components with a new Playwright journey.

**Assumption stated (per `CLAUDE.md` rule 4):** since no live retrieval/LLM layer exists yet (by design, deferred past Phase C), "real content generated via `chronicle generate`" means a second, topic-specific **curated** provider set — hand-researched and hand-written, exactly as rigorous as Scene 2's authoring, expressed as deterministic Python functions plugged into the same 8-stage engine contract, rather than a generic algorithm that could curate any topic.

**Built:**
- `backend/src/chronicle/providers/curated/concert_of_europe/` — real Source/Document/Passage records for three primary documents (the Congress of Vienna's General Treaty, the Troppau Protocol, and Castlereagh's State Paper of 5 May 1820), 4 real Person entities (Metternich, Alexander I, Castlereagh, Canning) and 5 real Place entities with genuine coordinates, 5 events dated within their real historical ranges, 5 claims, and 3 relationships — including one genuine `disputed` relationship (Britain's rejection of the Troppau doctrine) carrying both a supporting and a counterevidence link, the same validator rule 7 path C2's mock relationship exercised, now with real content.
- **Sourcing discipline, disclosed per-source:** the Vienna Final Act is cited to a directly hosted, independently verified public-domain full text (Wikisource); the Troppau Protocol's key clause is quoted directly because it is independently corroborated with consistent wording across multiple secondary descriptions, with the gap that no directly hosted full primary transcription was located explicitly disclosed; Castlereagh's State Paper is represented as an honest paraphrase, not a fabricated verbatim quotation. No quotation in this package is invented.
- **A real, rights-cleared period map for one scene only.** William R. Shepherd, *Historical Atlas* (1911), "Treaty Adjustments, 1814, 1815," p. 157 (PCL-digitized, public domain) — downloaded to `public/maps/concert-of-europe/`, documented in `docs/research/concert-of-europe-map-source.md` (bounds read from the plate's own printed reference grid by visual inspection, disclosed as an approximation). Deliberately **not** attached to the second scene ("The Principle of Intervention, 1820-1822"): the plate documents the 1815 settlement, not the Troppau/Laibach/Verona-era situation five to seven years later, so the honest choice is no map for that scene, not a misfit one — disclosed in `generationReport.omissions`, the same discipline `docs/research/scene-2-map-source.md` established for its own gap.
- **A second genuine, disclosed gap:** no dedicated Congress of Verona primary document was independently located and curated in this pass, so `claim-verona-spain` and its relationship are supported only indirectly, via continuity with the Troppau doctrine — stated plainly in the package's own omissions, not hidden.
- **A real bug caught and fixed during integration, not shipped:** registering the generated package in the frontend surfaced that Pydantic's `model_dump(mode="json")` serializes unset `Optional[...]` fields as `null`, while the TS/Zod contract's `.optional()` fields require the key to be *absent*, not present-as-null — a present-but-null optional field failed frontend schema validation even though it passed Python's validator. Fixed in `providers/verification.py` by adding `exclude_none=True` to the final serialization; this fix applies to the mock provider set too, closing a latent C2 gap that had gone uncaught because no C2 mock package had previously been round-tripped through the frontend's Zod schema.
- `--provider-set {mock,concert-of-europe}` added to `chronicle generate`/`resume` (default `mock`, so every existing C0-C2 test's behavior is unchanged); `cli/commands.py`'s `PROVIDER_SETS` lookup table selects the `(stage_fns, provider_set_version)` pair. No changes to `engine.py`'s stage-execution contract were needed — the curated provider set plugs into exactly the same `StageFn` shape the mock set uses.
- `fixtures/concert-of-europe.generated-investigation.json` — the frozen, checked-in output of `chronicle generate "The Concert of Europe and Revolutionary Intervention" --provider-set concert-of-europe`, confirmed byte-identical across two independent runs before freezing. `src/content/investigationFixtures.ts` registers it (`isDefault: false`) alongside the golden and empty fixtures.
- `tests/e2e/concert-of-europe-journey.spec.ts` — two new Playwright journeys: the Vienna scene (real map citation renders, narrative → evidence sync, cross-facet place selection) and the intervention scene (schematic-fallback map with its own honest "no period-accurate basemap curated for this scene yet" label, disputed-relationship evidence rendering visible classification text, not color alone).

**Verification:** Python — 59/59 pytest passed (49 existing + 10 new: 2 pipeline + 7 content-accuracy + 1 CLI). Manual: `chronicle generate ... --provider-set concert-of-europe` then `chronicle validate` on its own output — confirmed valid; reran and diffed the two runs' `output/package.json` byte-for-byte identical before freezing into `fixtures/`. Frontend — `npm run typecheck`, `npm run lint`, `npx vitest run` (77/77), `npm run build` all clean; `npm run test:e2e` — 7/7 passed, including both new Concert-of-Europe journeys alongside all pre-existing journeys unmodified.

**Explicitly not in C3:** no live search/retrieval/embeddings/model calls (still deferred past Phase C). No changes to `engine.py`'s stage contract. No third package.

**No commit, no push, no merge** on C0-C3 — per `AGENTS.md` §9, that needs separate explicit approval. This closes out the Phase C roadmap from the adjusted plan.

### Codex Handoff: Phase C — Python Deterministic-Generation Backend (C0-C3)

**Feature or phase:** Phase C (all four sub-plans: C0 contract parity, C1 workflow engine, C2 mock providers, C3 real curated package + frontend integration), per `chronicle_phase_c_adjusted_plan.md`.
**User problem:** Prove that a deterministic, resumable, file-persisted Python pipeline can produce packages conforming exactly to the existing `GeneratedInvestigation` contract — first mechanically (C0-C2, synthetic content), then for real (C3) — as the foundation the eventual AI-generation layer (Phase D+) will build on.
**Expected user outcome:** `chronicle generate <topic> [--provider-set mock|concert-of-europe]` produces a schema-valid package; the frontend renders a second, independently sourced investigation through the same generic route/components as the original hand-authored one, with no hidden coupling.
**Relevant product documents:** `chronicle_phase_c_adjusted_plan.md` (supplied by Kamal, not checked into the repo as a file), `AGENTS.md` §4 (deterministic software vs. provider-layer boundary) and §12 (historical-integrity discipline).
**Relevant architecture documents:** `docs/architecture/spatial-architecture.md` (map/period-fit requirements), `docs/research/scene-2-map-source.md` (the disclosed-approximation pattern C3's map doc follows).
**Files changed:** see the C0/C1/C2/C3 "Built" sections above; C3 specifically touches `backend/src/chronicle/providers/curated/concert_of_europe/*` (new), `backend/src/chronicle/providers/verification.py` (`exclude_none` fix), `backend/src/chronicle/cli/{main,commands}.py` (`--provider-set`), `backend/tests/providers/curated/*` (new), `backend/tests/cli/test_cli.py` (new test), `docs/research/concert-of-europe-map-source.md` (new), `public/maps/concert-of-europe/*` (new), `fixtures/concert-of-europe.generated-investigation.json` (new), `src/content/investigationFixtures.ts` (registration), `tests/e2e/concert-of-europe-journey.spec.ts` (new).
**Database changes:** none (file-based run storage only, gitignored).
**API changes:** none (no HTTP API yet — CLI only).
**Tests added:** 59 Python tests total (C0-C3 combined); 2 new Playwright journeys; frontend vitest suite grew implicitly via the new fixture (77 tests, unchanged count — fixture validity is exercised through existing repository/page tests).
**Commands run:** `pytest -v` (backend, all sub-phases); `chronicle generate`/`resume`/`inspect`/`validate` manually for both provider sets; `npm run typecheck`/`lint`/`build`; `npx vitest run`; `npm run test:e2e`.
**Known limitations:** the Concert of Europe package cites the Troppau Protocol and Castlereagh's State Paper via secondary reprints/paraphrase rather than independently verified primary-text transcriptions (disclosed in each Source's `knownLimitations`); the Verona/Spain claim is only indirectly evidenced (disclosed in `generationReport.omissions`); the intervention scene has no period map by design (disclosed, not a bug). None of these are silently hidden — they are the actual point of the disclosure discipline this package exercises.
**Risks:** the `exclude_none` fix changes serialization behavior for every future provider set (mock included) — low risk since it only removes already-optional, already-unset fields, but worth an explicit look given it touches a shared code path.
**Acceptance criteria:** package passes `validate_generated_investigation()`/the frontend's Zod schema unmodified; two independent generations of the same topic are byte-identical; the frontend renders it through the unmodified generic route; a second reviewer should be able to trace every claim in the package back to a disclosed source and confirm no fabricated quotation exists.
**Specific areas requiring independent review:** the historical accuracy of the curated content itself (dates, figures, the Troppau Protocol quotation, the paraphrases) — Codex checks software behavior per `docs/delivery/codex-review-process.md` Review Type D, not independent historical truth; a human with domain expertise should still spot-check the specific claims before this content is treated as anything beyond a prototype curation pass.
