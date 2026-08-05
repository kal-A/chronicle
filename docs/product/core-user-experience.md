# Core User Experience

> This document defines the investigation-canvas capabilities. The generation-first request/scope/workflow experience that now precedes the canvas is defined in `generation-first-user-experience.md`. Starting Phase D, the canvas itself is map-first (persistent map + docked/sheet assistant panel + lenses), with items 1/3/6/7/8 below primarily surfaced through the panel's Explore/Evidence tabs or the Inspector rather than a single scrolling article — see `docs/product/map-first-workspace-instructions.md`.

Chronicle's value proposition is defined by ten things a user should be able to do that static articles, generic chatbots, and ordinary timelines don't do well. Every feature should map back to at least one of these.

1. **Follow a complex event through a guided experience.** A narrative spine (chapters/scenes) that a reader with no prior background can follow start to finish.
2. **Move between narrative, timeline, map, graph, and evidence without losing context.** Selecting something in one view updates the others; there's no "leaving the investigation" to look something up.
3. **Select an event, decision, actor, institution, or place and see how it fits into the wider system.** A focused local graph expansion from any entity, not a single global hairball.
4. **Compare different perspectives and accounts.** See the same event from more than one actor's or historian's vantage point.
5. **Ask what specific actors or institutions knew by a given date.** A first-class "known at the time" reconstruction, not an implicit assumption that everyone had the same information.
6. **Trace a historical connection through evidence.** Follow a claimed relationship back to the specific passages that support (or dispute) it.
7. **Inspect supporting, opposing, or incomplete evidence.** Evidence panels show what's there and what's missing, not just a citation count.
8. **See where an interpretation is debated.** Disagreement between sources/historians is a first-class, visible state, not smoothed over.
9. **Ask an assistant questions grounded in the current investigation.** Not a general chatbot — answers are scoped to reviewed data in the current investigation and cite it.
10. **Add a source privately and see where it may connect** to the investigation or the wider historical database (Phase 5+; the read-side of this — "here's what this source might relate to" — is a Studio-adjacent capability that must not corrupt public data, see `explore-and-studio.md`).

These ten map onto the phased roadmap in `docs/delivery/development-phases.md`: 1–3 and 6–8 are largely Explore-side (Phases 1–3), 5 and 9 need the assistant (Phase 4), 10 needs Studio infrastructure (Phase 5+).
