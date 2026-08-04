# Information Architecture

## Top-Level Structure

```text
Home / Investigation index (Phase 2+; Phase 1 links straight into July Crisis)
  └─ Investigation (e.g., July Crisis of 1914)
       ├─ Narrative (chapters/scenes) — default entry point
       ├─ Timeline — synchronized with narrative position
       ├─ Map — synchronized with narrative position / selection
       ├─ Graph — focused local view driven by current selection
       ├─ Evidence panel — driven by current selection
       └─ Assistant — overlay/side panel, available from any facet
```

There is one navigational hierarchy (Investigation → facets), not five separate apps that happen to share a header. A user should never have to "leave" the investigation to change facets — facets are views onto one shared focus state, not separate routes that lose context (`docs/architecture/frontend-architecture.md`).

## Entry Point

The guided narrative (chapters/scenes) is the default entry point for a first-time reader — it's the "documentary" framing from `docs/product/product-vision.md`. Timeline/map/graph/evidence are equally capable entry points for a returning or more expert user (`docs/product/target-users.md` secondary persona), reachable directly via URL-persisted state, not buried behind the narrative.

## Selection / Focus Model

A single `focus` concept — an entity, event, decision, or time range — is the organizing unit of the IA. Every facet is a projection of the current focus:

- Narrative sets focus as the reader progresses through scenes.
- Timeline, map, and graph both *reflect* the current focus and let the user *change* it by interacting directly.
- Evidence panel always shows evidence for the current focus.
- Assistant answers can change the focus (`docs/product/investigation-assistant.md` — "answers are actions").

See `map-timeline-graph-sync.md` for the interaction contract this implies.

## Depth

Two levels of depth are always available from any focus: a compact summary (what's shown inline in timeline/map/graph) and a full detail view (evidence panel expansion, or a dedicated entity/event detail view for Phase 3+). Never force a full page navigation just to see one more layer of detail on the current focus.

## Studio IA (Phase 6+, sketched now to avoid future conflict)

Studio's IA is deliberately separate: Upload → Review Queue → Entity/Claim detail → Impact Review → Publish. It does not reuse Explore's facet-based IA, because authoring/reviewing is a task-oriented workflow, not an exploration experience — conflating the two IAs was explicitly flagged as a risk in `docs/product/product-principles.md` item 4.
