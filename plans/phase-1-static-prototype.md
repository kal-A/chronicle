# Phase 1 Plan — Static Explore Prototype

> **Superseded after Plans 0–5.** Preserve the completed prototype as the Blank Cheque golden fixture. Do not execute conditional scene expansion; follow `docs/delivery/ai-first-pivot-plan.md`.

## Objective

Build and validate one polished frontend-only Chronicle Explore scene before expanding to the remaining three scenes. The first slice demonstrates whether readers can move among narrative, timeline, map, focused graph, and evidence while correctly understanding uncertainty.

## Scope and Gate

- **First slice:** Scene 2, “Vienna and Berlin: The Blank Cheque.”
- **No backend, database, auth, upload, live AI, or political-border polygons.**
- **Gate 1:** Stop after the one-scene implementation, run automated/manual checks, and conduct the user test in `docs/delivery/phase-1-validation-plan.md`.
- **Expansion:** Implement Scenes 1, 3, and 4 plus the scripted assistant only after Gate 1 passes or a revised interaction is retested successfully.

## Planned Technical Choices

- React + TypeScript + Vite.
- Tailwind CSS for styling.
- React Router URL search parameters for focus persistence and browser navigation.
- TanStack Query with a static asynchronous data provider so loading/failure behavior is real without a backend.
- MapLibre GL JS with a border-suppressed, explicitly labelled orientation base or local simplified background.
- Cytoscape.js for the focused graph, paired with an accessible relationship list.
- Vitest + React Testing Library + axe-core; Playwright for the user journey.
- npm initially, minimizing bootstrap prerequisites. Runtime/tool versions are pinned in repository configuration when scaffolding occurs.

## Plan 0 — Historical Content Fixture Gate

**Files:**

- `src/content/july-crisis/scene-blank-cheque.*` (created during implementation)
- `docs/research/july-crisis-source-register.md`
- `docs/research/validation-status.md`

**Tasks:**

1. Extract exact, locator-bearing passages from `jc-src-001` and `jc-src-002`.
2. Acquire and extract two materially different specialist interpretations.
3. Record Document edition/translation metadata, Passage locators, EvidenceLink roles, temporal/geographic scope, direct/inferred status, classification, limitations, and owner-review notes.
4. Mark the fixture `prototype-curated`, not `reviewed`, until the review standard is completed.

**Verification:** Every displayed material claim resolves to a fixture Passage and Source; intentionally deleting a supporting link fails schema validation.

## Plan 1 — Walking Skeleton and Quality Harness

**Owned paths:** root frontend configuration, `src/app/`, `tests/`, `.github/workflows/` if CI is included in this slice.

**Tasks:**

1. Scaffold the Vite React/TypeScript application without removing documentation.
2. Add lint, typecheck, unit-test, build, and Playwright commands.
3. Add a minimal app shell and investigation route.
4. Add Vitest/RTL/axe setup and a Playwright smoke test.
5. Add `.gitignore`, `.env.example` only if environment configuration exists, and README setup commands.

**Verification commands:** `npm run lint`, `npm run typecheck`, `npm test -- --run`, `npm run build`, and the documented Playwright command.

## Plan 2 — Versioned Domain Contract and Static Provider

**Owned paths:** `src/features/investigation/model/`, `src/features/investigation/data/`, `src/content/`.

**Tasks:**

1. Define runtime-validated types for HistoricalDate, Source, Document, Passage, Claim, Relationship, EvidenceLink, PlacePeriodRecord, NarrativeBlock, Scene, and Focus. Source must not require an Investigation ID; every material NarrativeBlock statement references reviewed/prototype-curated records.
2. Keep `reviewStatus`, `visibility`, `evidenceClassification`, and precision fields required and without certainty-implying defaults.
3. Implement an asynchronous static provider with deterministic success, empty, and failure modes.
4. Validate content fixtures at startup/test time and reject unsupported claims.

