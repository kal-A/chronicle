# Frontend Architecture

## Stack

React + TypeScript + Vite, Tailwind CSS for styling, TanStack Query for server state, Cytoscape.js for the systems graph, MapLibre GL JS for the map, PDF.js where source documents need in-browser rendering. Vitest + React Testing Library for unit/component tests, Playwright for end-to-end user journeys.

## Structure Principle: Package-Driven Investigation Canvas

The frontend accepts a validated, supported-version `GeneratedInvestigation` package, normalizes it, and renders a progressive investigation canvas. Narrative, timeline, map, graph, and evidence remain synchronized through a single Focus state. The renderer contains no event-specific imports or generated code.

**Phase D update (map-first workspace, see `docs/decisions/ADR-002-map-first-workspace.md`):** this principle is extended, not replaced. The map becomes the persistent primary canvas with a docked/bottom-sheet assistant panel beside it, driven by an optional `InvestigationExperiencePlan` and a lens registry; the original article-first narrative/evidence/numbered-graph renderer is preserved as an "Inspector" mode rather than deleted. The single shared Focus state remains the synchronization mechanism for both the workspace and Inspector — no second, parallel selection system.

```text
src/
  features/
    generation/           # request, scope approval, workflow/report UI (pre-AI-first roadmap;
                          # superseded by the Phase E-K AI-core sequence, see
                          # docs/decisions/ADR-003-llm-agent-system-is-product-core.md)
    investigation/        # package loader + synchronized canvas/facets
      narrative/           # Inspector-hosted
      timeline/            # shared base; workspace/timeline/ extends it
      map/                 # shared base; workspace/canvas/ extends it
      graph/               # Inspector-hosted (numbered claim/relationship graph)
      evidence/            # Inspector-hosted (full evidence/provenance view)
      workspace/           # Phase D: map-first shell, docked/sheet panel, lenses
      inspector/           # Phase D: rehosts narrative/evidence/graph as a mode
      assistant/           # typed package/corpus tools (Phase E6 — real Ask-panel
                          # integration, replacing workspace/panel/AskTab.tsx's
                          # placeholder; docs/ai-core-instructions/05_PHASE_E_AI_CORE_IMPLEMENTATION_PLAN.md)
    studio/                # later review/enrichment UI
  shared/
    api/                   # typed API client generated/derived from backend OpenAPI schema
    ui/                    # design-system components
    state/                 # focus/selection state, URL sync
  app/                     # routing, providers, top-level layout
```

## State & URL

The current focus (selected entity/event/time-range/scene) is persisted to the URL so a specific view is shareable/bookmarkable and back/forward navigation works as users would expect — this is called out explicitly in the product instructions ("strong state and URL persistence," Phase 3) and should be designed in from Phase 1, not retrofitted.

## Data Fetching

Phase B loads versioned golden JSON through a validating package repository. Phase C loads CLI artifacts through the same boundary. Later TanStack Query calls a typed FastAPI contract. Zod guards the interchange boundary; Pydantic owns backend stage/domain validation. Shared golden fixtures detect drift.

## Golden Fixture

The Blank Cheque content moves from a TypeScript module to `fixtures/blank-cheque.golden-investigation.json`. Fixture-specific assertions remain in fixture tests; generic renderer/provider code must not contain July Crisis constants.

## Testing Requirements

- Component tests (Vitest + RTL) for each facet component in isolation.
- Playwright journeys for: opening an investigation, following the guided narrative, cross-navigating via selection between facets, asking the assistant a question and having it navigate the UI.
- Accessibility checks as part of component tests where feasible (see `docs/design/accessibility.md`), not deferred to a separate audit phase.

## Explicitly Deferred

- Component library abstraction beyond what's needed (no premature design-system package).
- Offline/PWA support.
- Studio UI (Phase 6+), kept in a separate `features/studio/` tree from day one so it doesn't entangle with Explore.
