# Request trace — one investigation, end to end

This traces a single request through Chronicle's real code paths, file by file, from
the HTTP call to the cited answer (or principled abstention) that reaches the
browser. It is written to be checked against the source: every step names the
module and function that performs it. Line numbers are given where stable; prefer
the function name if a line has drifted.

The request traced is the flagship **"search any topic"** call —
`POST /api/investigations/build` — because it exercises the whole system:
**acquisition → retrieval → four agents → deterministic validation → streamed result.**
A question over an already-built corpus (`POST /api/investigations/{id}/questions`)
is the same trace with Phase A skipped.

## At a glance

```
HTTP POST /api/investigations/build
  │  api/app.py: build_and_investigate()
  ▼
Phase A — Acquisition (synchronous, in the request thread)
  acquisition/build_service.py: CorpusBuildService.build()
    → acquisition/pipeline.py: AcquisitionPipeline.run()
        scope years → discover_sources() → fetch/cache → chunk → embed → corpus_builder
    → registers a PackageBackedCorpus in the CorpusRegistry
  ▼
Handoff
  api/app.py: _make_run_record()  →  AgentRunManager.submit()  → HTTP 202 (runId)
  ▼
Phase B — Investigation (async, single background worker)
  ai/orchestration/manager.py: _execute() → workflow.run()
    → ai/orchestration/graph.py: LangGraphAgentWorkflow  (compiled StateGraph)
        planner → retrieval → analyst → finalization(critic → [follow-up] → guide)
  ▼
Streaming + result
  ai/orchestration/manager.py: bounded event journal
  api/app.py: GET /api/agent-runs/{id}/events (SSE)  +  GET /api/agent-runs/{id} (poll)
```

Every stage writes the run record to disk (`storage/agent_run_store.py`) before the
next begins, so the run is resumable and fully auditable.

---

## Entry — the HTTP route

`api/app.py` → `build_and_investigate(submission)` (around line 173).

1. Guards that acquisition is configured (`build_service is not None`), else `501`.
2. Calls `build_service.build(topic=…, terms=…, max_sources=…)` — **Phase A**, run
   synchronously. FastAPI runs sync routes in a threadpool, so the event loop is not
   blocked while acquisition (minutes-scale on CPU) proceeds.
3. A per-source outage surfaces as `502`, not an opaque `500` (`ConnectorError` handler).
4. On success it looks the freshly registered corpus up in the `CorpusRegistry`,
   builds the run record (`_make_run_record`, ~line 399), and submits it to the
   `AgentRunManager` — **handoff to Phase B**.
5. Returns `202 Accepted` with the discovery/acquisition counts and the `runId` the
   frontend will stream.

## Phase A — Acquisition (`build_service.build` → `AcquisitionPipeline.run`)

`acquisition/build_service.py: CorpusBuildService.build()` bridges an arbitrary topic
to a registered, investigatable corpus. It is idempotent: an identical topic reuses
the already-registered corpus rather than re-acquiring.

Inside `acquisition/pipeline.py: AcquisitionPipeline.run()`:

1. **Scope.** `scope_years(...)` resolves an era-aware time window (BC/CE capable,
   ADR-005) and a `DiscoveryQuery` is built from `topic` + scope `terms` (pipeline.py
   ~line 101).
2. **Discovery.** `acquisition/discovery.py: discover_sources()` fans the query across
   free connectors (`connectors/wikipedia.py`, `gutenberg.py`, `internet_archive.py`,
   `doc_registry_seed.py`), drops candidates whose full text is not retrievable
   (snippets are never evidence), deduplicates, and **ranks by topic relevance**
   (`_select_by_relevance`) so namesakes that share only the head word are dropped
   rather than crowding out on-topic sources.
3. **Acquire + cache.** Each surviving candidate's full text is fetched and stored in a
   content-addressed `FetchCache`; a single 403/flaky source is skipped and recorded
   (partial acquisition), never fatal.
4. **Chunk.** `acquisition/chunking.py` splits text into `Passage` records tied to
   `Source` records.
