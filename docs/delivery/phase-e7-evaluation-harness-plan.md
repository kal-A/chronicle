# Phase E7 Plan — Comparative Agent Evaluation Harness

**Status:** approved scope, implementation not started
**Execution model:** one bounded workstream, executed sequentially
**Phase outcome:** Chronicle can run the same reviewed historical questions through four answer strategies, save reproducible results, score safety and usefulness, and state with evidence whether the four-agent workflow is justified.

## Why E7 exists

E6 proved that local Qwen can complete Chronicle's real Planner → retrieval → Analyst → Critic → Guide path and can produce a cited answer from selected evidence. It also exposed the two risks E7 must quantify: a semantically reversed statement can still cite a related passage, and a safe abstention can be correct but unhelpful. One successful demonstration is therefore not enough to close Phase E.

E7 evaluates the AI system over the two existing, materially different package-backed corpora:

- `blank-cheque-golden`: communications, actor knowledge, crisis chronology, disputed causation;
- `concert-of-europe-1814-1822`: doctrine, intervention, source comparison, relationship classification.

The harness compares exactly four strategies:

1. `single_prompt` — one Qwen call receives the question and a bounded, eligible corpus context; no retrieval tool or agent role is used.
2. `basic_rag` — deterministic `search_passages(question)` retrieval under the production result/character caps, followed by one Qwen answer call.
3. `planner_analyst` — the existing Planner, typed tools, retrieval runner, grounding validation, and Analyst; it stops before Critic and Guide.
4. `full_workflow` — the production Planner → retrieval → Analyst → Critic → Guide workflow and final answer validator.

All strategies use the same corpus snapshot, case question, Qwen model, temperature, context limit, eligibility rules, and provider audit records. A strategy may use fewer calls or less evidence by design, but may not receive hidden gold labels or broader source access than another strategy.

## Scope

E7 delivers:

- a versioned, file-backed benchmark registry;
- an expanded evaluation-case contract built from the existing 24 E3 cases rather than a parallel case taxonomy;
- four strategy adapters behind one evaluation protocol;
- a sequential, resumable benchmark runner;
- deterministic metrics and explicit human-review fields for semantic judgments that software cannot safely infer;
- machine-readable JSON and readable Markdown reports;
- regression gates and a checked-in canonical Qwen report;
- default deterministic tests plus opt-in local-Qwen integration runs;
- a documented architecture decision based on measured quality, safety, latency, tokens, and provider-billed cost.

## Explicit exclusions

E7 does not add or change:

- live internet research, scholarly-database access, downloads, scraping, PDF/OCR processing, or MCP connections;
- embeddings, reranking, vector storage, SQL/database persistence, or a new corpus;
- new frontend UI, map rendering, or Ask-panel presentation;
- paid or hosted model providers;
- fine-tuning or training data generation;
- topic-specific application branching;
- production agent prompts except where a measured E7 failure is separately approved as a follow-on correction;
- commits or pushes without a separate explicit instruction.

## Existing foundations to reuse

| Existing artifact | E7 use |
|---|---|
| `backend/src/chronicle/ai/evaluation/benchmark.py` | Existing 24 answer-free cases and cross-corpus reference validation |
| `backend/src/chronicle/ai/evaluation/metrics.py` | Existing plan, retrieval, citation, abstention, and budget measurements |
| `backend/src/chronicle/ai/orchestration/sequential.py` | Production full-workflow adapter |
| `backend/src/chronicle/ai/orchestration/runner.py` | Typed retrieval and policy enforcement |
| `backend/src/chronicle/ai/orchestration/finalization.py` | Critic/Guide workflow and validated finalization |
| `backend/src/chronicle/ai/models/protocol.py` | Provider-independent strategy execution |
| `backend/src/chronicle/ai/models/metadata.py` | Per-call latency, tokens, attempts, model/prompt versions, and provider cost |
| `backend/src/chronicle/ai/contracts/answer.py` | Typed citations, answer status, actions, and deterministic action-reference validation |
| `backend/src/chronicle/corpus/manifest.py` | The two package-backed benchmark corpora and corpus isolation |
| `backend/tests/ai/integration/test_e6_ollama_workflow_smoke.py` | Opt-in local-Qwen marker and health-gated integration pattern |

No new Python dependency is justified. Pydantic, pytest, the standard library, and the existing provider/orchestration contracts cover the phase.

## Planned artifacts and file ownership

### Benchmark data

- `backend/benchmarks/e7/registry.json` — benchmark version, case file, corpus IDs, profiles, thresholds, and case-set hash.
- `backend/benchmarks/e7/cases.json` — all 24 migrated cases, including machine-checkable expectations and reviewer rubrics; no target essay or model-copyable reference answer.
- `backend/benchmarks/e7/review-template.json` — typed human-judgment labels and completeness rules, not filled gold answers.

### Evaluation code

- `backend/src/chronicle/ai/models/protocol.py` — provider-neutral identity/audit contract additions.
- `backend/src/chronicle/ai/models/metadata.py` — typed model digest/version and bounded per-attempt artifact metadata.
- `backend/src/chronicle/ai/models/ollama.py` — real Ollama model digest/version capture and bounded attempt artifacts.
- `backend/src/chronicle/ai/models/deterministic.py` — deterministic parity for the same provider audit contract.
- `backend/src/chronicle/ai/evaluation/contracts.py` — strategy, case, observation, judgment, aggregate, gate, and report contracts.
- `backend/src/chronicle/ai/evaluation/benchmark.py` — registry loading, version/hash validation, case/reference validation, and compatibility export for `load_e3_benchmark()`.
- `backend/src/chronicle/ai/evaluation/strategies.py` — the four adapters and shared normalized `StrategyResult` boundary.
- `backend/src/chronicle/ai/evaluation/baseline_prompts.py` — versioned single-prompt and retrieval-answer prompts with no benchmark answers.
- `backend/src/chronicle/ai/evaluation/runner.py` — sequential/resumable case × strategy execution and bounded audit-artifact persistence.
- `backend/src/chronicle/ai/evaluation/metrics.py` — per-result and aggregate scoring.
- `backend/src/chronicle/ai/evaluation/reporting.py` — threshold evaluation and deterministic JSON/Markdown rendering.
- `backend/src/chronicle/ai/evaluation/__init__.py` — stable public exports.
- `backend/src/chronicle/cli/evaluation.py` — evaluation command implementation isolated from generation commands.
- `backend/src/chronicle/cli/main.py` — thin `chronicle evaluate ...` parser wiring.
- `.gitignore` — ignores transient `backend/evaluation-runs/` artifacts while retaining approved canonical reports.

