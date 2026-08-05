# Investigation Layout

> **Superseded as the default layout starting Phase D.** This document describes the article-first layout Phases 1-3/A-C actually built (`InvestigationLayout.tsx`) and which now ships as **Inspector** mode — still accurate for that mode, not deleted. The default Explore presentation is the map-first workspace: persistent map canvas, docked (desktop, `~360-420px`, resizable/collapsible)/bottom-sheet (mobile) assistant panel with Ask/Explore/Evidence/Sources tabs — not the "floating entry point, opens as overlay" assistant described below. See `docs/product/map-first-workspace-instructions.md` §7-9 for the current default layout and `docs/decisions/ADR-002-map-first-workspace.md` for the decision record.

## Primary Layout (Desktop) — Inspector mode

A persistent-but-collapsible layout, not a modal-heavy one: narrative takes primary reading width; timeline is a persistent strip (top or bottom); map and graph share a secondary region the user can toggle between (not both crammed on-screen at once, to avoid the "unreadable graph" failure mode in `docs/product/product-principles.md`); evidence opens as a panel driven by selection, not a permanent quarter of the screen.

```text
┌───────────────────────────────────────────────────────────┐
│ Investigation header (title, scene progress)                │
├───────────────────────────────────────────────────────────┤
│ Timeline strip (always visible, current position marked)     │
├───────────────────────────────┬─────────────────────────────┤
│                                 │  Map  |  Graph  (toggle)    │
│  Narrative (primary reading)    │                             │
│                                 ├─────────────────────────────┤
│                                 │  Evidence panel (contextual) │
└───────────────────────────────┴─────────────────────────────┘
        [ Assistant: floating entry point, opens as overlay ]
```

## Primary Layout (Mobile/Narrow)

Facets stack rather than split-pane; narrative is default view, with a persistent bottom tab bar to switch to timeline/map/graph/evidence, each still reflecting the same shared focus state. The assistant remains a floating entry point. Map/graph interactions are simplified (fewer simultaneous nodes/pins) rather than shrunk illegibly — see `docs/design/accessibility.md` and `docs/architecture/frontend-architecture.md` responsive testing requirement.

## Scene-Driven Map/Graph

Map and graph don't show "everything" by default — they show what's relevant to the current scene/focus, consistent with `docs/product/product-principles.md`'s rule against unreadable graphs and redundant map views. Zooming out to "the whole investigation" is an explicit user action (e.g., an "overview" toggle), not the default state.

## States

Every facet defines, from Phase 1 onward: loading state, empty state (e.g., no evidence yet reviewed for this focus — shown honestly, not hidden), and failure state (e.g., assistant couldn't ground an answer — shown as a clear message, not a silent fallback to ungrounded text). This is a Phase 1 requirement, not deferred polish (`AGENTS.md` §10, `docs/product/product-principles.md` MVP definition).

## Deferred

- Fully custom per-investigation layouts (the layout is investigation-agnostic; content varies, structure doesn't, until a second investigation's needs prove otherwise in Phase 7).
- Print/export layouts.
