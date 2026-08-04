# Development Phases

> **Superseded for active sequencing.** The AI-first roadmap is `revised-development-phases.md`, adopted by `docs/decisions/ADR-ai-generation-is-the-product-core.md`. This file is retained as the pre-pivot roadmap and historical record.

Full phased roadmap. Each phase must leave a runnable or testable artifact (`AGENTS.md` §10 / `docs/product/product-principles.md` MVP definition). Phase 0 and Phase 1 have dedicated detail docs (`phase-0-product-foundation.md`, `phase-1-static-prototype.md`); Phases 2–10 are specified here at the level needed to plan them when reached — each will get its own detailed plan in `plans/` when it becomes the active phase, per `CLAUDE.md`'s planning-mode workflow.

---

## Phase 0 — Product and Historical Foundation

**Purpose:** Establish durable product/architecture/research documentation and a curated content foundation before any application code.
**Product assumption tested:** None yet — this phase de-risks *what* to build, not whether it works for users.
**User-facing capabilities:** None.
**Technical work:** This documentation set (done as of this session). No production backend.
**Historical/content work:** Initial July Crisis source register, chapter/scene outline draft.
**Output:** This documentation tree + `docs/delivery/phase-0-product-foundation.md` content deliverables.
**Manual test flow:** A reader unfamiliar with the project can read `README.md` → `AGENTS.md` → `docs/product/product-vision.md` and correctly describe what Chronicle is and isn't.
**Automated test requirements:** None (no code yet).
**Completion criteria:** Documentation tree exists and is internally consistent; source register has a first pass of sources; Phase 1 scope is concrete enough to plan.
**Explicitly deferred:** Any application code, any AI pipeline, any backend.
**Risks:** Content curation (source register) takes real historical-research time and could become a bottleneck if treated as an afterthought — track it as real work, not a checkbox.
**Claude Code responsibilities:** Author/maintain the documentation tree; do not begin Phase 1 implementation until the content foundation is credible enough to prototype against.
**Codex review responsibilities:** Phase Plan Review (`docs/delivery/codex-review-process.md` §A) — assess coherence, scope, and whether the roadmap below is over/under-engineered before Phase 1 implementation starts.

---

## Phase 1 — Static Explore Prototype

**Purpose:** Validate whether the combined narrative/timeline/map/graph/evidence format is understandable and compelling, before investing in backend complexity.
**Product assumption tested:** *Is exploring history in this combined format actually understandable, useful, and compelling?*
**User-facing capabilities:** A polished, frontend-only July Crisis investigation: 3–5 guided scenes, synchronized timeline, basic map, focused relationship (graph) view, visible evidence, mocked assistant.
**Technical work:** React/TS/Vite/Tailwind app; `Focus` state per `docs/design/map-timeline-graph-sync.md`; mock data modules shaped like the future API (`docs/architecture/frontend-architecture.md`); responsive layout per `docs/design/investigation-layout.md`.
**Historical/content work:** Curated mock content for 3–5 scenes, drawn from the Phase 0 source register, simplified but structurally honest (real evidence classifications, real disputed items — not placeholder Lorem Ipsum history).
**Output:** A deployable static frontend demonstrating the full synchronized experience end to end.
**Manual test flow:** Gate 1 first: a first-time reader completes the one-scene tasks in `phase-1-validation-plan.md`. Only after Gate 1 passes, expand to four scenes and run Gate 2 plus the full journey: follow the narrative, explore an event across timeline/map/graph, open evidence, and use the mock assistant to navigate the UI.
**Automated test requirements:** Vitest/RTL component tests per facet; one Playwright journey covering the manual test flow above; axe-core accessibility checks.
**Completion criteria:** Gate 1 and Gate 2 thresholds in `phase-1-validation-plan.md` pass and a dated validation report records the proceed decision; all manual flow steps work without a backend; loading/empty/failure states exist for each facet; implemented surfaces pass the specified automated accessibility checks and logged manual keyboard/screen-reader passes.
**Explicitly deferred:** Any backend, persistence, live AI, authentication, full 5-week event coverage (3–5 scenes only).
**Risks:** Mock data quality — if it's not representative of real historical complexity, Phase 1 validates the wrong thing. Scene selection must include at least one genuinely disputed relationship and one multi-actor "known at the time" moment.
**Claude Code responsibilities:** Implement per `docs/design/*` and `docs/architecture/frontend-architecture.md`; do not start Phase 2 backend work until this phase's completion criteria are met and reviewed.
**Codex review responsibilities:** Feature Diff Review (`docs/delivery/codex-review-process.md` §C) on the implementation; Historical Feature Review (§D) checking that mock content still respects uncertainty/citation/precision rules despite being "just mock data."

