# Agent Architecture (Phase E)

Restates `docs/ai-core-instructions/02_AGENT_ARCHITECTURE.md`'s four-agent contracts as the actual target `backend/src/chronicle/ai/` is being built to serve — this is the living, code-adjacent version; the instruction-set document is the frozen source. See `docs/decisions/ADR-003-llm-agent-system-is-product-core.md` for why this exists at all.

## Status as of Phase E2

The model-provider foundation (`ai/models/`, E1) and the deterministic corpus/tool layer (`corpus/`, `ai/tools/`, E2 — full detail in `docs/ai/tool-registry.md`) both exist. **No agent exists yet.** Investigation Planner, Evidence Analyst, Historical Critic, and Investigation Guide remain E3 and E4 work, sequenced separately. E2 makes no model calls of any kind — it is the deterministic retrieval layer the future Planner will call into, not a step toward the Planner itself.

## The four roles, and what E1+E2 already support for them

| Role | Responsibility | What exists for it |
|---|---|---|
| Investigation Planner | Converts a question + workspace context into a typed `InvestigationPlan` | `ModelProvider.generate_structured(response_model=InvestigationPlan, ...)` (E1); `ai.tools.build_default_registry()`'s 10 tools to plan calls against (E2) — the `InvestigationPlan` contract type itself is E3 work |
| Evidence Analyst | Builds a structured `AnalysisDraft` from retrieved evidence | Same `generate_structured` call shape; now has real retrieved evidence to analyze via `search_passages`/`get_claim_evidence`/`get_relationship_evidence` (E2) — `AnalysisDraft` itself is E3 work |
| Historical Critic | Produces a `CriticDecision` (approve/downgrade/reject/abstain) challenging the Analyst's draft | Same; `find_counterevidence`/`trace_relationships` (E2) give it something concrete to check a draft against — the bounded retrieve/critique loop itself is E4 orchestration, not built yet |
| Investigation Guide | Turns critic-approved material into a user-facing `AgentAnswer` with citations and typed `AssistantAction`s | Same; `AssistantAction` itself is already fully specified (`docs/product/map-first-workspace-instructions.md` §15) and unchanged by this work; `get_map_context` (E2) is what will resolve a map action's referenced IDs |

## The typed tool layer (E2)

`chronicle.corpus` (a provider-independent, read-only `InvestigationCorpus` protocol over an existing `GeneratedInvestigation` package, backed today by `PackageBackedCorpus`) and `chronicle.ai.tools` (10 deterministic tools — `search_passages`, `get_source_metadata`, `compare_sources`, `get_claim_evidence`, `find_counterevidence`, `get_relationship_evidence`, `trace_relationships`, `get_timeline_context`, `get_actor_knowledge_state`, `get_map_context`). A future Planner discovers compact, serializable, corpus-aware contracts through `ToolRegistry.list_specs()`; it does not import implementations or receive Python dataclasses. No database — the corpus is the validated package's embedded records. Tool execution remains bound to that current package and every failure carries a completed audit record. Full detail lives in `docs/ai/tool-registry.md`.

Every one of the four roles will call `generate_structured()` on whatever `ModelProvider` is configured (`DeterministicModelProvider` in tests, `OllamaModelProvider` in development) — no role-specific provider code exists or is planned; role-specific behavior lives entirely in each agent's prompt and response-model contract, not in the provider layer (`AGENTS.md` §4's deterministic/LLM boundary).

## Orchestration shape (E1 scaffolding only)

`AgentRunRecord` (`orchestration/run_models.py`) defines the *shape* a run's question, target investigation/scene, status (`orchestration/statuses.py`'s `AgentRunStatus`), and list of `ModelCallRecord`s will eventually be recorded in — stated precisely because "persists" overstates what exists today: nothing in E1 writes an `AgentRunRecord` to disk or any other durable store, and nothing constructs one outside its own tests (`backend/tests/ai/orchestration/test_run_models.py`, which check valid construction, required-field enforcement, and the status enum's supported values). This is deliberately **not** wired to `workflow/engine.py`'s `run_pipeline()` — that engine's fixed linear `StageName` sequence produces a new `GeneratedInvestigation` package; an agent run answers a question against a package that already exists, via a dynamic, bounded tool-calling loop with a different shape entirely. `chronicle.ai.orchestration` reuses `engine.py`'s *patterns* (file-based record persistence, `createdAt`/`updatedAt`/`touch()`, hash-based idioms where relevant) as a sibling module, not its code path or its actual storage — the actual runner, and the actual durable storage of the records it produces, are both E3/E4 work: the thing that drives Planner → tools → Analyst → Critic → (bounded retry loop) → Guide, catches failures, and writes real `AgentRunRecord`s somewhere.

## No autonomous agent swarms

`AGENTS.md` §4 and `docs/ai-core-instructions/02_AGENT_ARCHITECTURE.md` §1 both bind here identically: exactly four bounded roles, typed input/output contracts, a small deterministic tool layer (E2) the Planner calls into rather than open-ended free-form action, and a small bounded retry/critique loop (`orchestration/policies.py`'s `MAX_STRUCTURED_OUTPUT_ATTEMPTS`), not an unbounded agent loop. Do not add a fifth agent role until evaluation (E7) proves a need.
