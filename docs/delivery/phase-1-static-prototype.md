# Phase 1: Static Explore Prototype — Detail

See `development-phases.md` for the standard phase-summary fields. This document will hold the concrete implementation plan once Phase 1 begins — kept separate from the roadmap summary so it can grow without bloating `development-phases.md`.

## Preconditions (from Phase 0)

- Source register and four-scene outline drafted (`docs/research/july-crisis-source-register.md`, `docs/research/phase-1-scene-outline.md`).
- Scene 2 passage-level content gate completed and owner review recorded.
- Historical review standard and Phase 1 validation plan approved by Kamal.

## Scope Recap

Frontend-only. React/TS/Vite/Tailwind. Provisional mock data shaped by the documented domain contract. Gate 1 ships the synchronized narrative/timeline/map/graph/evidence experience for Scene 2, with URL-persisted focus and a border-suppressed map. The remaining scenes and mocked assistant follow only after Gate 1 passes.

## Implementation Plan

Not yet written — to be produced via Claude's planning-mode workflow (`CLAUDE.md`) once Phase 0 content preconditions are met, and stored in `plans/current-phase.md` when Phase 1 becomes active work. This document will be updated with the concrete task breakdown, affected-files list, and manual test walkthrough results as Phase 1 proceeds.

## Recommended First Vertical Slice (for planning reference)

The smallest complete slice that proves the synchronized-facet pattern end to end: **one scene**, with narrative text, 2–3 timeline events, 1–2 map locations, a small graph (3–5 nodes), and evidence for one claim — wired through the real `Focus` state contract (`docs/design/map-timeline-graph-sync.md`), not a simplified stand-in. Get this one scene fully synchronized and polished before replicating the pattern across the remaining 2–4 scenes; this de-risks the interaction contract before content volume makes mistakes expensive to fix.
