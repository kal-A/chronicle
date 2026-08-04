# Interaction Principles

1. **Selection is the primary interaction.** Clicking/tapping an entity, event, place-pin, graph node, or evidence item sets the shared focus and updates every other facet. This is the single most important interaction in the product and should be implemented once, centrally (`docs/architecture/frontend-architecture.md`), not re-implemented per facet.
2. **Never lose the reader's place.** Switching facets, opening the assistant, or expanding evidence must never reset narrative scroll position or lose current focus — state is centralized and URL-persisted (`docs/architecture/frontend-architecture.md`).
3. **Depth is progressive, not modal-heavy.** Prefer inline expansion (evidence panel growing, a detail drawer) over full-screen modals that interrupt the synchronized view. Modals are reserved for genuinely interrupting actions (Phase 5+ upload flow), not for reading history.
4. **Uncertainty is visible, not hidden in tooltips only.** Disputed/speculative/insufficient-evidence relationships get a distinct, consistent visual treatment (not just a hover tooltip) across timeline, map, and graph — see `AGENTS.md` §12.
5. **The assistant is an accelerator, not a gate.** Every capability the assistant provides (focus timeline, open evidence, compare accounts) must also be directly reachable by manual interaction. A user who never opens the assistant should be able to do everything.
6. **Assistant answers are inspectable, not just readable.** Every citation in an assistant answer is clickable and opens the actual evidence/passage it references (`docs/product/investigation-assistant.md`) — never a bare citation-shaped string.
7. **Honest empty and insufficient states.** "No reviewed evidence yet" and "the evidence doesn't establish this" are first-class, designed states, not degraded fallbacks (`docs/product/product-principles.md`).
8. **Keyboard and motion discipline.** All selection interactions must be keyboard-reachable; animation on facet-sync transitions is used to *preserve* spatial continuity (e.g., map easing to a new location) not for decoration — see `accessibility.md` for reduced-motion handling.

## Anti-Patterns to Avoid

- A "chat box that does everything" — violates principle 5 and `docs/product/product-principles.md`.
- Full-page navigations between facets — violates principle 2.
- Confidence-flattening UI (e.g., rendering disputed and settled relationships identically) — violates principle 4 and `AGENTS.md` §3/§12.
- Graph views with no filtering by current focus — violates principle 3 and the product-principles "unreadable graph" rule.
