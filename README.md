# Chronicle

Chronicle is a local-first, multi-agent AI research engine for historical investigation.

Given a historical question, it discovers and acquires public sources, builds a retrievable corpus, and runs a four-agent workflow — **Planner → Analyst → Critic → Guide** — designed to return either a source-backed, cited answer or a principled abstention rather than fabricate unsupported claims.

It pairs source retrieval with a map-first, auditable investigation workspace for exploring people, events, geography, evidence, disagreement, uncertainty, and cause-and-effect — not a general-purpose history chatbot.

**Stack:** Python, FastAPI, Pydantic, LangGraph, Ollama, React, TypeScript, Vite, Vitest. Storage is file-based with a local vector index — no external database.

## Status

Chronicle is in local pre-alpha. End-to-end generation works with local models and free/open-source infrastructure: a question is scoped, public sources are discovered and acquired, a retrievable corpus is built, and four bounded AI roles produce a cited answer or a principled abstention.

The main remaining limitation is **consistency across the full multi-call local-model pipeline** — not missing retrieval or generation capability. Chronicle is built test-first: roughly 850 backend and 140 frontend tests, plus six Playwright end-to-end journeys, currently pass. Out of scope for now: an external database, authentication, and Studio review/publication workflows; generic-answer usefulness and CPU-only latency remain under evaluation. See [How it works](#how-it-works) for the pipeline and [Current limitations](#current-limitations) for the detail.

## How it works

A question runs through a bounded pipeline; each stage is a distinct, typed unit rather than one large prompt:

1. **Scope resolution** — an LLM-assisted, deterministically gated pass proposes a time window, key actors, and search terms; the frontend lets you review and edit the scope before acquisition.
2. **Source discovery** — free public connectors (Wikipedia, Project Gutenberg, Internet Archive, in-repo document registers) return candidate sources; a connector that fails is skipped, not fatal.
3. **Acquisition** — full text is fetched and cached; a single flaky or forbidden source (e.g. a 403) is skipped and recorded, so the build continues on the sources that do succeed (partial acquisition).
4. **Corpus build** — acquired text is chunked into `Passage` records tied to `Source` records.
5. **Retrieval** — typed `search_passages` over the corpus, lexical by default, with optional local-embedding semantic re-ranking (RRF) of the lexical candidates.
6. **Planner** — proposes an authorized, corpus-scoped plan of typed tool calls, or abstains.
7. **Analyst** — drafts statements grounded in retrieved evidence.
8. **Critic** — reviews the draft for support and directionality.
9. **Guide** — composes the final user-facing answer from approved statements.
10. **Grounding validation → cited answer or abstention** — deterministic validators check that every claim resolves to a retrieved passage/source; the run returns a cited answer or a principled abstention.
11. **Frontend rendering** — a React/TypeScript workspace streams progress over SSE and renders the cited answer, evidence, and a data-driven map.

Orchestration is an explicit LangGraph state machine (`graph.py`), not an autonomous agent swarm. Model calls run locally through Ollama (`qwen2.5:7b-instruct`) with JSON-Schema-constrained structured outputs; ordinary tests use a deterministic provider instead of live inference. The map renders time-indexed territory (control / influence / contested) resolved from sourced historical-boundary datasets, across the BC/CE boundary. A test-enforced anti-hardcoding guard keeps the corpus, tool, orchestration, acquisition, and evaluation code free of any specific subject name, so the same code path serves an arbitrary topic.

## Current limitations

Chronicle is honest about what is and isn't reliable:

- **Multi-call consistency is the main limiting factor.** The end-to-end path chains roughly five local-model calls (planner, analyst, critic, guide, plus retrieval-driven calls). Each stage is deterministically validated, but the full chain on a local 7B model is probabilistic: a run can abstain or produce a weaker answer where a larger model would succeed. Isolated stages and the end-to-end architecture work; production-grade reliability across the whole chain is not claimed.
- **Semantic retrieval is a precision re-rank, not full hybrid recall.** It reorders lexical candidates; it does not retrieve passages the lexical lane misses entirely, and it is a no-op without a local embedding model.
- **Corpora are `prototype-curated` / auto-acquired scaffolding**, not independently reviewed historical publications; auto-acquired corpora can be thin.
- **CPU-only latency is minutes-scale** for a full run, and **generic-answer usefulness is not yet formally evaluated** (the Phase E7 comparative-evaluation harness is planned, not implemented).
- **No authentication, no external database, and no Studio review/publication workflow.** The local API is unauthenticated and must not be exposed publicly.

## Why this exists

Many general-purpose AI tools optimize for fluent answers over explicit evidence chains. Chronicle is built the other way around: an investigation is an auditable object — evidence chains, source-backed claims, preserved disagreement and uncertainty, causal relationships, historical actors, and time-indexed geography — and an honest abstention is a valid result rather than a failure to paper over.

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

- **Generation pipeline** — the product core (see [How it works](#how-it-works)).
- **Chronicle Explore** — the inspection and navigation environment for generated investigations.
- **Chronicle Studio** — later review, correction, enrichment, and publication tooling (not yet built).

## Development Model

Chronicle is built test-first, in bounded and independently testable vertical slices. See [`docs/delivery/revised-development-phases.md`](docs/delivery/revised-development-phases.md) for the phased roadmap.

## Cost Constraint

Chronicle is developable and demonstrable entirely on free and open-source tooling — no paid APIs or hosted infrastructure; local inference and embeddings run through Ollama with open-weight models. See [`AGENTS.md`](AGENTS.md) §5 for the policy on introducing paid dependencies.

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
- Orientation: the [complete engineering handoff](CHRONICLE_COMPLETE_ENGINEERING_HANDOFF.md), then the [PRD](docs/product/CHRONICLE_PRODUCT_REQUIREMENTS.md), [progress report](docs/delivery/CHRONICLE_PROJECT_PROGRESS_REPORT.md), and [`plans/current-phase.md`](plans/current-phase.md).
- Review the PRD and progress report before changing architecture.
- Do not expose the unauthenticated local API publicly or commit secrets/run artifacts.

## Contributing / Agent Workflow

If you're an AI coding agent (Claude Code, Codex, or otherwise) working in this repo, start with [`AGENTS.md`](AGENTS.md). Claude Code should also read [`CLAUDE.md`](CLAUDE.md). Codex reviewers should start at [`docs/delivery/codex-review-process.md`](docs/delivery/codex-review-process.md).
