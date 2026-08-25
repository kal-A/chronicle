# Phase E5 — FastAPI and Streaming Agent Runs

**Status:** implemented and verified locally on `phase-e-ai-core`; uncommitted and unpushed.

## Delivered

- A strict, resumable `SequentialAgentWorkflow`: Planner → retrieval → Analyst → Critic → optional one bounded retrieval/reanalysis retry → Guide. Completed artifacts are reused on resume rather than recomputed.
- Safe cancellation checks between stages. Cancellation never fabricates a partial answer and persists a terminal `cancelled` run state.
- A project-wide `AgentRunManager` backed by exactly one worker. Investigation runs queue and execute one at a time; this deliberately avoids overlapping local-model calls and excess agent/session use.
- Bounded public progress events with monotonically increasing sequence numbers. Clients can reconnect with an `after` cursor or `Last-Event-ID` and replay events retained by the current server process.
- Atomic run persistence through the existing `AgentRunStore`. Polling remains authoritative across server restarts; a resumed run emits a new progress stream while retaining all previously persisted stages, model calls, tool calls, validations, and answers.
- Failure audit hardening. A provider/schema failure now persists the failed model call, failed named stage, and bounded underlying cause instead of leaving a generic error and an empty stage history.
- The first FastAPI boundary in Chronicle:

  - `POST /api/investigations/{investigation_id}/questions`
  - `GET /api/agent-runs/{run_id}`
  - `GET /api/agent-runs/{run_id}/events` (JSON polling or SSE via `Accept: text/event-stream`)
  - `POST /api/agent-runs/{run_id}/resume`
  - `POST /api/agent-runs/{run_id}/cancel`
  - `GET /api/corpora`
  - `GET /health`

- Local development CORS for `localhost`/`127.0.0.1`, including dynamic ports, so E6 can connect the current React surface without weakening the production origin policy globally.
- A default local composition using Ollama, all four implemented roles, the ten deterministic corpus tools, file-backed run storage, and compact Planner tool specifications.

Run locally from the repository root:

```powershell
backend\.venv\Scripts\python.exe -m uvicorn chronicle.api.app:create_default_app --factory --host 127.0.0.1 --port 8000
```

## Verification

- Focused sequential workflow, manager, and API suite: 13 tests passed.
- Complete AI/API suite: 355 passed, 1 skipped, and 2 opt-in local-Ollama tests deselected in the ordinary run.
- The API tests cover accepted question submission, single-worker serialization, run polling, ordered event replay, SSE framing, resume, queued cancellation, duplicate-run conflicts, terminal cancellation rejection, corpus discovery, health, and honest 404s.
- A real Uvicorn/Ollama HTTP smoke verified `/health`, two-corpus discovery, `202` question submission, persisted run polling, progress-event polling, failed-run inspection, server restart, and resume against `qwen2.5:7b-instruct`.

The live question did not reach a final answer: Qwen twice produced a `proceed` plan with zero tool calls. Chronicle correctly rejected it, persisted `planner:failed`, recorded the failed model-call metadata, and exposed the exact `SchemaValidationError`. Strengthening the topic-neutral Planner instruction and using compact tool specifications did not make this specific 7B response valid. E5 therefore proves the genuine HTTP/model boundary and honest failure behavior, not reliable production answer quality; model/prompt evaluation remains E7 work and the frontend must render retry/error states in E6.

## Operational boundaries

- SSE event replay is process-local and bounded to 256 events per run. Persisted `AgentRunRecord` state is the durable recovery source after a server restart.
- Cancellation is cooperative at stage boundaries. It can stop queued work immediately, but it does not forcibly terminate an in-flight local Ollama HTTP call.
- The run manager uses one worker by design. Parallel historical investigations are not part of this local MVP runtime.
- E5 does not add live internet research, scraping, OCR, a vector database, user accounts, or frontend integration.

## Known blocker outside E5

The repository-wide backend suite still cannot collect because the tracked legacy `backend/src/chronicle/storage/run_store.py` is deleted in the existing working tree; three package-generation/workflow tests still import it. E5 does not restore or include that unrelated deletion. The complete AI/API slice is green independently.

## E6 handoff

Replace the current Ask placeholder/keyword route with the API above. The frontend should submit the question plus immutable workspace context, subscribe to SSE with polling fallback, display the five named stages, render cited answers and limitations from the persisted run, apply only validated map actions, expose retry/resume/cancel states, and preserve the existing map-first visual system. No additional backend endpoint is required for that first integration slice.
