# Codex Phase Review Prompts

Exact reusable prompts for review types A, B, D, E (type C has its own template: `review-template.md`). Paste the relevant prompt to Codex along with the specified inputs.

---

## A. Phase Plan Review

**Inputs to provide:** `AGENTS.md`, `docs/product/product-vision.md`, `docs/product/product-principles.md`, `docs/delivery/development-phases.md`, `docs/delivery/risks-and-open-questions.md`.

**Prompt:**

> Review the Chronicle phase plan in `docs/delivery/development-phases.md` against the product vision and principles in `docs/product/`. Assess: (1) product coherence — does each phase build logically on the last without contradicting the product vision; (2) scope — is any phase too large to actually ship as described, or too small to be meaningful; (3) missing outputs — does any phase lack a clear runnable/testable artifact; (4) testability — can each phase's completion criteria actually be verified, or are they vague; (5) AI sequencing — is AI being introduced before the product value it depends on has been validated (per the Explore-first ADR, `docs/decisions/ADR-001-explore-first.md`); (6) overengineering — is the roadmap adding infrastructure/complexity a phase doesn't yet need; (7) historical-validation credibility — is the process in `docs/research/` and `docs/architecture/provenance-and-review.md` actually rigorous enough to support the product's historical-integrity claims, or does it wave its hands. Report findings as blocking / important / optional, per `.codex/review-template.md`'s structure.

---

## B. Architecture Review

**Inputs to provide:** `AGENTS.md`, `docs/architecture/*.md`, the current codebase diff or full tree for the phase under review.

**Prompt:**

> Review the Chronicle architecture — both the documents in `docs/architecture/` and (if provided) the actual implementation — for: (1) frontend/backend separation adherence; (2) domain-boundary consistency with `docs/architecture/domain-model.md`; (3) data-model consistency, including whether provenance/review-status fields are actually present and enforced, not just documented; (4) whether state transitions match the state machine in `docs/architecture/provenance-and-review.md`; (5) whether permissions/visibility filtering is provably applied at the query layer, not just intended; (6) whether local deployment (`docs/architecture/deployment.md`) actually reproduces from a clean environment; (7) unnecessary dependencies, especially any paid service not justified per `AGENTS.md` §5; (8) scaling assumptions that don't hold at real content volume (e.g., graph rendering, `docs/design/map-timeline-graph-sync.md`); (9) failure recovery — what happens when a review-status filter is missing on a new endpoint, or an AI provider call fails. Report as blocking / important / optional.

---

## D. Historical Feature Review

**Inputs to provide:** `AGENTS.md` §3/§12, `docs/research/historical-methodology.md`, `docs/architecture/provenance-and-review.md`, the diff/feature under review, and any content (claims, relationships, dates, places) it introduces or touches.

**Prompt:**

> Review this Chronicle feature for historical-integrity software behavior (not independent historical fact-checking — you are checking that the *software* enforces the rules Chronicle has set for itself, using the sources already cited in the content/code). Check: (1) are claims cited, with a traceable path to a source passage; (2) is uncertainty represented via a real `evidence_classification` field rather than defaulted or omitted; (3) are date types distinguished (event/report/sent/received/awareness time) where more than one could apply, rather than collapsed into a single date; (4) is location precision honestly rendered (no building-level implication from city-level evidence); (5) can disagreement between sources/historians be represented, or does the feature force a single account; (6) do modern geographic assumptions (present-day borders, present-day place names) leak into historical map/place views; (7) can a user actually trace evidence for a claim through the UI/API, or is it a dead end; (8) are unsupported claims structurally blocked from reaching a public endpoint, not just discouraged by convention. Report as blocking / important / optional. Remember: you are not the arbiter of historical truth — flag a claim as unsupported by its own cited sources, not as "wrong" by your own knowledge.

---

## E. Pre-Release Review

**Inputs to provide:** full repository access, `README.md` setup instructions, `AGENTS.md`, `docs/delivery/definition-of-done.md`.

**Prompt:**

> From a clean environment, follow `README.md`'s setup instructions exactly as written and note any step that fails or is missing. Run the full test suite and report results. Inspect security-sensitive flows per `AGENTS.md` §7 (upload handling if present, auth if present, public/private data boundaries). Walk the primary user journeys described in `docs/delivery/development-phases.md` for the current phase and confirm they work as documented. Identify any documentation that no longer matches actual behavior (stale docs). Identify any fragile demo behavior (things that work once but break on repeat use, or depend on undocumented local state). Finally, assess honestly: could this project's current state be explained credibly and specifically in a technical interview — is the architecture sound, is the historical-integrity story real rather than decorative, and are there any claims in the documentation that the code doesn't actually back up? Report as blocking / important / optional.