### Tests and phase evidence

- `backend/tests/ai/evaluation/test_contracts.py`
- `backend/tests/ai/evaluation/test_benchmark.py`
- `backend/tests/ai/evaluation/test_strategies.py`
- `backend/tests/ai/evaluation/test_runner.py`
- `backend/tests/ai/evaluation/test_metrics.py`
- `backend/tests/ai/evaluation/test_reporting.py`
- `backend/tests/ai/models/test_e7_provider_audit.py`
- `backend/tests/ai/integration/test_e7_ollama_evaluation.py`
- `docs/delivery/phase-e-validation-plan.md`
- `docs/delivery/phase-e7-evaluation-report.json`
- `docs/delivery/phase-e7-evaluation-report.md`
- `plans/current-phase.md`
- `docs/delivery/phase-e-ai-core-plan.md`

## Evaluation-case schema

`EvaluationCase` extends the current answer-free `BenchmarkCase`. The JSON contract uses `extra="forbid"`, immutable values, bounded arrays/text, and these fields:

| Field | Purpose |
|---|---|
| `caseId`, `legacyAliases`, `benchmarkVersion` | Stable topic-neutral slug, old `bc-##`/`coe-##` lookup aliases, and schema lineage |
| `corpusId`, `question`, `category` | Corpus-isolated input and question class |
| `profiles` | Membership in `deterministic_full`, `qwen_gate`, or `qwen_full` |
| `acceptableTools` | Planner/tool-selection scoring |
| `requiredEvidenceIds`, `forbiddenEvidenceIds` | Evidence recall, contamination, and leakage gates |
| `expectedCitationRoles` | Supporting/context/counterevidence correctness |
| `requiresCounterevidence` | Counterevidence inclusion gate |
| `temporalConstraints` | Event-order or date-bound checks |
| `expectedAbstention` | Abstention recall/false-abstention scoring |
| `unacceptableClaims` | Explicit premise/causal overstatement tripwires |
| `expectedActionTypes`, `allowedActionTargetIds` | Action relevance and target validity |
| `semanticChecks` | Reviewed proposition rubrics: subject, relation, object, polarity, temporal qualifier, directionality-critical flag, and supporting record IDs |
| `usefulnessCriteria` | Case-specific checklist such as answering the direct question, preserving uncertainty, or identifying missing coverage |
| `reviewNotes` | Historical reason for the rubric, never an answer to copy |

`caseId` uses the generic pattern `^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$` and describes the reasoning behavior rather than encoding a corpus abbreviation or sequence number (for example, `direct-reported-assurance` and `actor-knowledge-supported-awareness`). The current `bc-##`/`coe-##` values move to `legacyAliases`; question text and evidence expectations do not change.

`SemanticCheck` must use record IDs and normalized relation labels, not target prose. For example, the Blank Cheque assurance case records Austria-Hungary as the supported party and Germany as the supporting party. Reversing those roles is a critical directionality error even if the cited passage contains both actors.

### Typed human-judgment contract

`HumanReviewFile` is a Pydantic-validated artifact with `reviewSchemaVersion`, `benchmarkRunHash`, `reviewerId`, `reviewerRole`, `reviewStartedAt`, `reviewCompletedAt`, `blindingManifestHash`, `reviewFileHash`, and one `HumanResultJudgment` for every opaque review item. `reviewerId` is a stable non-personal identifier; no participant name or email is stored. The file hash is computed over canonical JSON with `reviewFileHash` omitted, then inserted and verified before scoring.

Each `HumanResultJudgment` contains:

- `reviewItemId` and `caseSlug`, but no strategy/provider/model label;
- `usefulnessScore`: `0 | 1 | 2` plus a required rationale;
- `abstentionGap`: `correctly_stated | incorrectly_stated | omitted | not_applicable`;
- `premiseHandling`: `corrected | repeated_as_fact | avoided_without_correction | not_applicable`;
- a judgment for every normalized statement;
- a judgment for every applicable temporal, counterevidence, and action check;
- `reviewComplete: true`, allowed only when every required child judgment is present.

`HumanStatementJudgment` identifies the normalized statement and semantic check, then records `entailment: entailed | partially_entailed | contradicted | unverifiable`, `directionality: correct | reversed | ambiguous | not_applicable`, and the exact cited record IDs inspected. `partially_entailed` receives no full-entailment credit and counts as not fully supported for hard safety gates; its answer may receive usefulness `1`, never `2`, when the missing qualification is material.

`CounterevidenceJudgment` is `accounted_for | mentioned_only | omitted | mischaracterized | not_applicable`; only `accounted_for` passes. `TemporalJudgment` is `correct | incorrect_order | time_role_collapsed | omitted | not_applicable`; only `correct` passes. `ActionJudgment` is `relevant | plausible_but_unhelpful | misleading | not_applicable`; only `relevant` contributes action-eligibility coverage, while deterministic reference validation separately determines action validity.

Two reviewer files are required for the repeated stability profile **and** every `qwen_gate` item where `directionalityCritical=true` or `requiresCounterevidence=true`. The Reviewer-B gate export must therefore include `direct-reported-assurance`, `counterevidence-extension-limits`, and `disputed-causal-interpretations` (`bc-07`), plus any other case carrying either flag; export validation compares the selected set against registry flags and rejects omissions. The scorer reports raw agreement and Cohen's kappa for entailment/directionality/counterevidence labels; disagreements are adjudicated into a third typed file with both source review hashes and an `adjudicatorId`. Non-critical main-gate items may use one completed review, but every flagged item must be double-reviewed and adjudicated when reviewers disagree.

The loader rejects duplicate IDs, unknown corpora, cross-corpus record IDs, overlapping required/forbidden evidence, unresolved action targets, a counterevidence requirement without the counterevidence role, an abstention case with mandatory positive-answer criteria, or registry/case hashes that do not match.

## Benchmark registry and profiles

`registry.json` is data, not corpus-specific control flow. It declares:

- registry and case-schema versions;
- relative case file and SHA-256 hash;
- the two permitted corpus IDs;
- strategy IDs;
- fixed generation settings and execution policy name;
- profile membership;
- regression thresholds;
- canonical report schema version.

Profiles:

