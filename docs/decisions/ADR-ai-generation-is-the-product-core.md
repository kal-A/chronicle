# ADR: AI Generation Is the Product Core

**Status:** Accepted — 2026-08-03

## Context

Chronicle began with an Explore-first plan centered on a manually curated July Crisis experience. The resulting Blank Cheque slice validates valuable renderer, evidence, synchronization, map, graph, and accessibility patterns, but manual expansion would make Chronicle primarily a historical viewer and would not demonstrate its intended AI systems value.

## Decision

The bounded, auditable investigation-generation pipeline is Chronicle's product core. The frontend becomes a generic environment for inspecting and challenging versioned `GeneratedInvestigation` packages. The Blank Cheque slice becomes the first golden fixture and regression case.

Generation is not one prompt and not an autonomous swarm. It is a persisted workflow of typed stages with deterministic validation, source and rights controls, counterevidence/critic passes, abstention, retries, and audit metadata.

## Consequences

- Stop manually expanding July Crisis scenes.
- Define the versioned package contract before additional content work.
- Build a deterministic mock CLI pipeline before live discovery or model calls.
- Move real source discovery/acquisition ahead of broad investigation UI expansion.
- Preserve all existing historical-integrity, human-review, visibility, and publication protections.
- Limit initial claims to the supported domain in `docs/product/supported-domain-strategy.md`.
- Treat generated investigations as drafts unless human review/publication criteria are met.

## Relationship to ADR-001

This ADR supersedes ADR-001's phase sequencing. Explore remains the primary public inspection surface and Studio concerns still must not dominate reader UX, but generation infrastructure now precedes further manual Explore content because generation—not manual authoring—is the core product hypothesis.

## Alternatives Rejected

- Continue manually authored investigations: polished but fails the new product core.
- One large research prompt: unauditable and structurally unsafe.
- Build full live retrieval first: too much risk before the package and deterministic workflow contract are proven.
- Universal-history launch: unsupported by evaluation, source, language, and geography coverage.

