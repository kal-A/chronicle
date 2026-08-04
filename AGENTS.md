# AGENTS.md — Chronicle Canonical Agent Instructions

This is the canonical instruction file for any AI coding agent working in this repository (Claude Code, Codex, or others). `CLAUDE.md` imports this file and adds Claude-specific workflow rules. If the two ever conflict, this file wins on product/architecture matters; `CLAUDE.md` wins on Claude-specific workflow mechanics.

## 1. Product Purpose

Chronicle is an AI-powered historical investigation generator and interactive systems atlas. A bounded, auditable generation pipeline turns a user topic/question/source into a versioned draft investigation; the frontend is where users inspect, challenge, navigate, and extend its claims, timeline, map, graph, evidence, uncertainty, and limitations.

It is not a chatbot, not a Wikipedia clone, not a graph demo, not an autonomous historian. See `docs/product/product-vision.md` for the full statement.

## 2. Generation-First Priority

The investigation-generation pipeline is the product core; the existing Explore prototype is its renderer, evidence inspector, golden fixture, and regression case. Do not manually expand historical scenes before the versioned `GeneratedInvestigation` contract, generic renderer, and deterministic mock generation workflow exist. Generation must remain user-visible, bounded, resumable, and auditable. See `docs/product/ai-first-product-definition.md` and `docs/decisions/ADR-ai-generation-is-the-product-core.md`.

## 3. Historical Integrity Rules

These are non-negotiable constraints on any feature touching historical content:

- Relationships between events must be classifiable as: directly supported, indirectly supported, contextual, correlational, disputed, speculative, or insufficient evidence. Chronological adjacency is never sufficient to imply causation in the UI or the data model.
- Every claim/relationship of significance must be able to retain: supporting passages, counterevidence, source identifiers, source type, temporal scope, geographic scope, direct/inferred status, review status, reviewer notes, prompt version, model version, processing timestamp, revision history.
- Distinguish event-time, report-time, message-sent-time, message-received-time, actor-awareness-time, discovery-time, and interpretation-time as separate fields — never collapse them into one "date."
- Never represent city-level evidence as an exact building-level location.
- Never render modern political borders as if they were historical political geography. Period boundaries, place names, and political control require sourced historical data, not modern GeoJSON borders reused uncritically.
- See `docs/research/historical-methodology.md` and `docs/architecture/provenance-and-review.md`.

## 4. Architecture Boundaries

- Deterministic software owns: permissions, auth, investigation/project boundaries, persistence, review status, date filtering, timeline ordering, map coordinates, graph traversal, citation existence checks, source visibility, publication rules, state transitions.
- LLMs own: ambiguous language and unstructured material — extraction assistance, entity resolution suggestions, relationship proposals, retrieval, comparison, answer composition. LLM output is always a *proposal* until it passes a deterministic validation and/or human review gate appropriate to its risk (see `docs/architecture/provenance-and-review.md`).
- No autonomous agent swarms. Prefer explicit state machines, typed inputs/outputs, small bounded tools, deterministic validation, human review, auditable execution. See `docs/architecture/ai-agent-architecture.md`.
- Discovery/acquisition/model/embedding providers sit behind typed adapters. Search snippets and metadata are never evidence; rights and full-text availability are deterministic gates. Generated packages must pass `docs/architecture/verification-and-abstention.md`.
- Frontend/backend split, domain model, and service boundaries are defined in `docs/architecture/system-overview.md` and `docs/architecture/domain-model.md` — read them before adding new services or crossing an existing boundary.

## 5. Cost Constraints

- No paid infrastructure required to develop or demo the project. Preferred stack: React/TypeScript/Vite/Tailwind/TanStack Query/Cytoscape.js/MapLibre GL JS on the frontend; Python/FastAPI/Pydantic/SQLAlchemy/Alembic/PostgreSQL/pgvector(+PostGIS if justified) on the backend; Ollama + open-weight models + local embeddings for AI runtime; Docker Compose + GitHub Actions for infra; free hosting only for a seeded static/preprocessed public demo.
- Any new paid dependency must be explicitly proposed with a written justification for why no free option suffices, and requires Kamal's approval before adoption.
- Claude Code and Codex are development-time tools only. Never wire them into runtime request paths of the shipped product.

## 6. Testing Requirements