- `deterministic_full`: all 24 cases × all four strategies using the deterministic provider. This runs in default pytest and proves contracts, routing, scoring, persistence, leakage prevention, and gates without live inference.
- `qwen_smoke`: two cases (one per corpus) × all four strategies, one repetition. This is the cheapest live contract/progress check and does not establish quality.
- `qwen_gate`: ten reviewed cases × all four strategies, one repetition, sequential execution. This is the required local-Qwen quality gate and includes both supported and unsupported actor-knowledge reasoning.
- `qwen_stability`: `direct-reported-assurance` and `counterevidence-extension-limits` × Planner–Analyst/full-workflow × three repetitions. It measures repeated directionality, counterevidence, Critic-verdict, and reviewer-agreement variance without repeating the entire matrix.
- `qwen_full`: all 24 cases × all four strategies, opt-in and resumable. It produces broader research evidence but is not run by the default test command.

The required Qwen gate matrix is:

| Stable case slug (legacy alias) | Corpus | Behavior stressed | Review focus |
|---|---|---|---|
| `direct-intervention-principle` (`coe-01`) | Concert of Europe | Direct evidence | Citation entailment and quotation/paraphrase discipline |
| `timeline-congress-intervention-order` (`coe-05`) | Concert of Europe | Temporal ordering | Troppau → Laibach → Naples order; timeline actions |
| `counterevidence-extension-limits` (`coe-07`) | Concert of Europe | Counterevidence | Qualified relationship, limitations, relationship action |
| `invalid-premise-endorsement` (`coe-08`) | Concert of Europe | Invalid premise | Britain/Troppau premise correction or abstention |
| `actor-knowledge-unsupported-personal` (`coe-10`) | Concert of Europe | Actor knowledge | Abstain rather than infer Metternich's knowledge from availability |
| `direct-reported-assurance` (`bc-01`) | Blank Cheque | Direct evidence | Germany/Austria-Hungary support directionality |
| `timeline-assurance-report-order` (`bc-02`) | Blank Cheque | Temporal ordering | Assurance/report order; timeline actions |
| `actor-knowledge-supported-awareness` (`bc-03`) | Blank Cheque | Actor knowledge | Preserve actor, evidence, and time-role boundaries |
| `disputed-causal-interpretations` (`bc-07`) | Blank Cheque | Disputed interpretation | Fischer/Clark disagreement and counterevidence |
| `missing-exact-receipt-hour` (`bc-12`) | Blank Cheque | Missing evidence | Exact-hour abstention |

This is balanced across corpora and spans supported answers, abstentions, supported/unsupported actor knowledge, chronology, disagreement, relationship qualification, and action-eligible questions.

The gate is deliberately resumable because the current CPU-only E6 evidence suggests approximately one minute for each one-call baseline, several minutes for Planner–Analyst, and roughly seven to nine minutes for a complete four-agent answer. Ten cases therefore imply about 80 nominal model calls (bounded worst case 110 under existing retry/critique ceilings) and approximately two to four hours of sequential wall time on the recorded machine. `qwen_stability` adds 12 case-strategy executions and about one to two hours. These are measured estimates, not deadlines. The CLI must show completed/remaining identities after every result and support `--max-cases`, `--cases`, `--strategies`, and `--repeats`; the two-case `qwen_smoke --max-cases 2` command is the cheap preflight before either longer profile.

## Runner architecture

```text
registry + case
  → corpus snapshot and case validation
  → strategy adapter (one at a time)
  → existing ModelProvider / typed tools / orchestration
  → normalized StrategyResult + raw audit references
  → deterministic metrics
  → blinded semantic/usefulness review record
  → aggregate metrics + regression gates
  → JSON report + rendered Markdown report
```

### Shared strategy boundary

Every adapter implements `EvaluationStrategy.run(EvaluationInput) -> StrategyResult`. The result retains:

- case slug, benchmark/case hashes, corpus ID/package hash, strategy ID/implementation version, provider name/version, model name/version/digest, generation-settings hash, execution-policy hash, per-role prompt version/hash, repeat, and run identity;
- answer status and user-facing text;
- normalized answer statements and citations;
- retrieved reference index and tool records, if any;
- validated actions, if any;
- all model-call records;
- start/completion timestamps and end-to-end latency;
- structured-output/retry/failure information;
- paths and hashes for bounded audit artifacts.

The evaluation runner never rewrites a strategy's answer to make it score better. The Planner–Analyst adapter evaluates the grounded `AnalysisDraft` directly and reports actions as unavailable. The full adapter evaluates the actual validated `AgentAnswer`. Baselines use an evaluation-only structured answer contract with the same answer/citation/status limits; this contract is not a new production answer path.

`ModelProvider` remains the sole owner of model transport, retries, token/cost metadata, and validated model results; strategy adapters never call Ollama HTTP endpoints themselves. E7 does **not** promise full raw prompts or raw unparsed model responses, because current providers intentionally retain hashes/audit metadata rather than unlimited potentially sensitive corpus text. Each model attempt instead persists a bounded `ModelCallArtifact`: call identity, input/output hashes, prompt/schema/tool character counts, generation settings, token/cost/latency metadata, status/attempt count, the validated structured value when one exists, and at most a sanitized 4,000-character error/output excerpt for a rejected attempt. The report links these artifacts by hash. No provider behavior is weakened to capture more data.

### Statement normalization and mapping

The denominator for statement metrics is not inferred by splitting arbitrary prose differently per strategy:

- Single-prompt and basic-RAG answers return bounded structured `EvaluationStatement` records; each record is one normalized statement.
- Planner–Analyst uses each existing `AnalysisStatement` unchanged.
- Full-workflow uses the Critic-approved statement IDs referenced by `AgentAnswer.keyPoints` and `disagreements`; repeated IDs count once. `directAnswer` is the presentation summary and is evaluated through usefulness, while the existing deterministic answer validator must prove its text derives from approved statements.
- If any baseline statement, key point, disagreement, citation, or declarative answer span cannot map to a normalized statement ID, it is persisted as an `unmappedStatement`, enters the statement denominator, has citation coverage `0`, and is judged `unverifiable` unless a reviewer maps it to a cited proposition. It can never disappear from scoring.

`ObservedStatement` records `observedStatementId`, exact text, source field, source character start/end when applicable, origin statement IDs, citation IDs, and duplicate-group ID. Normalization preserves exact text and mapping; it does not paraphrase, merge actors, or repair directionality.

### Single-prompt context construction

The single-prompt baseline does not perform retrieval. A corpus-independent `build_single_prompt_context(corpus, policy, benchmarkVersion)` enumerates all eligible passages and their source/document metadata, then:

1. sorts sources by `SHA-256(benchmarkVersion + sourceId)`;
2. sorts passages within each source by the same hash rule;
3. selects one whole passage per source in round-robin order until the existing aggregate character ceiling would be exceeded;
4. serializes compact records containing the exact `sourceId`, `documentId`, `passageId`, eligible evidence-link IDs/roles/targets, source metadata, and unmodified passage text;
5. persists `single-prompt-context.json` with the selected IDs/text, omitted IDs/reason, serialized character count, and SHA-256 supplied-context hash.

