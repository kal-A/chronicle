# Failure modes and engineering trade-offs

Chronicle's known limitations and the deliberate decisions behind them, stated so they
survive scrutiny. Each entry separates **what can fail / is limited**, **how Chronicle
handles it today**, **why the current design was chosen**, and **what remains
unresolved**. Every claim is anchored to code or to a verified companion document
([`request-trace.md`](./request-trace.md), [`architecture-diagram.md`](./architecture-diagram.md),
[`verification-and-abstention.md`](./verification-and-abstention.md),
[`../delivery/live-investigation-abstention-gap.md`](../delivery/live-investigation-abstention-gap.md),
`../decisions/ADR-003`). Nothing here is aspirational.

---

## 1. Abstention behavior

**Can fail / limited.** A run can end without an answer (`ABSTAINED`) at five explicit
points: an invalid or out-of-scope plan, an unusable retrieval bundle, an ungroundable
analyst draft, a failed critic decision, or a guide that cannot compose from approved
statements (see the diagram's validation spine and `graph.py`'s conditional edges). The
honest cost: a request that *could* be answerable can still abstain when the local model
underperforms at one of these gates — an abstention is not proof that no answer exists.

**Handled by.** Abstention is a first-class, audited outcome, not an error. The mandatory
cases are enumerated in [`verification-and-abstention.md`](./verification-and-abstention.md)
("Mandatory Abstention Cases"), and each abstaining node records a `REJECTED`/`ABSTAINED`
stage with a reason on the run record. The system states a limitation rather than
fabricating content.

**Why chosen.** For historical research, a wrong confident answer is worse than a
principled non-answer. Abstention is the deterministic backstop that makes "grounded or
silent" enforceable regardless of model quality.

**Unresolved.** Abstention is currently binary at each gate — there is no graded
"partial answer with explicit gaps" surfaced to the live investigation user beyond the
`partial` verification outcome. Distinguishing "no answer possible" from "this model
couldn't get there" is not exposed to the end user.

## 2. Retrieval and corpus limitations

**Can fail / limited.** An auto-acquired corpus is a **draft**: passages + a thin
timeline, with **no synthesized claims / relationships / knowledge-states**. Over that
shape most typed tools are correctly filtered out (`available_tool_specs`), leaving
passage search as effectively the only answer-bearing tool — so a plan that picks a
map/timeline tool retrieves nothing. Retrieval is also hard-bounded (per-tool result
cap, aggregate character/result caps, a deadline), so evidence is deliberately partial.

**Handled by.** A **guaranteed retrieval floor** (`InvestigationRunner._augment_with_floor`,
enabled via `retrieval_floor=True` in `create_default_app`, `api/app.py`) appends one
bounded `search_passages(question)` whenever the plan omits it, so the analyst sees the
corpus text even under a weak plan. Planner steering (`planner_prompt.py`) biases
direct/descriptive questions toward passage search. Budgets live in
`AgentExecutionPolicy` (`policies.py`); the live path tightens them further
(`maxResultsPerTool=2`, `maxAggregateRetrievalCharacters=8000` in `app.py`). Snippets and
metadata are never treated as evidence.

**Why chosen.** The retrieval floor is model-independent: it fixes "search anything" at
the retrieval layer rather than trusting a small model to plan correctly. Tight budgets
keep prompts inside the local context window and keep grounding checkable.

**Unresolved.** Acquisition stops at a draft corpus; the richer typed tools (relationships,
actor-knowledge, counterevidence) have little to operate on for live topics. Corpus
synthesis (option C in the abstention-gap scope) is deferred.

## 3. Local model and hardware constraints

**Can fail / limited.** Even with correct retrieval, a small local model can fail to
*ground* an answer from good passages. Measured on a live "Anaconda Plan" corpus (41
passages, correct passages retrieved), a `qwen2.5:3b` analyst still abstained — small-model
**analyst capacity**, not a retrieval bug. The more capable `qwen2.5:7b` grounds answers
but needs ~5 GB and OOMs on a ~14.7 GB machine with only ~1.8 GB free.

