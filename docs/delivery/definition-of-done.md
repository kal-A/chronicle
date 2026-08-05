# Definition of Done

Applies to every vertical slice, at whatever phase it ships in. Restates and expands `AGENTS.md` §10 with concrete checks.

## Product

- [ ] Matches an approved plan or an explicitly documented, revisable assumption.
- [ ] Checked against `docs/product/product-principles.md`'s feature-evaluation checklist if it's a new capability (not required for pure bug fixes).
- [ ] Correctly placed in Explore vs. Studio (`docs/product/explore-and-studio.md`).

## Historical Integrity (if the slice touches historical content/data)

- [ ] Relationships carry a valid `evidence_classification` (`docs/research/historical-methodology.md`) — never defaulted.
- [ ] Temporal fields distinguish event/report/sent/received/awareness time where more than one applies.
- [ ] Location precision is tagged and rendered honestly.
- [ ] No modern political borders used to represent historical geography without sourcing.
- [ ] Provenance fields (`docs/architecture/provenance-and-review.md`) are populated, not left null where they shouldn't be.
- [ ] Any transition to `reviewed` or `disputed` satisfies and records the checks in `docs/research/review-standard.md`.

## Engineering

- [ ] Automated tests for the slice pass locally (Vitest/RTL, Playwright, and/or pytest as applicable).
- [ ] A manual test flow has been walked through and works.
- [ ] Loading, empty, and failure states exist for any new UI (`docs/design/investigation-layout.md`).
- [ ] Accessibility: keyboard reachability and axe-core check pass for new UI (`docs/design/accessibility.md`).
- [ ] Any new panel/sheet/dock or animated transition respects `prefers-reduced-motion` and has a documented keyboard path (resize, collapse, reopen) — required starting Phase D (`docs/decisions/ADR-002-map-first-workspace.md`).
- [ ] No raw SQL string interpolation; authz checks are server-side; no secrets committed (`AGENTS.md` §7).
- [ ] Public read paths verified not to leak `proposed`/`rejected`/`private` content, if the slice touches the Evidence or Review service.
- [ ] New evidence cannot mutate active narrative text; any text impact follows `source-to-narrative-enrichment.md` through an immutable draft revision and explicit publication.

## AI-Specific (if the slice touches an AI pipeline)

- [ ] A deterministic mock provider path exists and is what tests run against.
- [ ] Every AI-generated field carries `prompt_version`, `model_version`, `processing_timestamp`.
- [ ] Output lands in `proposed` state, never directly in a published table.
- [ ] Assistant answers (if applicable) pass the verification pass and cite real reviewed evidence.
- [ ] Workflow stages persist typed status, inputs/outputs, attempts, errors, and stage/model/prompt versions; failed work is resumable where the plan requires it.
- [ ] Generated synthesis introduces no material claim absent from the structured claim/evidence ledger.
- [ ] `GeneratedInvestigation` packages pass schema, reference, evidence, rights, temporal, geographic, interaction, and completeness checks or return an explicit partial/blocked/abstained result.
- [ ] Search snippets and metadata-only records are never used as evidence.

## Documentation

- [ ] `plans/current-phase.md` updated to reflect what's done vs. remaining.
- [ ] The relevant `docs/delivery/` phase-detail doc updated.
- [ ] Any new architecturally-significant decision recorded as an ADR (`docs/decisions/`).

## Handoff

- [ ] If a full phase is complete: a Codex handoff prepared per `docs/delivery/codex-review-process.md`.
- [ ] End-of-session summary given to Kamal per `CLAUDE.md` — what changed, what was tested, what's left.
- [ ] No commit/push has occurred without explicit per-instance approval.