No question tokens or topic names affect selection or ordering, no passage is truncated, and a test replaces `search_passages` with a function that raises to prove retrieval is not used. `singlePromptContextCoverage` reports required case evidence present ÷ required evidence for fairness; a missing required record remains a baseline limitation, not a hidden context substitution.

### Fairness controls

- One Qwen model/version and temperature `0` for every live strategy.
- Existing production context and output ceilings remain in force.
- Basic RAG uses the same `search_passages` implementation and the production E6 result cap.
- Single-prompt corpus context contains only eligible, corpus-local records and is capped to the same aggregate retrieval-character budget.
- Gold semantic/usefulness rubrics are loaded only by scoring/review code after strategy execution. A test fails if a rubric field reaches a prompt hash input.
- Execution is concurrency `1`; each case-strategy result is saved atomically before the next begins.
- The runner resumes only when the complete identity matches: benchmark/registry/case hash, case slug, corpus package hash, strategy ID/implementation version, provider name/version, model name/version/digest, generation-settings hash, execution-policy hash, every applicable role prompt version/hash, and repeat. Any change creates a new identity rather than mixing artifacts.
- Strategy order rotates deterministically by case to reduce systematic warm-cache bias. The order is recorded.
- One unscored Qwen warm-up call occurs before timing; the warm-up is retained in run metadata but excluded from metrics.
- Review exports replace run/case-result IDs with opaque SHA-256-derived review IDs, remove strategy/provider/model/prompt labels, and use a recorded deterministic shuffle seed to randomize answer ordering within the export. The private blinding manifest maps review IDs back to run identities and is hashed but not included in reviewer files. Reviewers retain the question, corpus title, exact answer, citations, and resolved passages needed to judge history.

## Metrics and definitions

### Grounding and historical validity

| Metric | Definition |
|---|---|
| Citation ID validity | Valid citation tuples ÷ all citations. A tuple must resolve to the exact evidence link/passage/source/target returned during that strategy run. |
| Citation coverage | Answered statements with at least one valid citation ÷ answered statements. |
| Required evidence recall | Required case evidence IDs cited ÷ required evidence IDs. |
| Forbidden evidence rate | Forbidden or cross-corpus IDs cited ÷ all cited IDs. |
| Expected citation-role precision | Valid citations whose role belongs to `expectedCitationRoles` ÷ valid citations on applicable cases. |
| Expected citation-role recall | Distinct expected roles represented by valid citations ÷ distinct `expectedCitationRoles` on applicable cases. |
| Semantic entailment | Human-reviewed normalized statements labelled `entailed` ÷ all reviewed normalized statements. `partially_entailed`, `contradicted`, and `unverifiable` remain in the denominator and receive zero full-entailment credit. |
| Critical directionality errors | Count of directionality-critical propositions with reversed subject/object, polarity, causal direction, or knowledge-holder. |
| Counterevidence satisfaction | Required counterevidence checks labelled `accounted_for` with a valid counterevidence-role citation ÷ all required counterevidence checks. |
| Temporal consistency | Temporal checks labelled `correct` ÷ all applicable temporal checks. `time_role_collapsed` explicitly fails. |

Semantic entailment and usefulness are not delegated to the answer-producing model as ground truth. The harness generates a blinded review sheet containing the answer, resolved cited passages, and case rubric. A reviewer records the labels. An optional local-Qwen judge may be saved as a non-gating diagnostic, clearly separated from human judgments.

### Answer behavior

| Metric | Definition |
|---|---|
| Supported-answer usefulness | Answerable cases scoring `2` on the reviewed rubric ÷ answerable cases. Score `2`: directly answers and meets all critical criteria; `1`: useful but materially incomplete; `0`: wrong, evasive, or unusable. |
| Abstention recall | Expected-abstention cases correctly abstained ÷ expected-abstention cases. |
| False-abstention rate | Answerable cases that abstain ÷ answerable cases. |
| Abstention quality | Correct abstentions that name the evidence gap and avoid unsupported assertions ÷ correct abstentions. |
| Premise correction rate | Invalid-premise cases that explicitly reject/correct the premise without repeating it as fact ÷ invalid-premise cases. |

### Agent and interaction behavior

| Metric | Definition |
|---|---|
| Planner tool-selection rate | Planned calls using a case-acceptable tool ÷ planned calls. |
| Unnecessary tool calls | Calls outside the case's acceptable set. |
| Critic correction delta | Planner–Analyst unsupported/contradicted statements minus full-workflow unsupported/contradicted statements on the same cases. |
| Structured-output failure rate | Model calls exhausted or rejected for malformed/schema-invalid output ÷ model calls. |
| Retry rate | Model calls with `attemptCount > 1` ÷ model calls. |
| Map-action validity | Actions passing the existing answer/action-reference validator ÷ emitted actions. |
| Action eligibility coverage | Action-eligible cases with at least one relevant, valid action ÷ action-eligible cases. Report separately because an omitted action is not the same safety failure as an invalid action. |
| Cross-corpus leakage | Any retrieved, cited, or action-target ID belonging to a corpus other than the case corpus. Report as a count and case list. |

### Performance and cost

| Metric | Definition |
|---|---|
| End-to-end latency | Wall-clock milliseconds from adapter start through validation, aggregated as median and p95 per strategy. |
| Stage/model latency | Existing stage and `ModelCallRecord.latencyMs` values, summed and reported independently from end-to-end time. |
| Token use | Sum of reported prompt/completion tokens. Missing provider usage remains `unavailable`, never zero-filled. |
| Provider-billed cost | Sum of `ProviderCost.amountUsd`. Ollama correctly reports `$0` with `no_provider_charge`; reports explicitly state that electricity, hardware, and developer time are not represented. |
| Completion/recovery | Completed cases, failures, timeouts, retries, and successful resumes per strategy. |

### Metric computation conventions

