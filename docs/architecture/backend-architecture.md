# Backend Architecture

## Stack

Python + FastAPI + Pydantic (request/response contracts and validation) + SQLAlchemy (ORM/Core) + Alembic (migrations) + PostgreSQL + pgvector (embeddings for retrieval) + PostGIS only if/when spatial queries genuinely need it (not adopted speculatively — see `spatial-architecture.md`). pytest for tests.

## Service Boundaries

- **Investigation service** — CRUD/read for Investigations, versioned InvestigationPresentation records, Scenes, and NarrativeBlocks. Owns atomic publication state transitions; published prose is never edited in place.
- **Evidence service** — Sources, Documents, Passages, Entities, Events, Decisions, Claims, Relationships, EvidenceLinks, and KnownAtTime records. Owns the domain model in `domain-model.md`. Public/unauthenticated reads use a deny-by-default public repository interface that can return only `review_status IN (reviewed, disputed)` and `visibility = public` records attached to published investigation presentations. Unrestricted repository methods are unavailable to public endpoint handlers; authorization is not an optional per-endpoint filter.
- **Review service** — the state machine governing `proposed → reviewed/disputed/rejected` transitions, ImpactReviews, and NarrativeRevisionProposals (Phase 6+). It may create draft presentation revisions but cannot publish them. See `provenance-and-review.md` and `source-to-narrative-enrichment.md`.
- **Generation workflow** — persisted bounded stages for scope, discovery, assessment, acquisition, extraction, resolution, timeline, relationship/critic, geography, composition, and verification. Every generated record is a proposal with stage/prompt/model provenance. See `investigation-generation-pipeline.md`.

## API Contract

The versioned `GeneratedInvestigation` JSON contract is the renderer boundary. Pydantic owns backend schemas and FastAPI/OpenAPI transport; Zod validates frontend consumption. Shared golden JSON contract tests prevent semantic drift.

## Persistence Rules

- No raw SQL string interpolation; SQLAlchemy ORM/Core parameterized queries only (`AGENTS.md` §7).
- Published content is never hard-deleted; edits to reviewed content produce a new revision (`revision_history`) rather than overwriting — this is what makes "no silent public updates" (`shared-evidence-network.md`) enforceable rather than aspirational.
- Migrations (Alembic) are the only way schema changes ship; no manual production schema edits, including in the seeded-demo environment.

## AI Runtime Integration

Model generation, embeddings, discovery, and acquisition use separate thin provider protocols. Deterministic mocks/fixtures are implemented first and used in tests. Ollama and real discovery adapters are added only in their scheduled phases; no test depends on live inference or network results.

## Testing Requirements

- pytest unit tests per workflow stage/provider/verification rule. The first CLI may use an artifact repository; database integration tests use containerized Postgres once SQLAlchemy persistence is introduced.
- Contract tests enumerating every public read endpoint and proving proposed, rejected, private-workspace, and unpublished-presentation fixtures are excluded (a regression here is a historical-integrity bug, not just a bug — see `AGENTS.md` §13).
- Integration tests for the review state machine's transitions, including that `disputed` is publicly visible only after human review, with its disputed label and rationale intact.

## Explicitly Deferred

- Splitting AI orchestration into its own service/process (only if load or deployment genuinely requires it — none expected under the free-infrastructure constraint).
- Multi-tenant/organization concepts.
- PostgreSQL/pgvector/PostGIS/background-worker adoption before a phase proves it needs them.