- Every vertical slice ships with tests appropriate to its layer: Vitest + React Testing Library for frontend units, Playwright for user journeys, pytest for backend/services.
- AI-touching code must have a mock/deterministic provider path so tests do not depend on live inference.
- A phase is not "done" until its automated test requirements (defined per-phase in `docs/delivery/development-phases.md`) pass, in addition to a manual test flow being walked through.

## 7. Security Requirements

- Never commit secrets, API keys, or credentials. Use `.env` files excluded via `.gitignore`.
- Treat all uploaded source content (Phase 5+) as untrusted input: validate file types/sizes, sanitize extracted text before storage/display, and never execute or interpret uploaded content as code.
- Public Explore endpoints must never expose unreviewed private-workspace data.
- Follow OWASP top-10 basics for any API surface: parameterized queries only (SQLAlchemy ORM/Core, no raw string interpolation), authz checks server-side (never trust client-side role flags), output-encode anything rendered as HTML.

## 8. Development Workflow

- Work in bounded vertical slices defined by `docs/delivery/revised-development-phases.md`: package contract/generic renderer → deterministic mock CLI → real discovery/acquisition → extraction/criticism/geography → generation UX/assistant/enrichment.
- Prove the contract end to end with golden fixtures and mock providers before live search, downloads, embeddings, or model calls. Do not add manually authored scenes as a substitute for the generation pipeline.
- Update the relevant `docs/delivery/` and `plans/` files as part of finishing a slice, not as an afterthought.

## 9. Git Restrictions

- Never commit or push without explicit, per-instance approval from Kamal. A prior approval does not carry forward to future commits.
- Never force-push, never rewrite published history, never skip hooks (`--no-verify` etc.) without explicit instruction.
- Claude and Codex must not edit the same working tree simultaneously (see `docs/delivery/codex-review-process.md`).

## 10. Definition of Done

A slice/phase is done when all of the following hold — see `docs/delivery/definition-of-done.md` for the full checklist:

1. It matches an approved plan or documented assumption.
2. Automated tests for the slice pass locally.
3. A manual test flow has been walked and works.
4. Loading, empty, and failure states exist for any new UI.
5. Historical-integrity rules (§3) are respected in any touched data path.
6. Relevant docs (`docs/delivery/`, `plans/current-phase.md`) are updated.
7. A Codex handoff has been prepared if the phase is complete (see §11).

## 11. Rules for LLM Outputs

- LLM output is never treated as ground truth. It is either (a) a proposal awaiting deterministic validation + human review, or (b) an answer that must cite reviewed evidence already in the database, never bare model knowledge.
- The investigation assistant must refuse or hedge rather than invent citations, claim an actor "knew" something because information existed somewhere, flatten disputed interpretations into a single account, or present unreviewed uploads as public fact.
- Every AI-generated field that reaches a human review queue must carry prompt version, model version, and processing timestamp.
- Generated synthesis may use only structured evidence-backed Claims; it may not introduce new material claims in prose. Abstention and partial results are successful outcomes.

## 12. Rules for Map and Graph Accuracy

- Map layers must be tagged with the historical period they are valid for; do not silently reuse a present-day basemap layer to imply present-day borders were historical.
- Location precision must be tagged (e.g., `city`, `region`, `building`, `approximate`) and the UI must render precision honestly (no false-precision pins).
- Graph nodes/edges must carry the same relationship-strength classification as §3 — the graph must not visually imply certainty a relationship doesn't have.

## 13. Rules Protecting Human-Reviewed Data

- Public Explore content is only ever produced from data that has passed the review workflow defined in `docs/architecture/provenance-and-review.md`.
- New source ingestion (Phase 5+) must never silently mutate an already-published investigation. All proposed changes route through an impact review that a human editor accepts, revises, disputes, or rejects.
- Version history is retained for any published entity; destructive edits to reviewed content are disallowed at the data-model level, not just by convention.

## Document Map

- Product: `docs/product/`
- Historical research & methodology: `docs/research/`
- Architecture: `docs/architecture/`
- Design/UX: `docs/design/`
- Delivery/phases: `docs/delivery/`
- Decisions (ADRs): `docs/decisions/`
- Active plans: `plans/`
- Codex review process: `docs/delivery/codex-review-process.md`, `.codex/`
