# AI-First Pivot Plan

## Objective

Convert the working Blank Cheque prototype into a generic renderer for a versioned `GeneratedInvestigation` fixture, then establish a deterministic mock generation CLI. Do not implement live search, downloads, embeddings, or model calls in the first pivot slice.

**Execution status (2026-08-03):** Plans 1–2 are complete. Automated checks and the manual agent-browser walkthrough pass. Plans 3–4 are the next implementation scope and have not started.

## Plan 1 — Baseline and Golden Fixture

**Status:** Implemented.

1. Run and record lint, typecheck, unit/component, build, and E2E results.
2. Add package-level Zod schemas and validation rules from `generated-investigation-contract.md`.
3. Convert the existing Scene object into `fixtures/blank-cheque.golden-investigation.json` without changing its historical assertions.
4. Validate the JSON through runtime schema and referential checks.
5. Add tests for unsupported schema version, broken IDs, unsupported synthesis claims, invalid public evidence, and map-rights/precision failures.

## Plan 2 — Generic Renderer Migration

**Status:** Implemented.

1. Add a package repository/loader returning validated packages with success/partial/failure modes.
2. Add a normalized frontend view model, retaining current facet contracts where possible.
3. Route by package/investigation ID; remove `SCENE_ID` and “July Crisis” from generic page code.
4. Add first-class focus types for claim/relationship/source/passage rather than misusing person entity focus.
5. Keep current map/graph/list/evidence components and adapt them to package references.
6. Update tests to load the golden JSON; keep historical assertions inside fixture-specific tests only.

**Acceptance:** `rg` finds no July Crisis/Blank Cheque constants in generic renderer/data-provider files; the golden package reproduces current behavior and all existing accessibility/failure tests pass.

## Plan 3 — Contract Parity and Mock CLI

**Status:** Not started.

1. Create `backend/` package structure with Pydantic models mirroring the interchange contract.
2. Add shared golden JSON contract tests in TypeScript and Python.
3. Implement persisted workflow-run/stage-run models and deterministic mock providers.
4. Implement `chronicle generate`, `resume`, and `inspect` commands.
5. Produce a mock Concert of Europe package plus generation report without network/model access.
6. Render the CLI output in the frontend as a second fixture, proving genericity.

## Plan 4 — Verification and Handoff

**Status:** Phase B verification and handoff complete; Phase C verification work not started.

1. Run all frontend and backend commands from clean documented setup.
2. Test invalid/partial/abstained packages and resumable stage failures.
3. Update README, current phase, architecture, and limitations.
4. Prepare the factual Codex handoff.

## Proposed Backend Structure

Use the structure in `investigation-generation-pipeline.md`: domain, workflows, stages, providers, repositories, verification, CLI, and later API. PostgreSQL/background workers are not required for the first deterministic CLI; persistence may start with an explicit local artifact store behind a repository interface, then migrate without changing stage contracts.

## Decisions Requiring Kamal Approval

- Confirm the supported domain: European diplomatic/political history, 1814–1914.
- Confirm that Phase B precedes the five-participant Gate 1 study; current manual-content Gate 1 is no longer the next product gate.
- Confirm Python packaging/tooling choice when Plan 3 begins.
- Confirm whether generated drafts may be shared privately before human historical review (they must remain labelled and non-public by default).

## Explicitly Deferred

Live provider/API selection, live LLM/Ollama calls, embeddings/pgvector, background worker technology, database migrations, file upload, arbitrary web fallback, and automatic map georeferencing.
