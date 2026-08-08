# Phase E: Real LLM Agent Core — Sub-Plan Tracker

Tracks the E0-E9 sequence defined in `docs/ai-core-instructions/05_PHASE_E_AI_CORE_IMPLEMENTATION_PLAN.md` and recorded in `docs/decisions/ADR-003-llm-agent-system-is-product-core.md`. Each sub-plan is approved individually, same discipline as Phase C's C0-C3 and Phase D0's D0.1-D0.6 — see `plans/current-phase.md` for the live, detailed status of whichever sub-plan is currently in progress; this document is the stable index across all of them.

`docs/ai-core-instructions/06_CLAUDE_CODE_EXECUTION_INSTRUCTIONS.md`'s documentation-updates list also names a `docs/delivery/phase-e-validation-plan.md` — deferred until E7 (the evaluation harness) actually exists to write a validation plan around; writing it now would be a template with nothing real to validate against, the same category of premature scaffolding this project has consistently avoided (e.g. `InvestigationTimelinePlan` was deliberately left out of D0.2 until D0.3's UI existed to consume it).

| Sub-plan | Scope | Status |
|---|---|---|
| E0 | Reconcile repository state, add the instruction set to the repo, ADR, roadmap replacement, checkpoint commit | **Complete** — `43d2b94` |
| E1 | `ModelProvider` protocol, `DeterministicModelProvider`, `OllamaModelProvider`, error taxonomy, bounded retry policy, provider-billed cost recording, tested-but-unwired `AgentRunRecord`/`AgentRunStatus` scaffold | **Complete** — see `plans/current-phase.md` for the full write-up. One real smoke-test call has since been made against a real local Ollama daemon (`docs/delivery/phase-e1-real-model-smoke-test-report.md`) — the wiring is proven end to end, but no agent-run has ever actually run; that waits on E3+. |
| E2 | Corpus service + typed deterministic tools (`search_passages`, `get_source_metadata`, `compare_sources`, `get_claim_evidence`, `find_counterevidence`, `get_relationship_evidence`, `trace_relationships`, `get_timeline_context`, `get_actor_knowledge_state`, `get_map_context`) over existing `GeneratedInvestigation` packages | **Implemented and verified; not yet committed** — see `plans/current-phase.md`, `docs/ai/tool-registry.md`, and the implementation report. No model calls. Tests cover both built-in corpora and synthetic valid corpora with overlapping IDs. `compare_perspectives`/`find_conflicts`/`get_research_gaps` remain deferred because their backing collections are empty/untyped. |
| E3 | Investigation Planner + Evidence Analyst | Not started |
| E4 | Historical Critic + Investigation Guide, bounded critique/retrieval loop, citation/action validators | Not started |
| E5 | FastAPI + streaming agent runs (first HTTP boundary this project has ever had) | Not started |
| E6 | Real Ask-panel integration, replacing `AskTab.tsx`'s disclosed placeholder | Not started |
| E7 | Evaluation harness — benchmark registry, baseline/RAG/multi-agent runners, regression reports, `docs/delivery/phase-e-validation-plan.md` | Not started |
| E8 | Domain generalization — a second small benchmark corpus, no-topic-branching checks, holdout corpus | Not started |
| E9 | `docs/ai/` learning documentation finalized | In progress (opened at E1; entries accumulate through E9) |

## Phase gate (unchanged from document `01` §7 / `05`'s Completion gate)

Phase E does not pass on one corpus or one question working. Required before Phase E is considered complete: the real agent workflow operates across at least two materially different corpora; unsupported questions abstain; citation validity is measured; map actions validate; no topic-specific application branching exists; the agent workflow is compared against single-prompt and basic-RAG baselines; results and lessons are documented (`docs/ai/learning-log.md`).
