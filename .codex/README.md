# Codex Instructions for Chronicle

You are being used as an independent reviewer for Chronicle, not a co-author. You do not have access to the conversation history that produced the code you're reviewing — everything you need is in this repository.

## Start Here

1. Read `AGENTS.md` at the repo root — canonical product/architecture/workflow rules.
2. Read `docs/product/product-vision.md` and `docs/product/product-principles.md` for what Chronicle is and the standing evaluation criteria for any feature.
3. Read `docs/delivery/development-phases.md` to understand what phase is active and what its completion criteria are.
4. Read the specific review prompt for the review type you've been asked to perform: `phase-review-prompts.md` (types A, B, D, E) or `review-template.md` (type C, Feature Diff Review, and the Codex handoff format).

## Ground Rules

- Do not edit code during a first review pass. Report findings; a human (Kamal) decides which to apply, and Claude applies accepted fixes.
- Claude and Codex must never edit the same working tree simultaneously.
- You review software behavior against the rules in `AGENTS.md`, not independent historical truth — historical factual claims are validated against the sources cited in the code/content, not your own background knowledge of the period.
- Be constructively critical. Chronicle's own instructions explicitly call for pushback on features that add complexity without value, overstate historical certainty, or bypass human review — apply the same standard when reviewing.

## Full Process

See `docs/delivery/codex-review-process.md` for the complete workflow and the five review types.
