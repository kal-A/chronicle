# Historical Methodology

This document defines how Chronicle handles historical evidence and interpretation. It applies to every investigation, not just July Crisis, and is binding on both human editors and any AI-assisted extraction/proposal step.

## Core Principle: Chronology Is Not Causation

Two events being adjacent in time never, by itself, justifies a causal relationship in the data model or the UI. Every relationship between historical entities must be classified as one of:

- **Directly supported** — a primary or strong secondary source explicitly states the causal/relational link.
- **Indirectly supported** — the link is a reasonable inference from multiple sources but not explicitly stated by any one of them.
- **Contextual** — the entities are related in setting/background but no causal claim is being made.
- **Correlational** — a temporal or circumstantial association exists without evidence of causation.
- **Disputed** — credible sources or historians disagree about whether/how the entities are related.
- **Speculative** — plausible but evidentially thin; flagged as such, never presented with false confidence.
- **Insufficient evidence** — the relationship is asserted somewhere but cannot currently be supported or refuted.

This classification is a required field on every relationship record (`docs/architecture/domain-model.md`), not a documentation convention.

## Time Is Not One Field

Distinguish, wherever relevant:

- When an event occurred
- When it was reported
- When a message was sent
- When it was received
- When an actor became aware of it
- What later investigators discovered
- What later historians interpreted

Collapsing these into a single "date" is the single most common way historical claims quietly become inaccurate (e.g., implying an actor "knew" something the moment it happened, when in fact they learned of it days later via a delayed telegram). "Known at the Time" reconstructions (Phase 3) depend entirely on this distinction being real in the data, not inferred at render time.

## Geography Is Not Modern Borders

Modern political borders must never stand in for historical political control. Place names, period boundaries, and disputed geography require sourced historical data (a place record tagged with the periods/regimes under which it held a given name/status), not a present-day basemap layer reused uncritically. See `docs/architecture/spatial-architecture.md`.

## Evidence Standards

Every claim or relationship of significance retains: supporting passages, counterevidence (if any), source identifiers, source type, temporal scope, geographic scope, direct/inferred status, review status, reviewer notes, and (for AI-assisted extraction) prompt version, model version, processing timestamp, and revision history. See `docs/architecture/provenance-and-review.md`.

## Precision Discipline

Location precision is tagged (building/city/region/approximate) and rendered honestly — never a pin implying building-level precision from city-level evidence. Same discipline applies to dates (exact/approximate/range/disputed).

## Source Hierarchy and Register

See `source-hierarchy.md` for how sources are classified by evidentiary weight, and `source-register-template.md` for the per-investigation source tracking format.
