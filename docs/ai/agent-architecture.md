# Agent Architecture (Phase E)

Restates `docs/ai-core-instructions/02_AGENT_ARCHITECTURE.md`'s four-agent contracts as the actual target `backend/src/chronicle/ai/` is being built to serve — this is the living, code-adjacent version; the instruction-set document is the frozen source. See `docs/decisions/ADR-003-llm-agent-system-is-product-core.md` for why this exists at all.

## Status as of Phase E5

The model-provider foundation (E1), deterministic corpus/tool layer (E2), Investigation Planner and Evidence Analyst (E3), Historical Critic plus Investigation Guide (E4), and the FastAPI/streaming runtime (E5) now exist locally. All four roles use typed structured output and deterministic post-generation gates. The workflow is strictly sequential and runs through one project-wide worker; E4 permits at most one Critic-requested retrieval call before reanalysis, and a second request becomes an explicit abstention. E5 exposes persisted run polling, SSE progress, resume, and safe-boundary cancellation. E6 still needs to connect the React Ask and investigation surfaces.

## The four implemented roles

| Role | Responsibility | What exists for it |
|---|---|---|
| Investigation Planner | Converts a question + workspace context into a typed `InvestigationPlan` | `ai/agents/planner.py`; tool calls are validated against the E2 registry and corpus snapshot before execution. |
| Evidence Analyst | Builds a structured `AnalysisDraft` from retrieved evidence | `ai/agents/analyst.py`; every exposed statement passes deterministic citation, directness, temporal, geographic, and knowledge-state grounding. |
| Historical Critic | Produces a `CriticDecision` challenging the Analyst's draft | `ai/agents/critic.py`; every statement is accepted, downgraded, rejected, or the run retrieves once/abstains. The Critic cannot silently omit a statement. |
| Investigation Guide | Turns only approved material into an `AgentAnswer` and typed workspace actions | `ai/agents/guide.py`; approved text remains exact, canonical citations are reattached deterministically, and every action ID is checked against the current validated package. |

## The typed tool layer (E2)

`chronicle.corpus` (a provider-independent, read-only `InvestigationCorpus` protocol over an existing `GeneratedInvestigation` package, backed today by `PackageBackedCorpus`) and `chronicle.ai.tools` (10 deterministic tools — `search_passages`, `get_source_metadata`, `compare_sources`, `get_claim_evidence`, `find_counterevidence`, `get_relationship_evidence`, `trace_relationships`, `get_timeline_context`, `get_actor_knowledge_state`, `get_map_context`). A future Planner discovers compact, serializable, corpus-aware contracts through `ToolRegistry.list_specs()`; it does not import implementations or receive Python dataclasses. No database — the corpus is the validated package's embedded records. Tool execution remains bound to that current package and every failure carries a completed audit record. Full detail lives in `docs/ai/tool-registry.md`.

Every role calls `generate_structured()` on the configured `ModelProvider` (`DeterministicModelProvider` in ordinary tests, `OllamaModelProvider` in opt-in local smoke tests). Role behavior lives in its prompt, response contract, and deterministic validator—not provider-specific branches.

## Orchestration and persistence

`InvestigationRunner` executes the bounded E3 tool plan. `FinalizationRunner` executes Critic → optional single retrieval → reanalysis → Critic → Guide. `SequentialAgentWorkflow` resumes from the last durable artifact and checks cancellation between named stages. `AgentRunManager` owns exactly one worker and a bounded replayable progress journal. `AgentRunStore` atomically persists the plan, retrieval bundle, analysis, grounding report, all Critic decisions/validations, final answer/action validation, stage records, model calls, tool calls, latency, retries, failure causes, cancellation, and abstention state. `chronicle.api` exposes this through a deliberately small FastAPI surface with polling and SSE. Private chain-of-thought is never requested or stored. This remains deliberately separate from `workflow/engine.py`, whose fixed stage sequence generates packages rather than answering questions against them.

## No autonomous agent swarms

`AGENTS.md` §4 and the frozen architecture instructions bind here identically: exactly four bounded roles, typed input/output contracts, ten deterministic tools, at most two structured-generation attempts per call, and at most one Critic-requested retrieval. Do not add a fifth role until E7 evaluation proves a need.
