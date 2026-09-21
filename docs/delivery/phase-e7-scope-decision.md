# Phase E7 — Scope Decision Record

**Status:** Slice 1 (E7.1–E7.5, the deterministic spine) **delivered**; Slice 2 (live Qwen gate + human review) deferred, not started
**Companion:** [`phase-e7-evaluation-harness-plan.md`](./phase-e7-evaluation-harness-plan.md) (full specification), [`phase-e-validation-plan.md`](./phase-e-validation-plan.md) (review protocol)
**Purpose:** reconcile the approved E7 plan with the code as it stands, right-size it for a solo developer, and define the first shippable slice. This record governs where it differs from the companion plan; everything it does not touch carries over from the companion plan unchanged.

## Why this record exists

The E7 harness plan was written against the E6 architecture and assumes a multi-person review team. Two things have moved since:

1. **Production orchestration is now `graph.py` (LangGraph).** `api/app.py` drives the graph; `graph.py` composes the existing `sequential.py` / `finalization.py` as nodes. The companion plan still describes the `full_workflow` adapter as wrapping `sequential.py` directly.
2. **The project is single-developer.** The companion plan's Reviewer A / Reviewer B / Adjudicator / Cohen's kappa apparatus is inert with one rater and adds large surface area for no measured benefit.

The 24-case benchmark, both fixture corpora (concert-of-europe + blank-cheque), and both orchestration entry points are all present and intact; E7 harness code (`contracts.py`, `strategies.py`, `runner.py`, `reporting.py`, `baseline_prompts.py`) is genuinely unstarted. There is nothing to un-build.

## Decisions

### D1 — `full_workflow` adapter executes `graph.py`, not `sequential.py`

E7 must measure the path users actually hit. Production runs the LangGraph graph, so the `full_workflow` strategy adapter runs `graph.py` (which internally composes the sequential/finalization nodes). The `planner_analyst` adapter is unaffected — it still drives the retrieval runner + Analyst and stops before Critic/Guide.

Where the companion plan names `sequential.py` / `finalization.py` as the full-workflow adapter target (its "Existing foundations" table and "Shared strategy boundary" section), read `graph.py` as the production entry point that composes them.

### D2 — Single blinded reviewer; drop the dual-review apparatus

**Kept** (protects integrity even with one reviewer):
- **Blinding** — the reviewer scores answers without knowing which strategy produced them; strategy/provider/model/latency/cost labels are stripped and answer order is shuffled with a recorded seed.
- The **typed judgment rubric** — entailment, directionality, counterevidence, temporal, action-relevance, usefulness, abstention-gap, premise-handling labels.
- All **in-code leakage / contamination guards** — gold rubric fields never reach a prompt; cross-corpus IDs fail closed.

**Cut** (meaningless or inert with a single rater):
- Reviewer B and the `flagged-critical` second-review export selection.
- Cohen's kappa and raw-agreement statistics.
- The adjudication file and adjudicator role.
- `validate-review` collapses to single-file completeness + hash + blinding-intact checks; no `--require-secondary`, no dual-file agreement.

If a second independent reviewer becomes available later, the dual-review apparatus can be restored as its own additive change — the typed judgment schema is designed to support it without a rewrite.

### D3 — First slice is the deterministic spine (E7.1–E7.5); live gate + review deferred

The harness that runs the full case × strategy matrix on the **deterministic provider** — no Ollama, no human — is the reviewable unit. It proves contracts, routing, scoring, persistence, leakage prevention, and gates without any live inference or multi-hour run. The live Qwen gate and the human review depend on it and become a separate second slice.

## Slice 1 — E7 Deterministic Spine ✅ delivered

**Outcome:** the 24 cases run through all four strategies under one provider-independent runner on the deterministic provider, producing byte-stable JSON + Markdown reports and evaluating every gate that does not require a human judgment. Runs in default pytest.

**Delivered (all five steps green, guard scanned `ai/evaluation`):** E7.1 `EvaluationCase` contract + `benchmarks/e7/{registry,cases}.json` + loaders with corpus-isolation/leakage validation + `load_e3_benchmark()` compat; E7.2 four strategy adapters behind `EvaluationStrategy.run(EvaluationInput) -> StrategyResult` (`full_workflow` → `graph.py`); E7.3 `ProviderIdentity` + bounded `ModelCallArtifact`, deterministic + Ollama-digest (contract-only) parity; E7.4 resumable `run_benchmark` + `chronicle evaluate run|status` (concurrency-1, atomic per-identity save, resume-on-match, stale-identity refusal on version/hash mismatch, path-traversal guard, `--cases/--strategies/--max-cases/--repeats`); E7.5 `score_result` per-result metrics + `aggregate`/`evaluate_gates` (zero-denominator → `not_applicable`, human gates → `incomplete`) + byte-stable JSON + HTML-escaped Markdown reports + single-reviewer blinded `export-review` (labels stripped, order shuffled by seed, separate key file). Full deterministic `deterministic_full` profile (24×4 = 96 identities) runs end to end via CLI and test. All Slice-1 acceptance checks pass; backend suite 842 → **891 passed**.

