# Deployment

> AI-first sequencing note: Phase B remains a static frontend over golden packages; Phase C adds a local deterministic CLI/artifact store. Docker Compose, PostgreSQL, Ollama, and live inference are introduced only when the revised roadmap requires them.

## Local Development

Docker Compose services: `frontend` (Vite dev server), `backend` (FastAPI/uvicorn), `db` (PostgreSQL + pgvector extension), `ollama` (AI runtime, optional profile — not required for frontend-only or non-AI backend work). A single `docker compose up` should bring up a working stack from Phase 2 onward. Alembic migrations run as a one-shot service/command on startup in dev, not auto-applied silently in any environment beyond local dev.

## CI

GitHub Actions, free tier. Pipeline runs, at minimum: frontend lint + typecheck + Vitest, backend lint (ruff) + mypy/pyright (if adopted) + pytest against a containerized Postgres service, and Playwright journeys against a built frontend + seeded backend for PR-level confidence once Phase 2 exists. No paid CI runners or paid environments.

## Public Demo

A seeded, mostly-static or preprocessed build of the July Crisis investigation on free hosting (e.g., a static host for the frontend build; a small free-tier or self-hosted backend instance, or — preferably, to avoid any hosting cost/uptime burden — a fully static export of the seeded reviewed content with the live assistant either disabled, rate-limited, or backed by precomputed cached responses for the four supported question types). The exact hosting choice is deferred to Phase 2/4 implementation and should be proposed then with an explicit cost check against `AGENTS.md` §5, not decided here.

## Environments

- **Local** — full stack, live Ollama inference, seeded or hand-test data.
- **CI** — full stack, mock AI provider, seeded test fixtures.
- **Public demo** — seeded reviewed content only, AI features degraded gracefully to precomputed/cached or disabled rather than exposing an unreliable or costly live-inference path to anonymous public traffic.

## Secrets

No secrets are required for the core stack (Postgres credentials are local dev defaults, Ollama runs unauthenticated locally). If a future phase introduces any external API key, it is loaded via `.env` (git-ignored) and never committed — see `AGENTS.md` §7.

## Explicitly Deferred

- Any multi-region, autoscaling, or paid-tier hosting.
- A separate staging environment beyond CI + local (not justified at this project's scale).
