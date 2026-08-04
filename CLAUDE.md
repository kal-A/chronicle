# CLAUDE.md — Claude Code Instructions for Chronicle

This file adds Claude-specific workflow rules on top of the canonical instructions in [`AGENTS.md`](./AGENTS.md). Read `AGENTS.md` first — product purpose, historical-integrity rules, architecture boundaries, cost constraints, testing/security requirements, git restrictions, and definition of done all live there and apply in full here.

## Claude-Specific Workflow

1. **Enter planning mode before substantial multi-file changes.** A substantial change is anything touching more than one architectural layer (e.g., data model + API), or anything a reader would notice as a new capability. Trivial fixes (typo, single-file config tweak) don't need it.
2. **Read the relevant product and architecture documents before editing.** At minimum: the phase's entry in `docs/delivery/development-phases.md`, the relevant `docs/architecture/*.md`, and `docs/product/product-principles.md`. Don't rely on memory of a prior session — these documents are the source of truth and may have changed.
3. **Inspect current code before editing.** Never assume a file's contents or a function's signature; read it first.
4. **State assumptions explicitly** when a decision isn't fully specified, record them (in the plan, or in `docs/decisions/` if architecturally significant), and design so they can be revised later without a rewrite.
5. **Identify affected files** as part of any plan before starting implementation.
6. **Propose the smallest complete vertical slice** that produces something testable — not the smallest possible diff, and not more than the current phase calls for.
7. **Do not commit or push without explicit permission**, per instance. See `AGENTS.md` §9.
8. **Update delivery documentation after implementation** — `plans/current-phase.md`, and the relevant `docs/delivery/` file, before considering the slice finished.
9. **Provide an end-of-session handoff**: what changed, what was tested, what's left, and — when a phase is complete — the Codex handoff block from `AGENTS.md` §11 / `docs/delivery/codex-review-process.md`.
10. **Do not make broad architectural changes silently.** If a task seems to require one, stop and propose it explicitly (ideally as a new ADR draft in `docs/decisions/`) before touching code.

## Critical Review Behavior

Don't rubber-stamp feature requests. Before implementing anything non-trivial, weigh it against `AGENTS.md` §18-equivalent criteria (see `docs/product/product-principles.md`): what problem it solves, whether it duplicates an existing feature, whether it belongs in Explore or Studio (or neither), whether it actually needs an LLM, whether it expands historical-validation burden, whether it threatens the free-development constraint. If a request is weak, say so and propose a stronger alternative rather than building it as asked.

## Where to Start Each Session

1. Check `plans/current-phase.md` for in-progress work.
2. Check `docs/delivery/development-phases.md` for the phase's defined scope, completion criteria, and deferred scope.
3. Check `docs/decisions/` for any ADRs relevant to the area being touched.
