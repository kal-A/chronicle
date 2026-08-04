# Frontend Architecture

## Stack

React + TypeScript + Vite, Tailwind CSS for styling, TanStack Query for server state, Cytoscape.js for the systems graph, MapLibre GL JS for the map, PDF.js where source documents need in-browser rendering. Vitest + React Testing Library for unit/component tests, Playwright for end-to-end user journeys.

## Structure Principle: Package-Driven Investigation Canvas

The frontend accepts a validated, supported-version `GeneratedInvestigation` package, normalizes it, and renders a progressive investigation canvas. Narrative, timeline, map, graph, and evidence remain synchronized through a single Focus state. The renderer contains no event-specific imports or generated code.

```text
src/
  features/
    generation/           # request, scope approval, workflow/report UI (Phase I)
    investigation/        # package loader + synchronized canvas/facets
      narrative/
      timeline/
      map/
      graph/
      evidence/
      assistant/           # typed package/corpus tools (Phase J)
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