*Honesty note:* the deterministic provider is unscripted at the CLI, so a bare `evaluate run` records principled `runner-captured error` abstentions — it exercises the whole harness (routing, persistence, scoring, aggregation, gates, rendering, blinded export), not answer quality. Scored answer behavior per adapter is proven with scripted providers in `test_strategies.py`; live answer quality is Slice 2.

| Step | Scope | Notes vs. companion plan |
|---|---|---|
| E7.1 | Migrate the 24 cases from `benchmark.py` into `backend/benchmarks/e7/{registry,cases}.json`; `EvaluationCase` contract with semantic/usefulness/action rubric fields; loader with corpus-isolation + leakage validation; retain `load_e3_benchmark()` compat export. | Unchanged. |
| E7.2 | Four adapters behind `EvaluationStrategy.run(EvaluationInput) -> StrategyResult`: `single_prompt`, `basic_rag`, `planner_analyst`, `full_workflow`. | `full_workflow` targets `graph.py` (D1). |
| E7.3 | Provider identity + bounded `ModelCallArtifact` contract; deterministic-provider parity. | Real Ollama digest capture rides the contract but is only *exercised* in Slice 2. |
| E7.4 | Resumable runner + `evaluate run` / `evaluate status` CLI: concurrency-1, atomic per-identity save, resume-on-match, stale-identity refusal, `--cases` / `--strategies` / `--max-cases`. | Unchanged. |
| E7.5 | Per-result + aggregate metrics; JSON + escaped-Markdown reports; gate evaluation on deterministic data; typed rubric contract + blinded `export-review` + single-reviewer `score` path. | Human-only metrics (semantic entailment, usefulness) render `incomplete` / `not_applicable`. Review apparatus right-sized per D2. |

**Sequencing catch — guard extension follows the data migration.** The anti-topic-branching guard does not currently scan `ai/evaluation`, which is why today's `benchmark.py` (questions embedding real actor/event names) does not trip it. `ai/evaluation` is added to `SCANNED_PACKAGES` **only after** E7.1 moves case content into `benchmarks/e7/cases.json` (data is the sanctioned carve-out, like fixtures and `corpus/manifest.py`) and leaves `benchmark.py` a topic-neutral loader. Adding it earlier trips the guard on the harness's own benchmark code.

**Slice 1 acceptance:**
- `deterministic_full` profile (24 cases × 4 strategies) runs green in default pytest with no Ollama.
- Reports are byte-stable for identical inputs.
- Leakage / cross-corpus / rubric-in-prompt tests fail closed.
- Anti-topic-branching guard is green with `ai/evaluation` scanned.
- Interrupted deterministic run resumes without repeating completed identities.

## Slice 2 — E7 Live Gate & Review (deferred, scoped later)

- **E7.6** live `qwen_smoke` preflight → `qwen_gate` (10 cases) + `qwen_stability` (2 cases × 3 repeats) sequential runs on Ollama `qwen2.5:7b-instruct`; blinded exports. Measured 2–4 hr wall time on the recorded hardware.
- **E7.7** single blinded human review (D2) of every gate answer; completeness + hash + blinding validation.
- **E7.8** score reviewed candidate, compare vs. canonical (or bootstrap), record whether Critic/Guide are empirically justified, promote canonical JSON/Markdown, update trackers.

Slice 2 is scoped into its own plan once Slice 1 lands, because it depends on the spine and on a live model run that cannot be part of the default test suite.

## Unchanged from the companion plan

Explicit exclusions, the metric definitions and computation conventions, the fairness controls, the threshold/gate values, the failure-mode handling, and the security/integrity boundaries all carry over verbatim. No new Python dependency is justified.

## Open items for Slice 1 planning

- Confirm `graph.py` exposes (or can cheaply expose) a call boundary the `full_workflow` adapter can invoke without duplicating orchestration — inspect before writing E7.2.
- Confirm the deterministic provider can satisfy the E7.3 identity/artifact contract with a stable synthetic digest.
