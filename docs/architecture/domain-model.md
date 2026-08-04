# Domain Model

This is the entity model shared across investigations (`docs/product/shared-evidence-network.md`). It must not be hard-coded around July Crisis specifically — investigation-specific content is data, not schema. This is the outline used from Phase 2 onward; Phase 1's mock data may simplify it but should stay structurally compatible to avoid a rewrite.

## Core Entities

**Investigation** — a bounded historical topic (e.g., "July Crisis of 1914"). Has a title, scope description, period range, status (draft/published), and an ordered set of Scenes/Chapters for the guided narrative. Investigations reference shared entities below rather than owning private copies of them.

**Entity** (person / institution / place / idea / technology / condition — a shared, typed table or a supertype with subtype tables) — canonical historical entities reusable across investigations. Each carries: `entity_type`, `canonical_name`, `also_known_as` (historical naming variants), `description`, `review_status`.

- **Person** — adds role/title history (a person's role can change over the period in scope — e.g., a minister appointed mid-crisis).
- **Institution** — government body, military command, alliance, etc.
- **Place** — adds `PlacePeriodRecord` children: a place can have different names/political control across periods; never a single static "country" field. Precision tag: building/city/region/approximate.
- **Idea/Technology/Condition** — background pressures (e.g., "mobilization-timetable rigidity") that scenes/relationships can reference for context without needing to be full "events."

**Event** — something that happened at a (possibly uncertain) time and place. Carries `date_type` (exact/approximate/range/disputed) and separate optional fields for event-time vs. report-time (see Temporal Model below). References involved Person/Institution/Place entities via typed roles (actor, witness, location, etc.).

**Decision** — a specific subtype of Event where an actor/institution chose a course of action; carries `decided_by` (Person/Institution), `alternatives_considered` (optional, sourced), and is the primary anchor for "known at the time" reconstructions.

**Source** — the bibliographic/register record for a historical source, shared across investigations and permitted to exist without any Investigation link. Carries `source_type`, title, author/origin, source-production date, original language, stable citation/location, rights/access status, known limitations, curation status, and proposed/reviewed temporal and geographic coverage. The Phase 0 source register maps to this entity; acquiring or ingesting a copy does not create a second Source.

**Document** — a specific acquired or ingested representation of a Source (scan, transcription, edition, translation, or uploaded file). Carries `source_id`, representation/edition metadata, checksum, storage locator, access/rights metadata, `visibility`, and child **Passage** records. Multiple Documents may represent the same Source and must not be silently treated as textually identical.

**Claim** — an assertion about history extracted from or supported by one or more Passages. Carries temporal scope, geographic scope, and `direct_or_inferred`. Passage support is represented through required **EvidenceLink** records rather than an untyped citation list.

**Relationship** — a typed, directional or bidirectional link between two Entities/Events/Decisions/Claims. Carries `relationship_type` (causal/influenced/contextual/etc.), temporal scope, geographic scope, `direct_or_inferred`, and `evidence_classification` — one of the seven values in `docs/research/historical-methodology.md` (directly supported / indirectly supported / contextual / correlational / disputed / speculative / insufficient evidence). This field is **required**, never defaulted to a value implying certainty.

**EvidenceLink** — joins a Claim or Relationship to a Passage with a required role (`supporting` / `counterevidence` / `context`) and optional reviewer note. Every Claim requires at least one supporting EvidenceLink at write time. Relationships classified as `directly_supported` or `indirectly_supported` require supporting EvidenceLinks; a disputed Relationship must be capable of retaining both supporting and counterevidence links. Source identity and source type are reached through `EvidenceLink → Passage → Document → Source`, never duplicated as untraceable strings.

**KnownAtTime** — a record stating that a given Person/Institution knew (or did not yet know) a given fact/Event as of a given date, backed by specific evidence (a Document/Passage or a Decision that presupposes the knowledge). This is what powers "known at the time" views and is never inferred implicitly from event chronology alone.

**NarrativeBlock** — an ordered, investigation-specific unit of authored prose in a Scene. Carries immutable revision identity, referenced reviewed Claim/Relationship/KnownAtTime records, optional perspective attribution, temporal/geographic scope, and editorial metadata. Material historical assertions cannot exist only inside prose; they must resolve to reviewed domain records and their evidence chains.

**NarrativeRevisionProposal** — a reviewable proposed change to a NarrativeBlock or a proposed new block. Carries change kind, before/after text, triggering reviewed records, rationale, author/AI provenance, and review status. Acceptance creates a new block revision in a draft InvestigationPresentation version; it never mutates the active public version.

## Temporal Model

No entity has a single "date" field where more than one time concept could apply. Where relevant, separate fields exist for: `event_time`, `report_time`, `sent_time`, `received_time`, `awareness_time` (via `KnownAtTime`), `discovery_time` (when later investigators found the evidence), `interpretation_time` (when a historian's account was published). Each date field carries its own `date_type` (exact/approximate/range/disputed).

## Provenance, Review, and Visibility Fields

Claim, Relationship, KnownAtTime, and any AI-extracted candidate Entity/Event/Decision carry `review_status` (proposed/reviewed/disputed/rejected), `visibility` (public/private-workspace), `workspace_id` when private, `reviewer_notes`, and an immutable revision identifier. AI-originated or AI-modified revisions additionally carry `prompt_version`, `model_version`, and `processing_timestamp`. Full detail in `provenance-and-review.md`.

`review_status = disputed` means a human-reviewed item is intentionally published as contested. It is distinct from `evidence_classification = disputed`, which describes the strength/character of a specific Relationship. Neither value is inferred from the other.

## Investigation-Scoping vs. Shared Entities

An Investigation does not own Sources/Entities/Documents/Claims — it references them, and additionally owns versioned **InvestigationPresentation** records: investigation-specific ordering/framing of shared entities and NarrativeBlocks. One immutable presentation version is active publicly while new revisions remain draft. This makes the same evidence reusable across investigations with different framing without duplicating the underlying historical record or silently changing published prose. See `source-to-narrative-enrichment.md`.

## Explicitly Deferred

- Full entity-resolution/merge tooling (Phase 6).
- Cross-investigation relationship proposals as a distinct reviewable type (Phase 8).
- Multi-language content modeling beyond a single working language (not scheduled; flag as an open risk in `docs/delivery/risks-and-open-questions.md` if it becomes relevant).