**Handled by.** The model is configurable at runtime (`CHRONICLE_OLLAMA_MODEL` /
`resolve_model_from_env` in `ai/models/ollama.py`), so a constrained machine can run 3B
and a capable host can run 7B without code changes. The abstention spine ensures the weak
model abstains rather than hallucinates. The constraint is documented in
[`../delivery/live-investigation-abstention-gap.md`](../delivery/live-investigation-abstention-gap.md)
(slice S3, blocked on hardware).

**Why chosen.** Free/local-only is a hard product constraint (`AGENTS.md` §5): no paid
inference, no API keys. Running open-weight models on Ollama is the cost of that
guarantee, and it trades model quality for zero-cost reproducibility.

**Unresolved.** A live *cited answer* over an auto-acquired corpus needs the 7B analyst,
which does not fit this machine's free RAM. This is a hardware/model constraint, not an
engine defect — the retrieval chain up to the analyst is verified sound.

## 4. Deterministic composition and validation

**Can fail / limited.** LLM output is inherently untrustworthy for a research tool:
invented citations, unsupported claims, overstated causation. A pure "trust the model"
pipeline would fail silently.

**Handled by.** Every model call is bracketed by a deterministic gate (the validation
spine): planner tool-authorization + arg-schema (`_validate_candidate`), retrieval
capability/budget preflight (`_preflight_calls`/`_execute_calls`), analyst citation
grounding (`GroundingValidationReport`), critic decision validation
(`validate_critic_decision`), and a guide that composes the final answer **only from
approved, grounded statements** (`guide.py`). Model self-reported confidence never
substitutes for a check (`verification-and-abstention.md`).

**Why chosen.** ADR-003 fixes the architecture as **explicit state machines, not an
autonomous swarm**: bounded control flow the system can audit. Determinism at the seams is
what makes an LLM core defensible for history — the model proposes, deterministic code
disposes.

**Unresolved.** Grounding is checked at the citation/reference level, not semantic
entailment — a citation that *resolves* to a real passage but is a weak paraphrase can
still pass the reference gate. Deeper semantic-support validation is future work.

## 5. External and network-dependent behavior

**Can fail / limited.** Live acquisition depends on free third-party APIs (Wikipedia,
Gutenberg, Internet Archive). Sources can 403, rate-limit, go offline, or return
namesakes; results are non-deterministic across time.

**Handled by.** Per-source failure is **non-fatal**: a flaky/403 source is skipped and
recorded as partial acquisition rather than aborting the build; a per-source outage
surfaces as `502`, not an opaque `500` (`api/app.py`). Fetched text is stored in a
content-addressed `FetchCache`, so repeat runs are stable and cheap. Discovery ranks by
topic relevance (`discovery.py: _select_by_relevance`) to drop namesakes. Network- and
model-dependent tests are **deselected from the default suite and CI** (the
`live_network_integration` and `local_ollama_integration` markers in `pyproject.toml`;
see [`../../.github/workflows/README.md`](../../.github/workflows/README.md)), and
self-skip when the dependency is unreachable.

**Why chosen.** Free-only sourcing means accepting third-party variability; caching +
partial acquisition + relevance ranking make it usable without paid infrastructure.
Excluding live/model tests from CI keeps CI deterministic and credential-free.

**Unresolved.** Answer quality is bounded by what free sources expose for a topic; there
is no paid deep-search fallback (would require explicit approval per `AGENTS.md` §5).
Live-integration correctness is only asserted by opt-in local tests, not CI.

## 6. Concurrency and throughput

**Can fail / limited.** Only **one investigation runs at a time**
(`ThreadPoolExecutor(max_workers=1)`, `manager.py`). Concurrent requests queue; a long
CPU-bound acquisition + inference run is minutes-scale and blocks the next.

**Handled by.** By design for local hardware: LangGraph owns per-run control flow, the
manager owns the single global queue. Runs are async with a run record and SSE streaming,
and each stage is persisted (`AgentRunStore`) so a run is resumable and auditable rather
than fast.

**Why chosen.** On a CPU-only, memory-constrained machine, parallel inference would
thrash. Serial execution trades throughput for predictable resource use and a clean audit
trail — the right trade for a local research tool, not a production multi-tenant service.

**Unresolved.** No horizontal scaling or multi-run concurrency; throughput is explicitly
out of scope until deployment constraints justify it (`system-overview.md`).

---

*Scope note:* latency figures and the benchmark breakdown are intentionally omitted here —
they belong to the performance report (roadmap #3), not this limitations document.