---

## Phase 2 — Seeded Full-Stack Investigation

**Purpose:** Stand up the real backend/data model and prove Phase 1's UI can run on real persisted data.
**Product assumption tested:** Does the domain model (`docs/architecture/domain-model.md`) actually support the UX validated in Phase 1 without distortion?
**User-facing capabilities:** The validated four-scene Phase 1 experience, now backed by a real API and database. Expansion beyond those scenes is separately planned content work and is not allowed to make Phase 2 completion conditional or ambiguous.
**Technical work:** FastAPI + PostgreSQL + SQLAlchemy + Alembic per `docs/architecture/backend-architecture.md`; typed OpenAPI contract; Docker Compose local setup; global Source/Document/Passage tables that do not require an Investigation foreign key; versioned NarrativeBlocks linked to reviewed records; seed script loading curated content with correct provenance/review fields per `docs/architecture/provenance-and-review.md`.
**Historical/content work:** Expand source register and scene coverage toward the full `july-crisis-scope.md` boundary; every seeded claim/relationship must actually reach `reviewed` status per `docs/research/validation-status.md`, not just be plausible-looking.
**Output:** Full-stack app runnable via `docker compose up`, serving real persisted July Crisis data through the Phase 1 UI (migrated from mock data source to live API).
**Manual test flow:** Fresh clone → `docker compose up` → same manual test flow as Phase 1, now against the real API; verify a public/unauthenticated request cannot retrieve any non-reviewed content (there shouldn't be any yet, but the filter must be provably active).
**Automated test requirements:** pytest suite per service; the review-status/visibility contract tests from `provenance-and-review.md`; a persistence test for a Source with no Investigation link; narrative evidence-dependency and immutable-revision tests; Playwright journey re-run against the live stack.
**Completion criteria:** Docker Compose stack runs clean from a fresh clone; all Phase 1 UI functionality works against real data; contract tests for public-read filtering pass.
**Explicitly deferred:** Live extraction/AI agent, authentication/accounts, source upload.
**Risks:** Domain-model/UX mismatch discovered late — mitigate by reviewing `domain-model.md` against the actual Phase 1 UI needs before writing migrations, not after.
**Claude Code responsibilities:** Implement backend, write seed data faithful to `validation-status.md`, migrate frontend off mock data.
**Codex review responsibilities:** Architecture Review (§B) — data-model consistency, provenance, permissions, local deployment reproducibility; Feature Diff Review (§C).

---

## Phase 3 — Synchronized Historical Exploration

**Purpose:** Fully realize the `map-timeline-graph-sync.md` contract and deepen historical-specific UX (known-at-the-time, actor perspectives, historical naming).
**Product assumption tested:** Does true cross-facet synchronization (not just co-located facets) meaningfully improve understanding vs. Phase 2's simpler wiring?
**User-facing capabilities:** Full story/timeline/map/graph/evidence synchronization with feedback-loop-safe focus updates; scene-based map navigation; focused local graph expansion (1–2 hop); actor/institution perspective switching; Known-at-the-Time prototype; historical place-naming support; URL-persisted state.
**Technical work:** Implement the full `Focus` contract with source-tagging; `PlacePeriodRecord` resolution (`spatial-architecture.md`); `KnownAtTime` querying and UI.
**Historical/content work:** Populate `KnownAtTime` records for the key July Crisis decision points; populate `PlacePeriodRecord`s for in-scope places.
**Output:** The investigation experience described in `docs/product/core-user-experience.md` items 1–8, fully realized.
**Manual test flow:** Deep-link to a specific focus via URL and confirm all facets render correctly on load (not just after interaction); switch actor perspective on a scene and confirm evidence/known-at-time content changes accordingly.
**Automated test requirements:** Focus-state unit tests (feedback-loop rule); Playwright deep-link tests; KnownAtTime query contract tests.
**Completion criteria:** All items in `core-user-experience.md` 1–8 are demonstrable end to end with real data.
**Explicitly deferred:** The assistant (Phase 4), source upload (Phase 5).
**Risks:** Graph readability at full scale — validate against `product-principles.md`'s "unreadable graph" rule with real July Crisis entity density, not just a small mock set.
**Claude Code responsibilities:** Implement per `design/map-timeline-graph-sync.md`; flag if real data reveals the sync contract needs revision (update the doc, don't silently diverge from it).
**Codex review responsibilities:** Feature Diff Review (§C); Historical Feature Review (§D) on KnownAtTime and perspective-switching correctness.

---

## Phase 4 — Evidence-Grounded Investigation Assistant

**Purpose:** Ship the assistant, grounded only in seeded reviewed data, for four polished question types.
**Product assumption tested:** Can a tightly bounded, grounded assistant meaningfully accelerate exploration without becoming an ungrounded chatbot?
**User-facing capabilities:** Assistant answering: explain this event/connection; compare these accounts/actors; what was known by this date; what is disputed or missing — each with citations and UI-navigating actions.
**Technical work:** AI orchestration layer per `docs/architecture/ai-agent-architecture.md` §3 (query planner → bounded tools → composition → verification pass); Ollama integration + mock provider for tests.
**Historical/content work:** None beyond what Phase 2/3 already seeded — the assistant must work with existing reviewed data, not require new content specifically for it (a deliberate constraint proving the grounding is real).
**Output:** Working assistant panel integrated into the Phase 3 UI.
**Manual test flow:** Ask each of the four supported question types and confirm: correct answer, correct citations (clickable, resolve to real evidence), correct UI navigation action, and a deliberately-asked unsupported/out-of-scope question gets an honest insufficient-evidence response rather than a fabricated one.
**Automated test requirements:** Deterministic-provider tests for query planning/tool routing/verification pass; a small hand-curated eval set (not unit-test-exact-match) for live-inference answer quality, run manually or in a non-blocking CI job.
**Completion criteria:** All four question types work end to end with real citations; verification pass demonstrably rejects/retries a fabricated-citation case in testing.
**Explicitly deferred:** The remaining six question types from `investigation-assistant.md`, source-upload-aware questions (Phase 5).
**Risks:** Grounding failures are the single highest-stakes risk in the whole roadmap (`AGENTS.md` §11) — do not relax the verification pass for demo polish.
**Claude Code responsibilities:** Implement the bounded pipeline exactly per `ai-agent-architecture.md`; do not let the assistant call anything outside the defined bounded tools.
**Codex review responsibilities:** Architecture Review (§B) on the AI orchestration layer; Historical Feature Review (§D) specifically on citation/grounding integrity.

---

## Phase 5 — Private Source Upload and Analysis

**Purpose:** Prove the private-workspace half of the Studio pipeline without touching public data.
**Product assumption tested:** Can a user meaningfully connect a new source to an existing investigation's structure without an editor in the loop yet?
**User-facing capabilities:** Private workspace, document upload, source metadata, text extraction, passage storage, private assistant comparison against the investigation, suggested relevant entities/events.
**Technical work:** Minimal auth sufficient for private workspaces (deferred elsewhere until now — scope tightly); upload handling with validation per `AGENTS.md` §7; extraction pipeline steps from `ai-agent-architecture.md` §1, landing in `proposed`/private state only.
**Historical/content work:** None (user-supplied).
**Output:** A user can upload a document and see, privately, how it might connect to the July Crisis investigation.
**Manual test flow:** Upload a real historical document (e.g., a public-domain July Crisis telegram text), confirm extraction proposals appear, confirm nothing becomes visible on the public investigation.
**Automated test requirements:** Upload validation/security tests (file type/size limits, no code execution of uploaded content); contract test proving private data never leaks to public endpoints.
**Completion criteria:** End-to-end private upload → suggested-connections flow works; zero public-data mutation confirmed by tests.
**Explicitly deferred:** Full Studio review UI (Phase 6), cross-investigation routing (Phase 8).
**Risks:** Security surface expands meaningfully here (first user-supplied content) — treat as the first mandatory security-review checkpoint.
**Claude Code responsibilities:** Implement with security requirements (`AGENTS.md` §7) as a hard gate, not an afterthought.
**Codex review responsibilities:** Pre-Release-style security review (§E, applied early) on the upload path specifically, before this phase is considered done.

---

## Phase 6 — Chronicle Studio Review Workflow

**Purpose:** Build the editorial review environment that makes Studio real.
**Product assumption tested:** Is the review workflow (`provenance-and-review.md` state machine) usable enough for a trusted editor to actually process sources at a reasonable pace?
**User-facing capabilities:** Structured extraction UI; event/actor/place/date/claim proposal review; approve/revise/reject/merge/dispute actions; entity resolution UI; audit history.
**Technical work:** Studio frontend tree (`frontend-architecture.md`); global source-library intake that permits sources with no Investigation link; review-queue backend endpoints; entity-resolution proposal tooling; reprocessing safety (re-running extraction on an already-reviewed document doesn't silently overwrite prior human corrections).
**Historical/content work:** Process a real batch of new July Crisis sources through the full pipeline as the first real editorial exercise.
**Output:** A working Studio review environment, exercised on real content.
**Manual test flow:** Upload a new source, walk it through classification → extraction → review → publish, confirm it becomes visible on the public investigation only after explicit approval.
**Automated test requirements:** State-machine transition tests (`provenance-and-review.md`); reprocessing-safety regression test.
**Completion criteria:** A full source can go from upload to published public content entirely through the Studio workflow, with correct audit history.
**Explicitly deferred:** Cross-investigation impact review (Phase 8), publishing/versioning UI polish (Phase 9).
**Risks:** Editorial UX complexity — keep the first version to the minimum workflow that's actually usable, resist scope creep into a full CMS.
**Claude Code responsibilities:** Implement per `provenance-and-review.md`; keep Studio and Explore trees structurally separate.
**Codex review responsibilities:** Feature Diff Review (§C); Architecture Review (§B) on reprocessing safety and audit-history integrity.

---

## Phase 7 — Shared Evidence Network

**Purpose:** Demonstrate genuine entity/evidence sharing across investigations.
**Product assumption tested:** Does the domain model's investigation-agnostic entity design (`domain-model.md`) actually support a second investigation without rework?
**User-facing capabilities:** Canonical historical entities reused with different framing across two investigations; reusable sources/passages; investigation-specific presentation layers; public/private permissions; versioned evidence associations.
**Technical work:** Versioned `InvestigationPresentation` and evidence-linked `NarrativeBlock` implementation exercised for real; cross-investigation entity/source browsing; sources can remain unassigned until a relevant investigation exists.
**Historical/content work:** Stand up one additional connected investigation (small, deliberately scoped — e.g., a directly adjacent topic sharing at least one Person/Institution with July Crisis) — **not** an attempt to model broader history.
**Output:** Two investigations sharing real entities/evidence, each with its own narrative framing.
**Manual test flow:** Navigate to a shared entity from Investigation A, confirm it also appears correctly (with different framing) reachable from Investigation B.
**Automated test requirements:** Tests confirming a shared entity edit in one context doesn't corrupt the other investigation's presentation.
**Completion criteria:** Two working, connected investigations; no cross-investigation data corruption in tests.
**Explicitly deferred:** Full cross-investigation source routing UI (Phase 8).
**Risks:** Temptation to over-scope the second investigation — keep it deliberately small (`product-principles.md` item 10).
**Claude Code responsibilities:** Implement `InvestigationPresentation` fully; resist adding a third investigation "while we're at it."
**Codex review responsibilities:** Architecture Review (§B) on data-model consistency under real multi-investigation load.

---

## Phase 8 — Cross-Investigation Source Routing

**Purpose:** Automate (with human gate) surfacing new-source relevance across multiple investigations.
**Product assumption tested:** Is machine-proposed relevance classification (supporting/contradicting/contextual/duplicate) accurate/useful enough to save real editorial time?
**User-facing capabilities:** Investigation-impact analysis; proposed source relevance across investigations; supporting/contradicting/contextual/qualifying/duplicate/unrelated classification; evidence-linked narrative revision proposals; human editorial approval; explicitly no silent public updates.
**Technical work:** `ImpactReview` and `NarrativeRevisionProposal` pipeline (`source-to-narrative-enrichment.md`) fully implemented and wired to the two investigations from Phase 7.
**Output:** A new source uploaded once correctly proposes evidence and narrative impact on every relevant investigation while remaining available in the global library if it is unrelated to current investigations.
**Manual test flow:** Upload a source relevant to both investigations, confirm separate ImpactReviews and narrative proposals are created, accept one and reject the other, and confirm neither public narrative changes before explicit publication.
**Automated test requirements:** Tests confirming ingestion, ImpactReview acceptance, and narrative-proposal acceptance never mutate the active public presentation; tests for an unassigned source and parallel conflicting accounts.
**Completion criteria:** Cross-investigation routing demonstrably works end to end on the two-investigation testbed.
**Explicitly deferred:** Scaling to more than two investigations (validate the mechanism, don't stress-test breadth yet).
**Risks:** Classification accuracy — track false-positive/negative rate on the small testbed honestly rather than presenting it as solved.
**Claude Code responsibilities:** Implement the pipeline; instrument classification accuracy tracking.
**Codex review responsibilities:** Historical Feature Review (§D) on whether classification correctly represents supporting vs. contradicting vs. contextual distinctions.

---

## Phase 9 — Publishing and Contribution

**Purpose:** Complete the authoring loop — scene/timeline/map editing and full editorial publishing UX.
**User-facing capabilities:** Investigation authoring; scene creation; timeline and map editing; evidence review; editorial workflow; published Explore experience; version history and rollback.
**Technical work:** Studio authoring UI for versioned NarrativeBlocks and the presentation layer; evidence-dependency display; atomic publication and rollback building on immutable revisions.
**Output:** An editor can author/edit/publish investigation presentation entirely through Studio, with working rollback.
**Manual test flow:** Edit a published scene, publish, then roll back, confirming the public Explore view reflects each state correctly.
**Automated test requirements:** Rollback correctness tests.
**Completion criteria:** Full author→publish→rollback loop works without direct database intervention.
**Explicitly deferred:** Multi-editor concurrent-editing conflict resolution (flag as a risk if it becomes relevant, don't build speculatively).
**Claude Code responsibilities:** Implement authoring UI; ensure rollback is a true first-class operation, not a manual data fix.
**Codex review responsibilities:** Feature Diff Review (§C); Pre-Release Review (§E) dry run on the full authoring loop.

---

## Phase 10 — Evaluation and Portfolio Release

**Purpose:** Stabilize, evaluate, and package Chronicle for portfolio presentation.
**User-facing capabilities:** Stable seeded public demo; full local version; evaluated assistant; historical-limitations report; architecture documentation; demo video.
**Technical work:** Performance pass, security checks, stale-documentation cleanup.
**Output:** Public demo + case study materials.
**Manual test flow:** A fresh reviewer follows README setup from a clean environment successfully.
**Automated test requirements:** Full test suite green; a documented, run assistant-quality eval report (not just unit tests).
**Completion criteria:** Demo is stable under normal use; documentation matches actual shipped behavior; honest limitations report exists.
**Claude Code responsibilities:** Final polish pass, documentation reconciliation.
**Codex review responsibilities:** Pre-Release Review (§E) in full — clean-environment setup, security-sensitive flow testing, primary user journeys, stale-doc detection, interview-credibility check.