**Tests:** schema rejection for missing evidence classification, missing supporting EvidenceLink, materially assertive narrative without reviewed/prototype-curated record references, invalid precision, invalid time bounds, and private/proposed content entering a public fixture; acceptance of an unassigned Source with temporal/geographic coverage.

## Plan 3 — Central Focus and URL Contract

**Owned paths:** `src/features/investigation/focus/`, investigation route tests.

**Tasks:**

1. Implement the discriminated Focus contract and source-tagged updates.
2. Serialize focus deterministically to URL search parameters.
3. Support reload, deep links, browser back/forward, invalid-ID fallback, and preservation of narrative position.
4. Prevent a facet from re-running its own expensive focus reaction.

**Tests:** round-trip serialization, invalid URL handling, feedback-loop suppression, history navigation, and scene-to-time-range projection.

## Plan 4 — One-Scene Synchronized Experience

**Owned paths:** `src/features/investigation/narrative/`, `timeline/`, `map/`, `graph/`, `evidence/`, shared investigation layout.

**Tasks:**

1. Implement the responsive desktop/mobile layout.
2. Render Scene 2 narrative and two to three timeline events.
3. Render Vienna/Berlin at city precision without political-border implication.
4. Render a three-to-five-node local relationship graph with evidence classifications visible in text and styling.
5. Render Claim → EvidenceLink → Passage → Document → Source traceability in the evidence panel.
6. Make selection in each facet update every other facet through the central Focus contract.
7. Provide explicit loading, empty, and failure states per facet.

**Tests:** component behavior per facet, synchronized selection, evidence resolution, honest uncertainty labels, city precision, responsive navigation, and reduced-motion behavior.

## Plan 5 — Accessibility and Gate 1 Journey

**Owned paths:** facet components, accessible map/graph lists, Playwright tests, validation report template.

**Tasks:**

1. Provide keyboard-accessible timeline, location list, relationship list, evidence controls, and visible focus states.
2. Provide semantic headings, accessible names, live status where necessary, non-color uncertainty cues, and reduced-motion behavior.
3. Run axe checks and manual keyboard/NVDA review.
4. Automate the Gate 1 happy path in Playwright.
5. Create `docs/delivery/validation/phase-1-gate-1-template.md` for human study results.

**Checkpoint:** Present the running one-scene build and automated/manual results to Kamal. Conduct the five-person Gate 1 test. Record `proceed`, `revise`, or `stop`.

## Plan 6 — Conditional Expansion After Gate 1

Execute only after a recorded `proceed` decision.

1. Apply validated patterns to Scenes 1, 3, and 4.
2. Add the scripted assistant as a navigation affordance for supported fixture questions; unsupported questions produce an explicit insufficient-evidence response.
3. Run Gate 2 with five additional participants.
4. Reconcile documentation and prepare the Codex phase handoff.

## Acceptance Criteria

- Gate 1 and Gate 2 meet the thresholds in `docs/delivery/phase-1-validation-plan.md`.
- Every displayed significant claim is passage-traceable and prototype status is visible.
- Uncertainty, dispute, temporal distinctions, and city-level precision are never conveyed through color or coordinates alone.
- Focus is URL-persisted and synchronized without feedback loops.
- Loading, empty, and failure states are demonstrated and tested.
- Automated tests, build, keyboard pass, screen-reader pass, and manual user journey pass.
- README and delivery/status documents match actual behavior.
- No backend or deferred Phase 2+ infrastructure is introduced.

## Known Risks

- Historical passage acquisition may delay fixture completion; do not fill gaps with model knowledge.
- Map tile/style choice may introduce modern borders; prefer a border-suppressed local style for Gate 1.
- Cytoscape canvas accessibility requires the parallel relationship list to be a first-class interaction, not hidden fallback content.
- Five-person formative tests reveal major usability problems but do not establish broad market demand; describe conclusions accordingly.
