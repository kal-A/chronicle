# Chronicle

Chronicle is a local-first, multi-agent AI research engine for historical investigation. It takes an arbitrary historical question, discovers and acquires public sources, builds a retrievable corpus, and runs a four-agent pipeline (Planner → Analyst → Critic → Guide) that returns either a cited answer or a principled abstention.

The system is designed around auditable research rather than chatbot-style output. Claims are grounded to retrieved evidence, disagreement and uncertainty are preserved, and failures are handled explicitly rather than fabricated over.

**Stack:** Python, FastAPI, Pydantic, LangGraph, Ollama, React, TypeScript, Vite, Vitest.

## Status

Chronicle is a local pre-alpha on the `phase-e-ai-core` branch. End-to-end generation is working with local models and free/open-source infrastructure: an arbitrary topic is scoped, its sources discovered and acquired from public connectors (Wikipedia, Project Gutenberg, Internet Archive, and in-repo document registers), chunked into a retrievable corpus, and investigated by the four bounded AI roles over typed retrieval tools — surfaced in a map-first workspace behind a FastAPI/SSE runtime. Time-indexed territory (control / influence / contested) resolves from sourced historical-boundary datasets and works across the BC/CE boundary. The local runtime uses Ollama with `qwen2.5:7b-instruct`; ordinary tests use a deterministic provider.

The current limitation is **model consistency across the full multi-call pipeline** — not the absence of retrieval or generation capability. Chronicle is built test-first, with roughly 830 backend and 160 frontend tests currently passing. Still out of scope: a production database, authentication, and Studio review/publication workflows; generic-answer usefulness and CPU-only latency remain under evaluation (Phase E7 is planned, not implemented). New collaborators should begin with the [complete engineering handoff](CHRONICLE_COMPLETE_ENGINEERING_HANDOFF.md); the [PRD](docs/product/CHRONICLE_PRODUCT_REQUIREMENTS.md), [progress report](docs/delivery/CHRONICLE_PROJECT_PROGRESS_REPORT.md), and [`plans/current-phase.md`](plans/current-phase.md) remain supporting records.

## Project Structure

```text
AGENTS.md            canonical agent instructions (Claude Code, Codex, others)
CLAUDE.md             Claude-specific workflow, imports AGENTS.md
docs/
  product/            what Chronicle is and who it's for
  research/            historical methodology, source standards, scope
  architecture/        system, domain model, backend/frontend/AI/spatial design
  design/               UX/interaction/accessibility principles
  delivery/            phased roadmap, definition of done, risk register
  decisions/            architecture decision records (ADRs)
plans/
  current-phase.md    active work
  backlog.md          not-yet-scheduled work
  completed/          archived finished plans (currently contains its retention rules)
.codex/                Codex review prompts and process
fixtures/              cross-runtime generated-investigation JSON fixtures
```

## Product Shape

- **Generation pipeline** — the product core: scope, discovery, assessment, acquisition, extraction, criticism, geography, composition, and verification.
- **Chronicle Explore** — the inspection and navigation environment for generated investigations.
- **Chronicle Studio** — later review, correction, enrichment, and publication tooling.

## Development Model

Chronicle is built in bounded, testable slices: versioned package/generic renderer → deterministic mock CLI → real discovery/acquisition → extraction/criticism/geography → generation UX/assistant/enrichment. See [`docs/delivery/revised-development-phases.md`](docs/delivery/revised-development-phases.md).

## Cost Constraint

Chronicle is developable and demonstrable entirely on free/open-source tooling: React/TypeScript/Vite frontend, Python/FastAPI/PostgreSQL backend, Ollama + open-weight models for AI, Docker Compose for local dev. See [`AGENTS.md`](AGENTS.md) §5 for the full list and the policy on introducing paid dependencies.

## Getting Started

Frontend:

```bash
npm install
npm run dev          # start the Vite dev server
npm run lint          # oxlint
npm run typecheck    # tsc -b --noEmit
npm test              # vitest (unit/component tests + axe-core checks)
npm run build         # production build
npm run test:e2e      # Playwright journey (builds + previews first)
```

Backend and local assistant (PowerShell):

```powershell
py -3.11 -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -e "backend[test]"
ollama pull qwen2.5:7b-instruct
backend/.venv/Scripts/python -m uvicorn chronicle.api.app:app --app-dir backend/src --host 127.0.0.1 --port 8000
```

Run the frontend in another terminal with `npm run dev`. Vite proxies `/api` and `/health` to the local backend. Live-Ollama tests are opt-in; normal backend tests use the deterministic provider.

The current packages remain `prototype-curated`, not independently reviewed historical publications.

## Collaborating

- GitHub: https://github.com/kal-A/chronicle
- Start from `AGENTS.md`; Claude Code also reads `CLAUDE.md`.
- Review the PRD and progress report above before changing architecture.
- Do not expose the unauthenticated local API publicly or commit secrets/run artifacts.

## Contributing / Agent Workflow

If you're an AI coding agent (Claude Code, Codex, or otherwise) working in this repo, start with [`AGENTS.md`](AGENTS.md). Claude Code should also read [`CLAUDE.md`](CLAUDE.md). Codex reviewers should start at [`docs/delivery/codex-review-process.md`](docs/delivery/codex-review-process.md).
