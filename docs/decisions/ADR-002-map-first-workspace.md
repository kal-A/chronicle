# ADR-002: Map-First Investigation Workspace

**Status:** Accepted — 2026-08-04

## Context

Phases A-C established the generation-first product core: a versioned `GeneratedInvestigation` package contract, a generic single-scene renderer (persistent timeline strip, narrative reading column, a Map/Graph tab toggle, and an evidence panel, all synchronized through a shared `Focus` state), and a deterministic Python pipeline that now produces both mock and real curated packages. That renderer is article-first: the map is one of two tabs beside "Relationships," reachable only after reading into the narrative, and there is no persistent entry point for a conversational assistant.

Kamal supplied `docs/product/map-first-workspace-instructions.md` (preserved verbatim there), an additive product/UX correction: Chronicle should present as a conversational entry point that transforms into a map-first workspace — a persistent bounded historical map as the primary canvas, with a docked (desktop) or bottom-sheet (mobile) assistant panel beside it (Ask/Explore/Evidence/Sources tabs), driven by historical "lenses" and a new `InvestigationExperiencePlan` contract. This is a genuine architecture/experience-shape change, expensive to reverse silently, and meets this project's own bar (`docs/decisions/README.md`) for a recorded decision.

`docs/delivery/revised-development-phases.md` had already assigned **Phase D = "Real Discovery and Assessment"** (with Phases E-K following it) as the next lettered phase after Phase C. Inserting this work required either renumbering the existing roadmap or taking a non-conflicting label.

## Decision

1. **The map becomes the persistent primary investigation canvas**, not a tab beside a graph view. A docked, resizable panel (desktop) or an accessible bottom sheet (mobile/tablet-portrait) sits beside it, with Ask/Explore/Evidence/Sources tabs — reusing the existing WAI-ARIA tabs pattern already implemented in `InvestigationLayout.tsx`.
2. **The current article-first renderer (narrative/evidence/numbered-claim-graph) is preserved as "Inspector" mode**, not deleted. It remains the deep evidence/provenance/audit surface; the workspace's own Evidence tab is a new, shallower view.
3. **A new `InvestigationExperiencePlan` contract** (`MapScope`, `InvestigationLens`, `StorySequence`, `SystemPath`, contextual prompts, assistant actions) is added as an **optional, additive field** on `GeneratedInvestigation` — existing packages (`blank-cheque.golden-investigation.json`, `concert-of-europe.generated-investigation.json`) remain valid without modification until each is given a real plan.
4. **This work is inserted as the new Phase D in full** (not a "D0" sub-phase squeezed before the existing Phase D). The previously-lettered Phase D ("Real Discovery and Assessment") and everything after it shift down one letter each: D→E, E→F, F→G, G→H, H→I, I→J, J→K, K→L. `docs/delivery/revised-development-phases.md` reflects this; the source document's own internal "D0.1-D0.6"/"D1"/"D2-D5" sub-numbering (§20 of `map-first-workspace-instructions.md`) is retained as Phase D's own sub-plan sequencing, not the authoritative phase-letter mapping.
5. **The systems (graph) view splits in two**: a new labelled-node view (people/institutions/events/decisions/documents/places, readable edge verbs, evidence-strength encoded by line style plus text, never color alone) becomes the user-facing Systems lens; the existing numbered-claim-ID Cytoscape graph is retained, unchanged, as an Inspector-only "claim ledger" view.
6. **No free-floating/undocked panel mode** in this phase — only docked (desktop) and bottom-sheet (mobile/tablet-portrait), per the source document's explicit reasoning (map obstruction, focus-management complexity, discoverability).
7. Sequenced as six approved-individually sub-plans (D0.1 docs/ADR → D0.2 experience-plan contract → D0.3 workspace shell → D0.4 deterministic Concert of Europe experience plan → D0.5 initial Ask entry-surface prototype → D0.6 usability-gate test plan), mirroring how Phase C was sequenced as C0-C3.

## Consequences

- `docs/delivery/revised-development-phases.md`, `docs/architecture/system-overview.md`, `docs/architecture/frontend-architecture.md`, and `docs/architecture/generated-investigation-contract.md` all needed their Phase D-K cross-references updated to the new E-L lettering (done as part of this ADR's landing).
- Every future reference to "Phase D" in this codebase means the map-first workspace, not source discovery — source discovery is now Phase E.
- `src/features/investigation/{narrative,timeline,map,graph,evidence}/` are not deleted; they become Inspector's implementation and/or components the new `workspace/` tree wraps or extends. This avoids re-deriving already-tested, already-accessible interaction patterns (the ARIA tabs implementation, the `aria-hidden` canvas + accessible list pattern for both map and graph, the URL-as-source-of-truth Focus system).
- The already-defined-but-unwired feedback-loop/time-projection mechanism (`useFocusReaction.ts`, `projectFocusToTimeRange.ts`) finally gets a real consumer in the workspace timeline, rather than continuing to exist only as tested-but-dead code.
- `gate1-journey.spec.ts` and `InvestigationSync.test.tsx` — the two test files most tied to the current article-first shell — will need real rework during D0.3, not a silent pass-through.
- Historical-integrity discipline (AGENTS.md §3/§12) applies identically to lens content: every lens's `visibleX` arrays are generated/validated data, cross-referenced the same way scenes are today (`validate_generated_investigation`/`validateGeneratedInvestigation` rule additions), never client-side inference from raw scene data.

## Alternatives Considered

- **Keep "Phase D0" as a sub-phase squeezed between C and the existing D, without renumbering anything downstream.** Rejected: leaves a permanently confusing "D, then D0, then D again"-shaped index: `docs/decisions/README.md`'s intent, and the source document's own phrasing ("insert Phase D0... before live source-discovery work"), both point toward this work actually preceding Discovery in the primary sequence, not living in a parenthetical between C and D.
- **Give it an unrelated letter (e.g., Phase M), leaving D-K untouched.** Rejected: preserves numbering stability but produces a roadmap where phase letters no longer reflect execution order, which would be more confusing than a one-time cascading relabel.
- **Make `InvestigationExperiencePlan` required immediately**, forcing `blank-cheque` and `concert-of-europe` to be regenerated with a real plan before D0.2 is considered done. Rejected: unnecessarily blocks D0.2/D0.3 on content-authoring work; optional-and-additive lets the contract and hand-authored fixture plans land first, with the Concert pipeline's real plan following in D0.4.
- **Delete the numbered claim-graph and article-first renderer outright, replacing them entirely with the new views.** Rejected: throws away proven, accessibility-tested code and an audit-relevant view (the claim ledger) the new doc itself says should be preserved as Inspector, not discarded.
