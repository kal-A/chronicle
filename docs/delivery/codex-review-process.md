# Codex Review Process

Codex does not have access to prior Claude/Kamal product conversations. This document and `.codex/` are the durable, self-contained instructions Codex needs to review Chronicle independently. Codex is an independent reviewer, not a simultaneous co-author — Claude and Codex must not edit the same working tree at the same time (`AGENTS.md` §9).

## Workflow

```text
Claude plans → Kamal approves → Claude implements → Claude runs tests
  → Codex independently reviews → Kamal evaluates findings
  → Claude applies accepted fixes
```

Codex should not edit code during its first review pass — see `.codex/review-template.md`.

## Review Types

### A. Phase Plan Review

When: before/at the start of a phase, or when the roadmap itself changes.
Codex reviews: product coherence, scope, missing outputs, whether each phase is testable, whether AI is being introduced before product value is established, whether the roadmap is overengineered, whether the historical-validation process is credible.
Prompt: `.codex/phase-review-prompts.md` §A.

### B. Architecture Review

When: after a phase introduces or meaningfully changes a service boundary, data model, or infrastructure piece.
Codex reviews: frontend/backend separation, domain boundaries, data-model consistency, provenance, state transitions, permissions, local deployment, unnecessary dependencies, scaling assumptions, failure recovery.
Prompt: `.codex/phase-review-prompts.md` §B.

### C. Feature Diff Review

When: at the end of any implemented slice/phase.
Codex receives: `AGENTS.md`, the feature brief, acceptance criteria, the approved implementation plan, the current diff, and test results.
Codex identifies: (1) blocking issues, (2) important improvements, (3) optional refinements.
Codex checks: missing acceptance criteria, frontend/backend mismatch, provenance loss, human-review bypass, unreviewed claims leaking into published data, broken timeline/map semantics, incorrect historical certainty, accessibility, security, missing tests, unnecessary complexity, unrelated changes.
Prompt/template: `.codex/review-template.md`.

### D. Historical Feature Review

When: any slice touching historical claims, relationships, dates, places, or citations.
Codex checks software behavior, not independent historical truth: are claims cited, is uncertainty represented, are date types distinguished, is location precision honest, can disagreement be represented, do modern geographic assumptions leak into historical views, can historical evidence be traced, are unsupported claims blocked. Historical factual validation itself still requires reviewed sources, not Codex's judgment.
Prompt: `.codex/phase-review-prompts.md` §D.

### E. Pre-Release Review

When: before public demo / portfolio release (Phase 10), and as a checkpoint at Phase 5 (security) and Phase 9 (full authoring loop dry run).
Codex: follows setup instructions from a clean environment, runs tests, inspects security-sensitive flows, tests primary user journeys, identifies stale documentation, identifies fragile demo behavior, checks whether the project can be explained credibly in an interview.
Prompt: `.codex/phase-review-prompts.md` §E.

## Codex Handoff

At the end of every completed phase, Claude generates a handoff using `.codex/review-template.md`'s handoff block (feature/phase, user problem, expected outcome, relevant docs, files changed, DB changes, API changes, tests added, commands run, known limitations, risks, acceptance criteria, specific areas requiring independent review). The handoff is factual, based on the implemented code — not Claude's internal reasoning, and not a request for Codex to simply agree.

## Directory

```text
.codex/
  README.md                 orientation for Codex (this workflow, restated standalone)
  review-template.md         Feature Diff Review template + Codex handoff template
  phase-review-prompts.md    exact reusable prompts for review types A, B, D, E
```

`.codex/` (not `docs/codex/`) was chosen because the repository is a fresh project with no existing `.codex` conflicts, and colocating Codex-specific prompt files at the repo root alongside `AGENTS.md`/`CLAUDE.md` keeps all agent-facing instruction files discoverable in one place.