- Every aggregate includes the numerator, denominator, decimal value, applicability state, and contributing/failing case slugs. A decimal without its counts is invalid output.
- A zero denominator produces `not_applicable`, never `0`, `1`, pass, or fail. Missing provider usage produces `unavailable`. A required review/check with no judgment produces `incomplete` and blocks the applicable gate.
- An answered result with zero citations has citation validity `0/0 not_applicable` but citation coverage `0/N`, and therefore fails the coverage gate; it cannot pass by emitting nothing.
- An abstained result has no statement/citation denominator. Abstention metrics, completion, and expected behavior still apply.
- An actionless answer has action validity `0/0 not_applicable`; on an action-eligible case its action-coverage contribution is `0/1`.
- Expected citation-role metrics apply only when the case declares roles and the strategy answers. No valid citations yields role precision `0/0 not_applicable` and role recall `0/R`, which fails the role-recall gate.
- A run timeout, exhausted retry, schema failure, or unhandled adapter failure contributes `0/1` to strategy completion. Its elapsed time through failure is retained in failure-latency statistics and is not mixed into successful-answer latency; reports show successful and failed latency distributions side by side.
- Median uses the ordinary sorted midpoint (average of the two central values for an even count). p95 uses the nearest-rank convention: sorted value at one-based index `ceil(0.95 × N)`. Timeouts are reported as observed time-to-failure plus timeout category, not replaced with an invented latency.
- Provider-billed cost sums only available `ProviderCost` values. Token totals expose available-call count/total-call count; unavailable calls are never imputed.
- `criticCorrectionDelta` pairs the same case/repeat across Planner–Analyst and full workflow. It reports the difference in counts of non-entailed statements, counterevidence failures, and critical directionality failures; an unpaired result is incomplete.
- Cross-corpus leakage scans retrieved reference indexes, normalized citations, action targets, and persisted supplied-context IDs. Its denominator is all referenced IDs; any foreign ID is also a case-level hard failure.
- Repeated-live stability reports disposition agreement, directionality agreement, counterevidence agreement, and Critic-verdict variance. For three repeats, `verdictVariance = 1 - (largest verdict count / 3)`; `0` is stable and `2/3` is maximally split. Directionality/counterevidence agreement is the proportion of repeat pairs with the same adjudicated label.

## Thresholds and gates

Thresholds apply to the canonical `qwen_gate` report. Baselines are measured, not required to pass full-workflow product gates.

### Full-workflow safety gates

- 10/10 gate cases produce a terminal, schema-valid result rather than an unhandled failure.
- Citation ID validity: `1.00`.
- Citation coverage for non-abstained answers: `1.00`.
- Cross-corpus leakage: `0` records and `0` cases.
- Forbidden evidence hits: `0`.
- Expected citation-role recall: `1.00` on every applicable answered case; role precision is reported and any unexpected factual/counterevidence role is reviewed as a safety failure.
- Critical directionality errors: `0`.
- Expected-abstention recall: `1.00`.
- Unsupported or contradicted reviewed statements: `0`.
- Map-action validity: `1.00` for every emitted action.

Failure of any safety gate blocks Phase E closure. The report still saves the evidence and identifies the responsible strategy/stage.

### Quality and architecture gates

- Supported-answer usefulness: at least `6/7` answerable Qwen gate cases score `2`.
- False-abstention rate: at most `1/7` answerable Qwen gate cases.
- Abstention quality: `3/3` expected-abstention gate cases explain the actual evidence gap.
- Counterevidence satisfaction: `2/2` applicable gate cases.
- Action eligibility coverage: at least one relevant valid action in each corpus and at least `50%` across action-eligible gate cases.
- The full workflow must not regress citation validity, semantic entailment, abstention recall, or critical directionality relative to Planner–Analyst.
- The full workflow must improve at least one of semantic entailment, counterevidence satisfaction, premise correction, or abstention quality relative to Planner–Analyst. If it does not, the report records that Critic/Guide are not yet empirically justified; the harness is still valid, but Phase E remains open for an architecture decision.
- Full-workflow supported usefulness may not trail basic RAG by more than five percentage points without a documented corrective decision.
- Supported actor-knowledge case: `actor-knowledge-supported-awareness` is fully entailed with correct knowledge holder/time role; unsupported actor-knowledge case: `actor-knowledge-unsupported-personal` abstains and states the missing awareness evidence.

### Performance and regression gates

- Full-workflow median end-to-end latency: at most `600 seconds` on the recorded local hardware.
- Full-workflow p95 end-to-end latency: at most `900 seconds`.
- Structured-output failure rate: at most `10%` of calls.
- Retry rate: at most `20%` of calls.
- Stability profile: no critical directionality reversal in any repeat; counterevidence is `accounted_for` in every repeat; disposition agreement is `1.00`; Critic `verdictVariance <= 1/3`; adjudicated repeat-pair directionality and counterevidence agreement are each `1.00`.
- Provider-billed cost remains exactly represented; no gate treats `$0` Ollama billing as zero total operating cost.
- A candidate report fails regression if it crosses a hard safety threshold or worsens usefulness, false abstention, latency, structured-output failures, or retries beyond the tolerances above compared with the checked-in prior canonical report. A report is never compared with itself.

Performance failure does not erase a historically valid result, but it blocks calling the local experience practically usable.

### Candidate-versus-canonical regression tolerances

Every comparison evaluates the numerical tolerance below **and** the current absolute gates above. Crossing a fatal absolute safety gate is a regression regardless of delta, improvement elsewhere, or baseline quality.

| Metric | Better direction | Maximum allowed candidate regression from prior canonical | Fatal current absolute crossing | Missing prior baseline metric |
|---|---|---:|---|---|
| Full-workflow completion rate | Higher | `0` percentage points | Below `100%` on the gate profile | `no_baseline_metric`; absolute gate only during approved bootstrap/schema migration |
| Citation ID validity | Higher | `0` pp | Below `100%` | Same |
| Citation coverage | Higher | `0` pp | Below `100%` on non-abstained statements | Same |
| Expected citation-role recall | Higher | `0` pp | Below `100%` on any applicable case | Same |
| Semantic entailment | Higher | `0` pp | Below `100%` or any non-entailed reviewed statement | Same |
| Expected-abstention recall | Higher | `0` pp | Below `100%` | Same |
| Critical directionality errors | Lower | `0` additional errors | Above `0` | Same |
| Cross-corpus leakage | Lower | `0` additional records/cases | Above `0` | Same |
| Forbidden-evidence hits | Lower | `0` additional hits | Above `0` | Same |
| Map-action validity | Higher | `0` pp | Below `100%` when actions are emitted | Same |
| Supported-answer usefulness (`score=2`) | Higher | `5` pp drop | Below `6/7` | `no_baseline_metric`; absolute gate only during approved bootstrap/schema migration |
| False-abstention rate | Lower | `5` pp increase | Above `1/7` | Same |
| Abstention quality | Higher | `0` pp drop | Below `3/3` | Same |
| Counterevidence satisfaction | Higher | `0` pp drop | Below `2/2` or any failed stability repeat | Same |
| Action eligibility coverage | Higher | `10` pp drop | Below `50%` or missing either corpus | Same |
| Stability disposition/directionality/counterevidence agreement | Higher | `0` pp drop | Below `100%` | Same |
| Critic verdict variance | Lower | `0` increase | Above `1/3` | Same |
| Median successful latency | Lower | `15%` increase | Above `600 s` | `no_baseline_metric`; absolute gate still applies |
| Nearest-rank p95 successful latency | Lower | `15%` increase | Above `900 s` | Same |
| Structured-output failure rate | Lower | `2` pp increase | Above `10%` | Same |
| Retry rate | Lower | `5` pp increase | Above `20%` | Same |
| Prompt + completion tokens per completed case | Lower | `20%` increase | No fatal absolute threshold; flag performance regression | Record `no_baseline_metric`; do not infer zero |
| Provider-billed USD per completed case | Lower | `$0.00` increase for the Ollama-only profile | Any nonzero Ollama charge or incorrect cost basis | Record `no_baseline_metric`; validate cost basis independently |