5. **Embed (optional).** With `CHRONICLE_ENABLE_SEMANTIC`, `acquisition/embeddings.py`
   (`OllamaEmbedder`) adds a local vector index for semantic re-ranking; the lexical
   path always works without it.
6. **Enrich (optional).** With `CHRONICLE_ENABLE_EXTRACTION`, `acquisition/extraction.py`
   + `control_state.py` add located events, a timeline, and grounded territory via the
   period-aware geocoder and boundary resolver.
7. **Build + register.** `acquisition/corpus_builder.py` assembles a contract-valid
   `GeneratedInvestigation` package, persists it, and registers it as a
   `PackageBackedCorpus` — the **same** corpus type the two curated fixtures use, so
   the investigation layer treats a generated corpus exactly like a curated one.

Output: a registered `corpusId` plus discovery/acquisition counts.

## Handoff — request → run record → worker

`api/app.py: _make_run_record()` builds an immutable `AgentRunRecord` carrying the
`InvestigationRequest` (runId, corpusId, userQuestion) and a `CorpusSnapshot`
(packageHash, schemaVersion, capabilities, knownOmissions) — the provenance the whole
audit trail is anchored to.

`ai/orchestration/manager.py: AgentRunManager.submit()` (line 128) enqueues the record
onto a **single-worker** `ThreadPoolExecutor(max_workers=1)` (line 123). This is the
"one investigation at a time" gate: LangGraph owns per-run control flow, the manager
owns the global queue. `_execute()` (line 193) runs the workflow, passing an `emit`
callback that appends each stage signal to a bounded, replayable **event journal**
(the `_EventJournal`, line 55) for SSE.

## Phase B — Investigation (`LangGraphAgentWorkflow.run`)

`ai/orchestration/graph.py: LangGraphAgentWorkflow.run()` (line 95) sets the run
`RUNNING`, saves it, emits `RUN_STARTED`, and invokes a compiled LangGraph
`StateGraph`. The graph is an **explicit state machine** (ADR-003 — no autonomous
swarm): four nodes with conditional edges (wiring at lines 417–441).

### 1. `planner_node` (line 155)
- Builds a `ToolExecutionContext` bounded by the execution policy, gets the tool specs
  available **for this corpus** (a passages-only draft corpus offers only
  `search_passages` / `get_map_context`), and calls
  `ai/agents/planner.py: InvestigationPlanner.plan()` (line 79) — **one model call**.
- The model returns an `InvestigationPlan`. Before validation the planner **clamps**
  any over-budget result limit down to the policy max (`_clamp_result_limits`) rather
  than rejecting the whole plan, then runs deterministic authorization
  (`_validate_candidate`, line 142): tool must be authorized for the corpus, arguments
  must match the advertised schema, no invented record IDs.
- The system prompt steers direct/descriptive questions toward passage search
  (`ai/agents/planner_prompt.py`), so the planner does not default to a map/timeline
  tool that would retrieve nothing.
- **Branches:** an `ABSTAIN` disposition, or a `PlannerValidationError` on a model plan,
  ends the run as a principled `ABSTAINED` with an audited `REJECTED` stage.

### 2. `retrieval_node` (line 232)
- Calls `ai/orchestration/runner.py: InvestigationRunner.execute_initial()` (line 83).
- `_augment_with_floor()` appends one bounded `search_passages(question)` when the plan
  omitted it (the **retrieval floor**), so the analyst always sees the corpus text even
  if the planner chose a tool that retrieves nothing.
- `_execute_calls()` (line 284) dispatches each typed tool under strict budgets
  (per-tool result cap, aggregate character/result caps, a deadline), after
  `_preflight_calls()` (line 207) re-validates every call's capabilities and input
  schema. It produces a `RetrievalBundle` with a `RetrievedReferenceIndex` of the exact
  passages/sources/records retrieved.
- **Branches:** a `REJECTED` bundle (unusable plan) → `ABSTAINED`; a `FAILED` /
  `INTERRUPTED` bundle → `FAILED` / `INTERRUPTED`.

