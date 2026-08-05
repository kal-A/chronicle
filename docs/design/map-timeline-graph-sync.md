# Map / Timeline / Graph Synchronization Contract

This is the concrete interaction contract implied by `interaction-principles.md` #1 and `information-architecture.md`'s focus model. It exists so Phase 1's mock implementation and Phase 3's full implementation agree on the same contract without a rewrite.

**Phase D update:** this `Focus` contract (implemented as `FocusValue` in `src/features/investigation/model/focus.ts`) is extended, not replaced, by the map-first workspace — both the workspace and Inspector read/write the same shared focus. The workspace additionally introduces an **active lens** (Sequence/Positions/Knowledge/Systems/Sources/Uncertainty) as a second, orthogonal piece of state: focus selects *what*, the lens selects *which question the canvas is currently answering about it*. The already-defined-but-previously-unwired feedback-loop `source` tag this document specifies (§"Feedback-Loop Rule") gets its first real consumer in the workspace's timeline/map synchronization. See `docs/product/map-first-workspace-instructions.md` §10-12 and `docs/decisions/ADR-002-map-first-workspace.md`.

## Shared Focus State

```ts
type HistoricalDate =
  | { precision: "exact"; earliest: string; latest: string }
  | { precision: "approximate" | "range" | "disputed"; earliest: string; latest: string };

type Focus =
  | { kind: "scene"; sceneId: string }
  | { kind: "event"; eventId: string }
  | { kind: "entity"; entityId: string; entityType: EntityType }
  | { kind: "timeRange"; start: HistoricalDate; end: HistoricalDate };
```

Date strings use a documented proleptic-Gregorian ISO representation at the API boundary; they are not JavaScript `Date` objects. The paired bounds preserve approximate/range/disputed semantics and serialize deterministically into URLs. Phase 1 only needs dates in 1914, but it must use this shape rather than assuming every historical date is an exact timestamp.

One `Focus` value lives in centralized state (and the URL). Every facet subscribes to it; every facet's direct-interaction handlers write to it. No facet holds its own separate "selected thing" state that the others don't know about.

## Per-Facet Behavior on Focus Change

| Facet | On focus change, does |
|---|---|
| Narrative | Scrolls/highlights the relevant scene/paragraph if the focus originated elsewhere; does not auto-scroll when the focus originated from narrative scrolling itself (avoid feedback loops) |
| Timeline | Marks/centers the relevant date or range; if focus is an entity, highlights events involving that entity |
| Map | Eases camera to relevant place(s); if focus is a time range, filters visible pins to that range |
| Graph | Re-centers the focused node and expands its immediate local neighborhood (1–2 hops); does not attempt to render the whole investigation graph at once |
| Evidence panel | Loads evidence (claims/passages/relationships) for the current focus; shows the honest empty state if none exists yet |
| Assistant | Can read current focus as implicit context for a follow-up question ("what about this one") |

## Feedback-Loop Rule

A facet that *causes* a focus change does not need to re-react to the change it just caused (e.g., clicking a map pin updates focus; the map itself doesn't need to re-ease its camera in response to updating the same focus it just set). Implement via a "source" tag on focus updates (`{ focus, source: "map" | "timeline" | ... }`) so each facet can skip self-triggered reactions — this avoids jank and is worth deciding now rather than discovering it as a bug in Phase 3.

## Time-Range vs. Point Focus

Narrative/scene focus implies a time range (the scene's period) even though the user didn't set an explicit range — timeline/map/graph should treat scene focus as equivalent to the scene's associated time range for filtering purposes, not as a special case with no time semantics.

## Phase 1 Simplification

Phase 1's one-scene Gate 1 implementation uses URL-persisted focus from the start so browser back/forward and shareability are tested, but may use a simple in-memory data provider instead of a backend. It must implement the same `Focus` shape and source-tag feedback-loop rule, so Phase 2/3 are data-source and capability expansions rather than a state-contract redesign.