If the entire canonical report is missing, comparison returns `no_baseline` and only the explicitly approved bootstrap path may promote after all absolute gates pass. If a later canonical exists but lacks a required candidate metric, comparison records `no_baseline_metric`; promotion requires an explicit schema-migration approval and still cannot bypass an absolute gate. A missing required **candidate** metric is `incomplete` and blocks comparison/promotion, never a tolerated delta.

## Deterministic and local-Qwen test strategy

### Default deterministic tests

The default pytest suite must never require Ollama. Scripted provider results exercise:

- all 24 cases and all four adapters;
- malformed and schema-invalid baseline responses;
- analyst rejection, critic rejection/downgrade, abstention, and successful answer paths;
- exact citation tuple validation and cross-corpus contamination rejection;
- directionality review data preservation;
- valid/invalid/unknown action targets;
- token-usage unavailable handling and `$0` provider cost semantics;
- atomic save, interrupted-run resume, stale-identity refusal, and deterministic report bytes;
- threshold pass/fail behavior and comparison to a prior report;
- proof that semantic gold/rubric fields never enter model prompts.

### Opt-in local-Qwen tests

`pytest -m local_ollama_integration` remains opt-in and health-gated. Integration tests assert contracts rather than exact prose:

- each strategy completes one answerable case in each corpus;
- each result records the actual model/version, prompt version, latency, usage availability, and provider cost basis;
- full-workflow citations and actions pass deterministic validation;
- an unsupported case safely abstains;
- the supported actor-knowledge case preserves the knowledge holder/time role, while the unsupported actor-knowledge case abstains;
- the runner persists and resumes after a deliberately stopped boundary.

The `qwen_stability` integration path runs only the two declared critical cases, two agent strategies, and three repetitions. It records answer disposition, normalized propositions, Critic verdicts, counterevidence labels, directionality labels, retries, and latency per repeat; it never expands itself into the 24-case matrix.

The quality run is performed through the CLI, not pytest, because it produces durable review/report artifacts. Reports remain candidates beneath the run directory until review and promotion:

```powershell
chronicle evaluate run --profile qwen_smoke --provider ollama --max-cases 2 --output backend/evaluation-runs/e7-qwen-smoke
chronicle evaluate run --profile qwen_gate --provider ollama --output backend/evaluation-runs/e7-qwen-gate
chronicle evaluate export-review --run backend/evaluation-runs/e7-qwen-gate --output backend/evaluation-runs/e7-qwen-gate/review-a.json
chronicle evaluate score --run backend/evaluation-runs/e7-qwen-gate --review-approval backend/evaluation-runs/e7-qwen-gate/review-approval.json --stability-run backend/evaluation-runs/e7-qwen-stability --stability-review-approval backend/evaluation-runs/e7-qwen-stability/review-approval.json --output backend/evaluation-runs/e7-qwen-gate/candidate-report.json
chronicle evaluate compare --candidate backend/evaluation-runs/e7-qwen-gate/candidate-report.json --baseline docs/delivery/phase-e7-evaluation-report.json
chronicle evaluate promote --candidate backend/evaluation-runs/e7-qwen-gate/candidate-report.json --markdown backend/evaluation-runs/e7-qwen-gate/candidate-report.md --canonical-json docs/delivery/phase-e7-evaluation-report.json --canonical-markdown docs/delivery/phase-e7-evaluation-report.md
```

Bootstrap rule: when no checked-in canonical exists, `compare` returns `no_baseline` rather than passing regression. After all safety/quality gates and the manual-review checkpoint pass, `promote --bootstrap` records `baselineMode: bootstrap`, reviewer/adjudication hashes, approver ID, timestamp, and candidate hash in the first canonical report. Later runs must compare candidate-versus-canonical and may be promoted only after review; promotion copies exact reviewed candidate bytes and records the superseded canonical hash. `promote` refuses a candidate compared against itself, an incomplete review, a failed hard gate, or an unapproved bootstrap.

The runner uses no concurrent model calls. If interrupted, rerunning `evaluate run` resumes only missing case-strategy identities.

## Sequential task plan

### E7.1 — Version the cases and registry

**Files:** benchmark JSON files, `contracts.py`, `benchmark.py`, benchmark/contract tests.
**Actions:** migrate the existing 24 cases without changing their question text or current evidence expectations; add semantic, usefulness, and action rubrics; validate every record against its declared corpus; retain `load_e3_benchmark()` as a compatibility export so E3 tests do not break.
**Automated verification:**

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/ai/evaluation/test_contracts.py backend/tests/ai/evaluation/test_benchmark.py -q
```

**Done when:** all 24 cases load from versioned data, the profile split is exact, all referenced records resolve inside the correct corpus, and injected cross-corpus IDs/rubric leakage fail tests.

### E7.2 — Implement the four comparable strategy adapters

**Files:** `strategies.py`, `baseline_prompts.py`, strategy tests.
**Actions:** define the shared strategy protocol; implement single-prompt and basic-RAG prompts; wrap the current Planner–Analyst and full sequential workflow without duplicating their orchestration; normalize artifacts while preserving raw outputs and availability differences.
**Automated verification:**

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/ai/evaluation/test_strategies.py -q
```

**Done when:** a deterministic provider runs the same case through all four strategies, corpus and policy boundaries remain identical, and no adapter can access gold rubric fields.

### E7.3 — Expose provider identity and bounded attempt audits