### 3. `analyst_node` (line 295)
- Calls `ai/agents/analyst.py: EvidenceAnalyst.analyze(question, plan, bundle)` — **one
  model call** — which drafts statements, each carrying citations into the retrieved
  evidence.
- The draft is then **deterministically grounding-validated**: every citation must
  resolve to a passage/source/record actually present in the retrieval bundle. The
  result is a `GroundingValidationReport` stored on the run.
- **Branch:** an ungroundable draft raises `AnalystValidationError` → `ABSTAINED`
  ("the retrieved evidence could not ground an analysis"). This is the honest failure a
  small local model hits most often over a thin corpus — the system abstains rather
  than assert unsupported claims.

### 4. `finalization_node` (line 356) → `finalization.py: finalize()` (line 67)
- **Critic** (`ai/agents/critic.py: HistoricalCritic.review`, line 88) — one model call
  — reviews the grounded draft for support and directionality; the decision is itself
  validated (`ai/agents/validation.py: validate_critic_decision`).
- **Bounded single follow-up** (line 112): if the critic flags a gap, exactly one extra
  retrieval round + re-analysis runs (`execute_follow_up`) — the only loop, budget-capped.
- **Guide** (`ai/agents/guide.py: InvestigationGuide`) — one model call — composes the
  final user-facing `AgentAnswer` (directAnswer, keyPoints, disagreements) **only from
  approved, grounded statements**, each with its citations.
- **Terminal:** `ANSWER_READY` with a cited answer, or `ABSTAINED` if the critic/guide
  model call can't produce a usable, validated result.

## The deterministic-validation spine

Every model call is wrapped by a deterministic gate, which is what makes the system
auditable rather than "trust the LLM":

| Stage | Gate | On failure |
|---|---|---|
| Planner | tool authorization + schema (`_validate_candidate`) | audited abstention |
| Retrieval | capability + input preflight, hard budgets (`_preflight_calls`, `_execute_calls`) | abstain / fail |
| Analyst | citation grounding → `GroundingValidationReport` | abstain (unsupported) |
| Critic | decision validation (`validate_critic_decision`) | abstain |
| Guide | answer composed only from approved statements | abstain |

## Streaming and result

- Each `WorkflowSignal` (RUN_STARTED, STAGE_STARTED/COMPLETED, RUN_ABSTAINED/COMPLETED)
  is appended to the run's event journal (`manager.py`).
- The frontend opens `GET /api/agent-runs/{id}/events` → `api/app.py: _event_stream()`
  (line 454), which replays `manager.events(run_id, after_sequence=cursor)` (line 166)
  as Server-Sent Events, honoring `Last-Event-ID` for reconnect. It also polls
  `GET /api/agent-runs/{id}` for the terminal record.
- The React workspace renders the streamed stages (SCOPE → RETRIEVE → ANALYZE → VERIFY →
  COMPOSE), then the cited answer, evidence, and the data-driven map.

## Where a request ends up (honest outcome map)

- **`answer_ready`** — a cited answer, every claim grounded in a retrieved passage/source.
- **`abstained`** — a principled non-answer, at one of five explicit points above. Over a
  thin, auto-acquired corpus on a small local model the common point is the **analyst
  grounding** gate; see `docs/delivery/live-investigation-abstention-gap.md` for the
  measured analysis and the S1/S2 fixes that push the failure later in the chain.
- **`failed` / `interrupted`** — a genuine system/deadline error, distinct from an
  abstention and carrying a bounded error audit.

## Concurrency, persistence, resumability

- **One run at a time** (`ThreadPoolExecutor(max_workers=1)`), by design on local hardware.
- **Persisted per stage** (`AgentRunStore.save_run` after each node), so a crash resumes
  from the last completed stage — the graph nodes skip work already recorded on the run.
- **Every model call recorded** (`record.modelCalls`) with input/output hashes, for a
  reproducible audit of exactly what produced each result.
