# Architecture Decision Records

ADRs capture architecturally-significant decisions — ones that are expensive to reverse, affect multiple future phases, or resolve a genuine tradeoff rather than a default. Not every choice needs one; routine implementation decisions belong in the relevant `docs/architecture/*.md` file instead.

## When to Write One

- A choice between two or more genuinely viable approaches with real tradeoffs (per `CLAUDE.md` workflow item 10: broad architectural changes should be proposed as an ADR draft before implementation).
- A decision that would be costly to silently reverse later (e.g., domain-model shape, service boundaries, core sync contracts).
- A documented assumption from `AGENTS.md` §"State assumptions" that's significant enough to want a durable record of *why*, not just *what*.

## Format

`ADR-NNN-short-title.md`, numbered sequentially, never renumbered/reused even if superseded. Each ADR: Context, Decision, Consequences, Alternatives Considered, Status (proposed/accepted/superseded).

## Index

- [ADR-001: Explore-First Sequencing](ADR-001-explore-first.md) — accepted
- [ADR: AI Generation Is the Product Core](ADR-ai-generation-is-the-product-core.md) — accepted; supersedes ADR-001 phase sequencing
- [ADR-002: Map-First Investigation Workspace](ADR-002-map-first-workspace.md) — accepted; inserts Phase D, shifts former Phases D-K to E-L
