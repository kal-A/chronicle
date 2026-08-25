# Chronicle

An AI-powered historical investigation generator and interactive systems atlas. Chronicle builds bounded, source-backed draft investigations and provides a synchronized environment for inspecting claims, timelines, maps, relationships, evidence, disagreement, uncertainty, and gaps.

Chronicle is not a history chatbot, not a Wikipedia clone, and not a graph-visualization demo. It's built to answer questions static articles and generic timelines can't: what did this actor know by this date, where do these accounts disagree, what evidence actually supports this interpretation, how did this earlier decision shape this later one.

The existing July Crisis Blank Cheque slice is the first golden renderer fixture. The initial supported generation domain is European diplomatic and political history, 1814–1914.

## Status

Chronicle is a local pre-alpha on the `phase-e-ai-core` branch. The versioned package/generic renderer, deterministic Python pipeline, two package-backed benchmark investigations, map-first workspace, four bounded AI roles, typed retrieval tools, FastAPI/SSE runtime, and live investigation Ask panel are implemented. The local runtime uses Ollama with `qwen2.5:7b-instruct`; ordinary tests use a deterministic provider.

Phase E6 is a working vertical slice but is not formally closed: generic-answer usefulness, semantic directionality/entailment, and CPU-only latency still need evaluation. Phase E7 is planned but not implemented. Chronicle does **not** yet provide open web/database research, document acquisition, a production database, authentication, Studio review workflows, or general new-topic generation. The landing page currently routes only to two disclosed curated packages. See [`plans/current-phase.md`](plans/current-phase.md), the [PRD](docs/product/CHRONICLE_PRODUCT_REQUIREMENTS.md), and the [engineering progress report](docs/delivery/CHRONICLE_PROJECT_PROGRESS_REPORT.md).

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