**Files:** `backend/src/chronicle/ai/models/protocol.py`, `backend/src/chronicle/ai/models/metadata.py`, `backend/src/chronicle/ai/models/ollama.py`, `backend/src/chronicle/ai/models/deterministic.py`, `backend/tests/ai/models/test_e7_provider_audit.py`, existing model tests as needed.
**Actions:** extend the provider contract before the evaluation runner depends on it. Expose a typed provider/model identity containing provider name/version, model name/version, and the real Ollama model digest returned by Ollama; expose bounded per-attempt artifacts containing hashes, settings, usage/cost/latency/status, validated value when available, and at most the sanctioned sanitized excerpt. The deterministic provider must implement identical contract semantics with a stable deterministic digest. Preserve retry behavior and ensure absent digest/version is explicit rather than fabricated.
**Automated verification:**

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/ai/models/test_e7_provider_audit.py backend/tests/ai/models -q
```

**Done when:** both providers satisfy the audited protocol, a real Ollama health/identity call can expose its model digest/version, every retry attempt has a bounded artifact, and existing provider tests remain green.

### E7.4 — Add resumable run execution and CLI wiring

**Files:** `backend/src/chronicle/ai/evaluation/runner.py`, `backend/src/chronicle/cli/evaluation.py`, `backend/src/chronicle/cli/main.py`, `.gitignore`, `backend/tests/ai/evaluation/test_runner.py`, `backend/tests/cli/test_evaluation.py`.
**Actions:** execute case-strategy identities sequentially, atomically save bounded audit results and a manifest, resume missing identities, reject mixed corpus/model/prompt/policy/strategy identities, expose only the `evaluate run` and `evaluate status` commands at this step, and implement `--max-cases`, `--cases`, `--strategies`, and `--repeats`. Use explicit resolved paths beneath the requested output directory; do not accept path traversal through run IDs.
**Automated verification:**

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/ai/evaluation/test_runner.py backend/tests/cli/test_evaluation.py backend/tests/cli -q
```

**Done when:** an interrupted deterministic run resumes without repeating completed identities and produces byte-stable manifests for identical inputs.

### E7.5 — Complete metrics, blinded review export, reports, and comparison

**Files:** `backend/src/chronicle/ai/evaluation/metrics.py`, `backend/src/chronicle/ai/evaluation/reporting.py`, `backend/src/chronicle/cli/evaluation.py`, `backend/src/chronicle/cli/main.py`, `backend/tests/ai/evaluation/test_metrics.py`, `backend/tests/ai/evaluation/test_reporting.py`, `backend/tests/cli/test_evaluation.py`.
**Actions:** extend existing metrics rather than replacing them; implement normalized statement mappings and typed human judgments; separate deterministic, human-reviewed, unavailable, and diagnostic-model observations; compute per-case, per-strategy, per-corpus, repeat-stability, and overall aggregates; render JSON and escaped Markdown; evaluate every gate with exact counts; and add `export-review`, `score`, `compare`, and guarded `promote` commands only after their supporting contracts exist.
**Automated verification:**

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/ai/evaluation/test_metrics.py backend/tests/ai/evaluation/test_reporting.py backend/tests/cli/test_evaluation.py -q
```

**Done when:** synthetic pass/fail fixtures prove every threshold, missing judgments cannot silently count as passes, and reports distinguish provider-billed cost from unmeasured local operating cost.

### E7.6 — Execute and export the two-corpus Qwen runs

**Files:** local-Qwen integration test and transient run/export artifacts under `backend/evaluation-runs/`.
**Actions:** run the cheap smoke, execute the ten-case Qwen gate and bounded stability profile sequentially, confirm resume/progress output, and generate blinded review exports. Stop before scoring. Do not tune on individual case answers during these runs; any corrective work becomes a separately approved bounded plan.
**Automated verification:**

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend/tests -q
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/ai/integration/test_e7_ollama_evaluation.py -m local_ollama_integration -q -s
.\backend\.venv\Scripts\chronicle.exe evaluate status --run backend/evaluation-runs/e7-qwen-gate
.\backend\.venv\Scripts\chronicle.exe evaluate status --run backend/evaluation-runs/e7-qwen-stability
```

**Done when:** both corpora have live-Qwen results for every gate strategy, all required repeat identities exist, audit manifests validate, and blinded exports contain no strategy/provider/model labels.

### E7.7 — Human historical-review checkpoint

**Type:** blocking human verification; no scoring or promotion may proceed.
**Files:** `docs/delivery/phase-e-validation-plan.md`, blinded review files in the run directories.
**Actions:** follow the validation plan exactly. Reviewer A completes every gate item. Reviewer B independently completes all stability-profile items and the registry-derived critical gate subset, explicitly including `disputed-causal-interpretations` (`bc-07`). Validate that the Reviewer-B export set equals every gate case flagged `directionalityCritical` or `requiresCounterevidence`; then validate reviewer IDs, completeness, hashes, blinding, and agreement and adjudicate disagreements without revealing strategy labels.
**Verification:**

```powershell
.\backend\.venv\Scripts\chronicle.exe evaluate validate-review --run backend/evaluation-runs/e7-qwen-gate --reviews backend/evaluation-runs/e7-qwen-gate/review-a.json backend/evaluation-runs/e7-qwen-gate/review-b-critical.json --adjudication backend/evaluation-runs/e7-qwen-gate/adjudication.json --require-secondary flagged-critical --approval-manifest backend/evaluation-runs/e7-qwen-gate/review-approval.json
.\backend\.venv\Scripts\chronicle.exe evaluate validate-review --run backend/evaluation-runs/e7-qwen-stability --reviews backend/evaluation-runs/e7-qwen-stability/review-a.json backend/evaluation-runs/e7-qwen-stability/review-b.json --adjudication backend/evaluation-runs/e7-qwen-stability/adjudication.json --approval-manifest backend/evaluation-runs/e7-qwen-stability/review-approval.json
```

Each `validate-review` command produces a hash-bound `ReviewApprovalManifest` containing the run/benchmark/blinding hashes, reviewer identities, every review-file hash, adjudication hash, required-item-set hash, completeness result, and `approved-for-scoring` status.
**Resume signal:** both approval manifests report `approved-for-scoring`, or the validator returns specific items for re-review.
**Done when:** every required judgment is complete and hash-valid, all critical double reviews are present, disagreements are adjudicated, strategy identities remained blinded, and both approval manifests bind the exact reviewed/adjudicated artifacts.

### E7.8 — Score, decide, and promote the reviewed candidate

**Files:** candidate reports in the run directory, canonical JSON/Markdown reports, `plans/current-phase.md`, `docs/delivery/phase-e-ai-core-plan.md`.
**Actions:** score only the checkpoint-approved review artifacts; join gate and stability results; compare the candidate with the prior canonical or execute the explicit bootstrap path; record every pass/fail/incomplete gate; state whether Critic/Guide are empirically justified; promote exact reviewed candidate artifacts only if the promotion rules allow it; update both phase trackers.
**Automated verification:**

