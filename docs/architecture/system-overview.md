# System Overview

## Shape

Chronicle is a standard three-tier web application plus a bounded, persisted generation workflow—not a distributed agent swarm. Complexity remains proportional: the next slice is a package-driven frontend, followed by a deterministic local CLI before database/API/live-provider infrastructure.

```text
┌─────────────────────────────────────────────────────────┐
│  Frontend (React + TS + Vite)                            │
│  Chronicle Explore UI · (later) Chronicle Studio UI       │
│  - Narrative/Timeline/Map/Graph/Evidence views             │
│  - TanStack Query for server state                         │
│  - Cytoscape.js (graph) · MapLibre GL JS (map)             │
└───────────────────────────┬────────────────────────────────┘
                             │ typed HTTP API (OpenAPI via FastAPI)
┌───────────────────────────┴────────────────────────────────┐
│  Backend (Python + FastAPI + Pydantic + SQLAlchemy)         │
│  - Investigation/Entity/Evidence services (deterministic)    │
│  - Review/publication state machine                          │
│  - AI orchestration layer (bounded tools, see ai-agent-       │
│    architecture.md) — calls out to AI Runtime                │
└───────────────────────────┬────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                     │                     │
┌───────┴───────┐   ┌─────────┴─────────┐  ┌────────┴────────┐
│ PostgreSQL      │   │ AI Runtime          │  │ Object/file     │
│ + pgvector       │   │ (Ollama, local       │  │ storage          │
│ (+ PostGIS if     │   │ embeddings, mock      │  │ (local disk in   │
│ justified)         │   │ provider for tests)    │  │ dev; source docs)│
└───────────────────┘   └───────────────────────┘  └─────────────────┘
```

## Boundaries

- **Frontend never talks to the AI runtime directly.** All AI-derived content flows through the backend's review/state-machine layer so that provenance and review status are always attached (`provenance-and-review.md`).
- **The AI orchestration layer is part of the backend**, not a separate service, until/unless load or deployment constraints justify splitting it out (none are expected within the free-infrastructure constraint — see `AGENTS.md` §5).
- **Public Explore reads only ever touch reviewed/published data.** There is no code path where an Explore API response can include unreviewed content — enforced at the query layer, not just by convention (`provenance-and-review.md`).
- **Sources are global; narrative is versioned presentation.** A source may be stored without an Investigation, while any later effect on investigation prose flows through reviewed evidence, ImpactReview, NarrativeRevisionProposal, and explicit publication (`source-to-narrative-enrichment.md`).

## Active Sequencing

- **Phase A/B:** preserve the frontend, define `GeneratedInvestigation`, and render the Blank Cheque golden JSON generically.
- **Phase C:** deterministic Python CLI and mock/curated providers produce further valid packages (mock + real Concert of Europe).
- **Phase D:** map-first investigation workspace (persistent map canvas, docked/sheet assistant panel, lenses, `InvestigationExperiencePlan`, Inspector mode) — see `docs/decisions/ADR-002-map-first-workspace.md`.
- **Phase E:** real LLM agent core — four bounded agents (Planner/Analyst/Critic/Guide), typed tools over existing corpora, real (local, Ollama-based) model calls for the first time — see `docs/decisions/ADR-003-llm-agent-system-is-product-core.md`.
- **Phase F–G:** autonomous source discovery, then document acquisition and a RAG corpus (the former Phase E/F content, resequenced behind the AI core).
- **Phase H–K:** AI-driven historical model generation, a fine-tuned Chronicle task-model experiment, an AI geographic/experience composer, and full autonomous investigation end to end.

See `docs/delivery/revised-development-phases.md`.

## Deployment Shape

Current local development is the Vite frontend. The first CLI uses local artifacts and mocks. Docker Compose/Postgres/Ollama arrive only when a phase requires them. A public demo may render validated precomputed packages without live inference (`deployment.md`).
