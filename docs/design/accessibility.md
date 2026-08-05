# Accessibility

Accessibility is a Phase 1 requirement, not a later audit pass (`AGENTS.md` §8 / product-principles MVP definition).

## Standards

Target WCAG 2.2 AA as the baseline for all Explore surfaces. Studio (Phase 6+, internal/trusted-user tooling) targets the same baseline but may accept minor gaps in highly specialized authoring widgets if explicitly documented as a known limitation.

## Specific Requirements by Facet

- **Narrative** — standard semantic HTML reading flow; heading hierarchy matches chapter/scene structure; images/figures have real alt text describing historical content, not filenames.
- **Timeline** — keyboard-navigable (arrow keys move between events/scenes); each timeline marker has an accessible name including date and event title, not just a visual dot.
- **Map** — every pin/region reachable via keyboard and screen-reader accessible list view as an alternative to the visual map (a map-only interaction is not sufficient — provide a parallel list of "active locations" for the current focus).
- **Graph** — same principle as map: the graph is a visual convenience over a relationship structure that must also be reachable as an accessible list (e.g., "relationships involving X" list view alongside the Cytoscape canvas).
- **Evidence panel** — passages/citations are real readable text (not rendered-as-image scans without a text alternative); disputed/uncertain status is conveyed with text, not color alone.
- **Assistant** — responses are screen-reader announced (live region), and any UI action the assistant triggers (focusing the map, etc.) is also stated in the text response so it's not a purely visual-only effect.

## Color & Motion

- Uncertainty/dispute status (`interaction-principles.md` #4) is never conveyed by color alone — pair with icon/label/pattern.
- Respect `prefers-reduced-motion` for facet-sync transitions (map easing, graph re-layout) — provide an instant-jump alternative.
- Maintain AA contrast ratios across both the default and any dark-mode theme, if one is added.

## Testing

- Automated: axe-core (or equivalent) integrated into the Vitest/RTL component suite and/or Playwright runs, catching regressions on every PR, not just at phase boundaries.
- Manual: at minimum one full keyboard-only pass and one screen-reader pass (e.g., NVDA or VoiceOver) per phase that ships new UI, logged in that phase's manual test flow (`docs/delivery/development-phases.md`).

## Map-First Workspace Additions (Phase D)

- **Panel resize/collapse** — the docked panel's divider is a keyboard-operable `role="separator"` (focusable, arrow-key adjustable, with a documented reset/collapse/reopen shortcut set); focus moves to the collapse toggle on collapse and back to the panel on reopen (`docs/product/map-first-workspace-instructions.md` §8.1).
- **Bottom sheet** (mobile/tablet-portrait) — collapsed/half/expanded states are keyboard- and screen-reader-operable, not gesture-only; the drag handle has an accessible name and state (`docs/product/map-first-workspace-instructions.md` §9.1).
- **Lenses** — every lens has a required text-fallback equivalent (an ordered list of what the lens currently shows, e.g. a numbered sequence with dates), not just a visual map/graph state (`docs/product/map-first-workspace-instructions.md` §17.1); this is the same "canvas is a progressive enhancement, the accessible list is the real interaction" pattern already implemented for `MapView`'s place list and `GraphView`'s claims/relationships list — extended to every lens, not a new pattern.
- **Reduced motion** — this is the first real implementation of `prefers-reduced-motion` in this codebase (sheet transitions, lens transitions, any map fly-to); prior facet-sync "easing" described above was never actually gated on it.

## Explicitly Deferred

- Full WCAG AAA compliance.
- Alternate-language/localized accessibility content (tied to the multi-language deferral in `domain-model.md`).