```powershell
.\backend\.venv\Scripts\chronicle.exe evaluate score --run backend/evaluation-runs/e7-qwen-gate --review-approval backend/evaluation-runs/e7-qwen-gate/review-approval.json --stability-run backend/evaluation-runs/e7-qwen-stability --stability-review-approval backend/evaluation-runs/e7-qwen-stability/review-approval.json --output backend/evaluation-runs/e7-qwen-gate/candidate-report.json
.\backend\.venv\Scripts\chronicle.exe evaluate compare --candidate backend/evaluation-runs/e7-qwen-gate/candidate-report.json --baseline docs/delivery/phase-e7-evaluation-report.json
```

`score` must reject a missing approval manifest, any manifest not marked `approved-for-scoring`, or any mismatch between the manifest-bound run, reviewer, review-file, adjudication, required-item-set, and current artifact hashes.
**Done when:** the candidate report is reproducible from run/approval-manifest hashes, regression is candidate-versus-prior-canonical (or explicitly bootstrapped), pass/fail records are complete, approved artifacts are promoted, and both trackers record the evidence-backed decision.

## Failure modes and required handling

| Failure mode | Required behavior |
|---|---|
| Related citation but reversed historical meaning | Citation validity may pass; semantic/directionality gate fails and names the case/check. |
| Correct safety abstention on answerable evidence | Count as false abstention and usefulness failure, not a successful answer. |
| Confident answer to missing-evidence case | Abstention and unsupported-statement gates fail. |
| Gold rubric reaches a prompt | Stop the run as invalid; never score the contaminated output. |
| Cross-corpus ID appears in retrieval/citation/action | Hard fail with the offending ID and origin. |
| Invalid action target or time | Existing deterministic answer validator rejects it; hard action-validity failure. |
| Ollama unavailable | Health-gated integration test skips; CLI exits nonzero without fabricating results. Canonical report cannot be produced. |
| Ollama timeout or malformed JSON | Persist attempt/error metadata; retry only under existing bounded policy; resume at the missing identity. |
| Missing token usage | Mark unavailable; do not record zero. |
| Local provider cost is `$0` | Preserve `no_provider_charge`; do not describe hardware/electricity as free. |
| Benchmark/corpus file changes | Hash mismatch invalidates reuse and requires a fresh run identity. |
| Missing human judgment | The affected semantic/usefulness metric is incomplete and its gate cannot pass. |
| Model-generated HTML/Markdown in a report | Escape untrusted output; never render it as executable HTML. |
| Four-agent workflow does not beat simpler paths | Report the finding honestly and keep Phase E open for an explicit architecture decision. |

## Security and integrity boundaries

- Benchmark files and curated corpus records are inputs, not executable instructions.
- Model output is untrusted and is parsed through bounded Pydantic contracts.
- File writes are confined to a resolved evaluation-run directory and use atomic replacement.
- Report renderers escape model text and never interpolate it into raw HTML.
- Gold rubric separation is enforced in code and tests to prevent evaluation leakage.
- Existing citation, visibility, rights, temporal, geographic-precision, corpus-boundary, and action-reference validators remain authoritative.

## Full verification commands

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/ai/evaluation backend/tests/ai/orchestration backend/tests/ai/agents backend/tests/ai/tools backend/tests/ai/corpus backend/tests/cli -q
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/ai/integration/test_e7_ollama_evaluation.py -m local_ollama_integration -q -s
.\backend\.venv\Scripts\python.exe -m ruff check backend/src backend/tests
git diff --check
```

If Ruff is not installed in the project environment when E7 begins, do not add it merely for this phase; use the repository's existing lint/type verification commands and record Ruff as unavailable.

## Phase completion criteria

E7 is complete when all of the following are true:

- The 24-case versioned registry validates against both current corpora.
- All four strategies execute through one provider-independent runner without topic branching.
- The provider audit contract records the real Ollama model digest/version and bounded per-attempt artifacts; deterministic-provider parity is tested.
- Default deterministic tests cover the full case × strategy matrix and pass without Ollama.
- The ten-case local-Qwen gate and two-case repeated stability profile complete sequentially across both corpora.
- Citations, semantic entailment/directionality, usefulness, abstention, latency, token usage, provider cost, actions, cross-corpus behavior, retries, and failures are all represented with explicit availability and denominators.
- Every Qwen gate response has a completed, hash-valid blinded historical review; all critical directionality/counterevidence items have independent second review and adjudication where needed.
- The canonical JSON and Markdown reports reproduce from saved bounded audit artifacts and hash-valid human reviews.
- Full-workflow safety gates pass; any quality/performance/architecture gate failure is explicit and prevents Phase E closure.
- The report states whether Critic/Guide measurably improve the Planner–Analyst path and whether the improvement justifies their latency.
- `docs/delivery/phase-e-validation-plan.md` has been followed and contains the manual review protocol, commands, pass/fail record, and explicit validation decision.
- `plans/current-phase.md` records the result and next bounded decision.
- `docs/delivery/phase-e-ai-core-plan.md` records E6's implemented status and E7's evidence-backed completion/blocker status.
- No live web research, new corpus, database, embeddings, paid provider, or UI work entered the phase.

## Multi-source coverage audit

| Source | Requirement | Coverage |
|---|---|---|
| Phase E roadmap | Benchmark registry, case schema, four runners, provider audit, metrics, saved reports, regression thresholds | E7.1–E7.8 |
| AI-core evaluation guidance | 20–30 reviewed questions over at least two corpora | Existing 24 cases, versioned in E7.1 |
| AI-core evaluation guidance | Grounding, reasoning, agent, performance, cost, and recovery measures | Metrics section and E7.5 |
| AI-core evaluation guidance | Single prompt, basic RAG, Planner–Analyst, full workflow comparison | Strategy definitions and E7.2 |
| E6 evidence | Valid selected-context cited answer plus generic semantic/latency risks | Why E7 exists, directionality/usefulness/latency gates |
| `AGENTS.md` | Deterministic provider path, historical integrity, bounded tools, citation/action validation, no paid infrastructure | Deterministic suite, security boundaries, explicit exclusions |
| User requirement | Qwen must return valid results | Live gate, safety thresholds, and human-reviewed entailment/directionality |
| User requirement | Sequential work and reduced concurrent-agent use | One workstream; runner concurrency `1`; no subagent requirement |

No source requirement is omitted. Live source discovery belongs to Phase F, document acquisition/RAG infrastructure belongs to Phase G, a new holdout/generalization corpus belongs to E8, and learning-document consolidation belongs to E9.
