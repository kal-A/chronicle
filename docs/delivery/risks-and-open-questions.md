# Risks and Open Questions

## AI-First Pivot Risks

- **Renderer/schema drift.** Zod and future Pydantic models must share golden JSON contract tests.
- **Pipeline breadth before proof.** Do not adopt live providers, workers, embeddings, or databases before the deterministic mock pipeline renders end to end.
- **Discovery mistaken for evidence.** Metadata and snippets must remain outside claim support.
- **Source/rights fragility.** Provider availability, archive terms, OCR quality, and display rights can create partial results; failure and abstention are required product states.
- **Generated fluency masking corpus gaps.** Composition is limited to evidence-ledger claims and must surface imbalance/coverage reports.
- **Universal-history overclaim.** Initial support is bounded by `docs/product/supported-domain-strategy.md` and measurable evaluation fixtures.

## Product Risks

- **Combined-format value is unproven.** The entire product bets that narrative+timeline+map+graph+evidence synchronization is genuinely more understandable than existing formats. Phase 1 exists specifically to test this before further investment — if it fails, the roadmap after Phase 1 should be revisited, not pushed through regardless.
- **Scope creep toward "model all of history."** Explicitly rejected in `AGENTS.md` §8 and `docs/product/product-principles.md`, but worth naming as an ongoing discipline risk given the shared-evidence-network's inherent appeal to expand — Phase 7 deliberately caps at two investigations to guard against this.
- **Assistant becoming the de facto whole product.** Explicitly guarded against (`AGENTS.md` §4, `docs/design/interaction-principles.md` #5) but is a natural gravitational pull for any LLM-forward product; revisit if usage data (once it exists) shows the assistant dominating engagement at the expense of direct exploration.

## Historical-Research Risks

- **Source curation is real work, not a checkbox.** Flagged in `development-phases.md` Phase 0 — populating the source register and reaching genuine `reviewed` status (`docs/research/validation-status.md`) for July Crisis content takes real historiographical effort and could bottleneck Phase 1/2 if underestimated.
- **Minimum evidentiary bar for "reviewed" is not yet fixed.** Open question flagged in `docs/research/source-hierarchy.md`; recommended default given in `phase-0-product-foundation.md`, but should be confirmed during Phase 0 content work.
- **Historiographical disagreement (e.g., the Fischer thesis and its critics) must be represented as genuine disagreement**, not resolved by editorial preference — this is a standing discipline risk any time a specific claim is drafted.

## Technical Risks

- **Domain model / real UX mismatch discovered late (Phase 2).** Mitigation: review `docs/architecture/domain-model.md` against the actual Phase 1 UI before writing Phase 2 migrations, not after.
- **Graph readability at real entity density.** Mock data in Phase 1 is small by design; validate the "focused local expansion, not a hairball" approach (`docs/product/product-principles.md`) against real July Crisis entity counts in Phase 3.
- **AI grounding failures.** The highest-stakes technical risk in the roadmap (Phase 4) — a citation that doesn't actually resolve to real evidence, or a confidence-flattened disputed claim, undermines the entire premise of the product. The verification pass (`docs/architecture/ai-agent-architecture.md` §3) must not be relaxed for demo polish.
- **Security surface expansion at Phase 5** (first user-supplied content) — treat as a mandatory security-review checkpoint, not routine feature work.
- **Free-infrastructure constraint under real load** for the public demo (Phase 10) — if live inference proves unreliable/costly even for four question types, fall back to cached/precomputed responses as designed in `docs/architecture/deployment.md`, rather than relaxing the cost constraint.

## Open Product Questions (resolve when reached, not now)

- Exact hosting choice for the public demo (deferred to Phase 2/4 per `deployment.md`).
- Whether a second Phase 7 investigation should be Roman-era (per the Caesar example in `shared-evidence-network.md`) or another early-20th-century topic closer to July Crisis's evidentiary style — pick based on what's genuinely tractable to curate well in the time available when Phase 7 is reached.
- Multi-language content support — not scheduled; revisit only if a specific investigation requires it.
