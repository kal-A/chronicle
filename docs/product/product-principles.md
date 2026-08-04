# Product Principles

These are the standing criteria used to evaluate any proposed feature, on both product and engineering grounds. See `CLAUDE.md` §"Critical Review Behavior" — every non-trivial feature request should be checked against this list before being built.

## Evaluation Checklist for Any Proposed Feature

1. **What user problem does it solve?** Trace it back to one of the ten core-user-experience capabilities in `core-user-experience.md`. If it doesn't map to one, question whether it belongs.
2. **Does an existing feature already solve it?** Prefer extending over adding a parallel mechanism.
3. **Does it make the product clearer, or more confusing?** A feature that adds a fourth way to see the same information is usually a net loss.
4. **Explore, Studio, or neither?** Misplacing a Studio (authoring) concern into Explore (reading) muddies the reading experience; the reverse under-serves editors. See `explore-and-studio.md`.
5. **Does it actually need an LLM?** Default to deterministic software (`AGENTS.md` §4). An LLM is justified only for genuinely ambiguous language/unstructured material, not for anything with a clear rule.
6. **Does it expand historical-validation requirements disproportionately to its value?** Every new claim type or relationship type adds review burden forever, not just once.
7. **Does it add disproportionate complexity?** Weigh implementation and maintenance cost against the marginal user value.
8. **Does it threaten the free-development constraint?** See `AGENTS.md` §5.
9. **Does it improve the portfolio story?** Chronicle exists partly to demonstrate rigorous product judgment and full-stack/AI systems capability to a technical audience — features that are impressive but hollow (or correct but invisible) both under-serve this.
10. **Can it actually be built and polished properly** in the time available, or does it produce another half-finished screen? Prefer doing less, completely.

## Standing Product Rules

- Treat the generation pipeline—not manually authored historical scenes—as the product core. New historical fixtures exist to validate generic contracts and evaluations, not to scale content by hand.
- Broad requests require scope approval. Unsupported domains and weak corpora produce partial results or abstention, never universal-history claims.
- Search metadata/snippets are discovery material, not evidence; generated synthesis can only cite structured claims with passage-level support.

- Push back on anything that turns chat into the entire product. The assistant is one access point among several (narrative, timeline, map, graph, evidence), not a replacement for the others.
- Push back on graph views that become unreadable "hairballs." A systems graph should always be a *focused, local* view driven by a selection, not a full unfiltered network dump.
- Don't create redundant map views — one geographic surface, contextualized by scene/period, not several competing map widgets.
- Don't introduce services or infrastructure a phase doesn't need yet.
- Don't overstate historical certainty anywhere in the UI — see `AGENTS.md` §3 and §12.
- Don't let unreviewed AI output reach a public surface.
- Don't try to model "all of history" immediately — one well-executed investigation beats ten shallow ones.
- Favor coherent UX polish over raw feature count at every phase gate.

## "MVP" Definition

MVP means the smallest coherent and credible product experience that demonstrates real value — not the fastest collection of partially working screens. Every phase in `docs/delivery/development-phases.md` must produce something usable and testable, with real (if narrow) loading/empty/failure states, not stubs.
