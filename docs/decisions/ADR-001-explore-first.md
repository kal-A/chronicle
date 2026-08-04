# ADR-001: Explore-First Sequencing

**Status:** Superseded by `ADR-ai-generation-is-the-product-core.md`

## Context

Chronicle has two long-term product surfaces: Chronicle Explore (public reading/investigation experience) and Chronicle Studio (authoring/editorial review environment for processing sources into the shared evidence network). Both are necessary for the long-term vision, and Studio is in some sense a prerequisite for Explore to ever scale beyond hand-curated seed content. A plausible alternative sequencing would build Studio first, on the theory that content-authoring tooling is the real bottleneck to a rich product.

## Decision

Build Chronicle Explore first (Phases 1–5), Chronicle Studio second (Phases 6+). The central product bet — that a combined narrative/timeline/map/graph/evidence format is genuinely more understandable and compelling than existing historical-content formats — is unproven and must be validated with real users before investing in authoring infrastructure that only pays off if that bet is correct.

## Consequences

- Phases 1–5 rely entirely on hand-curated seed content (source register + manual curation), which is real historical-research effort, not a shortcut — see `docs/delivery/risks-and-open-questions.md`.
- The Phase 2 domain model must be designed to support Studio's eventual needs (provenance, review-status, entity/source separation) even though no Studio UI exists yet to exercise them — this is called out explicitly in `docs/product/explore-and-studio.md` and `docs/architecture/domain-model.md` so the Explore-first sequencing doesn't quietly become "Explore-only" architecture that needs a rewrite at Phase 6.
- If Phase 1 invalidates the combined-format bet, the roadmap after Phase 1 should be revisited before continuing — this sequencing is specifically designed to make that pivot point early and cheap.

## Alternatives Considered

- **Studio-first:** rejected — front-loads authoring-tool investment before knowing whether the reading experience it would feed is actually valuable; higher cost if the core bet fails.
- **Parallel build of both surfaces:** rejected — violates the vertical-slice development model (`AGENTS.md` §8) and splits focus across two large, interdependent surfaces before either is proven.
