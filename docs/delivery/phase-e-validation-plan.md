# Phase E Validation Plan — Historical Answer and Agent-Architecture Gate

**Status:** protocol approved for Phase E7 execution; no validation result has been recorded
**Companion plan:** `docs/delivery/phase-e7-evaluation-harness-plan.md`

## Decision being validated

Does Chronicle's local-Qwen four-agent workflow produce citation-valid, semantically supported, directionally correct, useful historical answers and safe abstentions across both current benchmark corpora—and does the Critic/Guide improve enough over Planner–Analyst and simpler baselines to justify its additional latency?

This is a historical-quality and architecture gate. It is not a usability study, a web-research evaluation, or a claim that the benchmark represents history universally.

## Required evidence before review

The review checkpoint may begin only when all of these exist and validate:

- a complete `qwen_gate` run: ten cases × four strategies × one repetition;
- a complete `qwen_stability` run: two critical cases × two agent strategies × three repetitions;
- run manifests containing benchmark/case hashes, corpus package hashes, strategy implementation versions, provider/model identity and digest, generation settings, policy hash, per-role prompt hashes, and result hashes;
- bounded model-call artifacts and exact supplied-context artifacts;
- blinded review exports with opaque review-item IDs, recorded shuffle seed/hash, exact answer text, normalized statements, citations, and resolved cited passages;
- a private blinding manifest withheld from reviewers.

The evaluation runner must report `complete`; partial runs can be inspected but cannot enter review or pass the gate.

## Reviewer protocol

### Roles and identity

- **Reviewer A:** reviews every `qwen_gate` item and every stability item.
- **Reviewer B:** independently reviews every stability item and the complete registry-derived gate subset where `directionalityCritical=true` or `requiresCounterevidence=true`. This explicitly includes `direct-reported-assurance`, `counterevidence-extension-limits`, and `disputed-causal-interpretations` (`bc-07`); any additional flagged case is included automatically.
- **Adjudicator:** resolves Reviewer A/B disagreements without strategy/provider/model labels. The adjudicator may be Reviewer A or B only if the disagreement and final rationale remain explicit.

Each person uses a stable non-personal `reviewerId`/`adjudicatorId` such as `historical-reviewer-a`; do not store names, emails, or unrelated personal data. Each review records reviewer role, start/completion timestamps, benchmark-run hash, blinding-manifest hash, and its own canonical JSON hash.

### Blinding

Review exports must:

- replace strategy/result identities with opaque IDs;
- remove strategy, provider, model, prompt, latency, and cost labels;
- deterministically randomize answer order using a recorded seed;
- retain the question, corpus title, exact answer, normalized statements, citation IDs, resolved passages/source metadata, and historical rubric required to judge the response.

Reviewers must not inspect the private identity map, source run directories, latency, or strategy labels until judgments and adjudication are hash-final. A blinding breach invalidates affected judgments and requires a fresh export/reshuffle/review.

### Statement and check judgments

Reviewers judge every exported normalized statement; they do not invent their own statement denominator. They record:

- entailment: `entailed`, `partially_entailed`, `contradicted`, or `unverifiable`;
- directionality: `correct`, `reversed`, `ambiguous`, or `not_applicable`;
- inspected cited record IDs and a concise rationale;
- counterevidence: `accounted_for`, `mentioned_only`, `omitted`, `mischaracterized`, or `not_applicable`;
- temporal behavior: `correct`, `incorrect_order`, `time_role_collapsed`, `omitted`, or `not_applicable`;
- action relevance: `relevant`, `plausible_but_unhelpful`, `misleading`, or `not_applicable`;
- usefulness: `2` (direct, complete on critical criteria), `1` (useful but materially incomplete), or `0` (wrong, evasive, or unusable);
- abstention gap and premise-handling labels where applicable.

`partially_entailed` is not a safety pass. It receives zero full-entailment credit and prevents usefulness `2` when the missing qualification is material. Only `accounted_for`, temporal `correct`, directionality `correct`/`not_applicable`, and action `relevant` count as their respective positive labels.

### Review completeness and adjudication

`reviewComplete: true` is valid only if every required child judgment and rationale is present. The review validator rejects duplicate/missing items, unknown record IDs, changed answer text, mismatched run/blinding hashes, missing reviewer identity, or a self-inconsistent file hash.

For double-reviewed items, the scorer records raw percent agreement and Cohen's kappa for entailment, directionality, and counterevidence. Every disagreement requires an adjudication entry referencing both review file hashes, selecting one allowed final label, and explaining the evidence-based decision. Scoring uses the adjudicated label; unadjudicated disagreement makes the result incomplete.

## Execution and review commands

### 1. Cheap live preflight

```powershell
.\backend\.venv\Scripts\chronicle.exe evaluate run --profile qwen_smoke --provider ollama --max-cases 2 --output backend/evaluation-runs/e7-qwen-smoke
.\backend\.venv\Scripts\chronicle.exe evaluate status --run backend/evaluation-runs/e7-qwen-smoke
```

Expected: two cases, all four strategies, both corpora represented, health/model identity recorded, no mixed identity. This does not count as the quality gate.

### 2. Required sequential runs

```powershell
.\backend\.venv\Scripts\chronicle.exe evaluate run --profile qwen_gate --provider ollama --output backend/evaluation-runs/e7-qwen-gate
.\backend\.venv\Scripts\chronicle.exe evaluate run --profile qwen_stability --provider ollama --repeats 3 --output backend/evaluation-runs/e7-qwen-stability
.\backend\.venv\Scripts\chronicle.exe evaluate status --run backend/evaluation-runs/e7-qwen-gate
.\backend\.venv\Scripts\chronicle.exe evaluate status --run backend/evaluation-runs/e7-qwen-stability
```

Runs use concurrency `1`, persist each identity atomically, and resume missing work when the same command is repeated. Operators may use `--max-cases`, `--cases`, or `--strategies` to make bounded progress; the final status must still show every required profile identity complete before export.

### 3. Produce blinded exports

```powershell
.\backend\.venv\Scripts\chronicle.exe evaluate export-review --run backend/evaluation-runs/e7-qwen-gate --output backend/evaluation-runs/e7-qwen-gate/review-a.json
.\backend\.venv\Scripts\chronicle.exe evaluate export-review --run backend/evaluation-runs/e7-qwen-gate --reviewer-slot b --selection flagged-critical --output backend/evaluation-runs/e7-qwen-gate/review-b-critical.json
.\backend\.venv\Scripts\chronicle.exe evaluate export-review --run backend/evaluation-runs/e7-qwen-stability --reviewer-slot a --output backend/evaluation-runs/e7-qwen-stability/review-a.json
.\backend\.venv\Scripts\chronicle.exe evaluate export-review --run backend/evaluation-runs/e7-qwen-stability --reviewer-slot b --output backend/evaluation-runs/e7-qwen-stability/review-b.json
```

Reviewer A/B fill only the exported typed fields. Export validation must prove that `review-b-critical.json` contains every and only required gate result whose case carries either critical flag across all evaluated strategies; omission of `disputed-causal-interpretations` or another flagged case blocks review. Do not reveal the generated private blinding manifest.

### 4. Validate reviews and adjudication

```powershell
.\backend\.venv\Scripts\chronicle.exe evaluate validate-review --run backend/evaluation-runs/e7-qwen-gate --reviews backend/evaluation-runs/e7-qwen-gate/review-a.json backend/evaluation-runs/e7-qwen-gate/review-b-critical.json --adjudication backend/evaluation-runs/e7-qwen-gate/adjudication.json --require-secondary flagged-critical --approval-manifest backend/evaluation-runs/e7-qwen-gate/review-approval.json
.\backend\.venv\Scripts\chronicle.exe evaluate validate-review --run backend/evaluation-runs/e7-qwen-stability --reviews backend/evaluation-runs/e7-qwen-stability/review-a.json backend/evaluation-runs/e7-qwen-stability/review-b.json --adjudication backend/evaluation-runs/e7-qwen-stability/adjudication.json --approval-manifest backend/evaluation-runs/e7-qwen-stability/review-approval.json
```

Each command must produce a hash-bound `ReviewApprovalManifest` containing the run/benchmark/blinding hashes, reviewer identities, every review-file hash, adjudication hash, required-item-set hash, completeness result, timestamp, and `approved-for-scoring` status. The checkpoint passes only when both manifests are approved, all reviews are hash-valid, and no disagreement is unadjudicated.

### 5. Score candidate and compare with prior canonical

```powershell
.\backend\.venv\Scripts\chronicle.exe evaluate score --run backend/evaluation-runs/e7-qwen-gate --review-approval backend/evaluation-runs/e7-qwen-gate/review-approval.json --stability-run backend/evaluation-runs/e7-qwen-stability --stability-review-approval backend/evaluation-runs/e7-qwen-stability/review-approval.json --output backend/evaluation-runs/e7-qwen-gate/candidate-report.json
.\backend\.venv\Scripts\chronicle.exe evaluate compare --candidate backend/evaluation-runs/e7-qwen-gate/candidate-report.json --baseline docs/delivery/phase-e7-evaluation-report.json
```

If no canonical report exists, comparison must return `no_baseline`. The first candidate uses an explicitly approved `promote --bootstrap`; it never compares against itself. Later candidates compare with the existing checked-in canonical and record the baseline hash.

`score` must reject a missing approval manifest, a manifest not marked `approved-for-scoring`, or any mismatch between the manifest-bound run, reviewer identity, review-file, adjudication, required-item-set, and current artifact hashes. The score command consumes the manifests rather than silently using only Reviewer A's file.

### 6. Promote only the reviewed candidate

```powershell
.\backend\.venv\Scripts\chronicle.exe evaluate promote --candidate backend/evaluation-runs/e7-qwen-gate/candidate-report.json --markdown backend/evaluation-runs/e7-qwen-gate/candidate-report.md --canonical-json docs/delivery/phase-e7-evaluation-report.json --canonical-markdown docs/delivery/phase-e7-evaluation-report.md
```

Use `--bootstrap` only for the first approved report. Promotion refuses incomplete review, failed hard safety gates, candidate/self-baseline comparison, identity/hash mismatch, or missing approval metadata. Promotion does not imply git commit/push authorization.

## Pass/fail gates

### Hard historical-safety gates

- 10/10 full-workflow gate cases terminate with schema-valid results.
- Citation ID validity and non-abstained statement citation coverage are both `1.00`.
- Expected citation-role recall is `1.00` on every applicable answered case.
- No cross-corpus or forbidden-evidence ID occurs.
- No reviewed statement is partially entailed, contradicted, or unverifiable.
- No critical directionality reversal occurs in any gate or repeat.
- Expected-abstention recall is `3/3`, with correct evidence-gap explanations.
- Every emitted map action is deterministically valid.
- The supported actor-knowledge case preserves holder/time role; the unsupported case abstains rather than infer knowledge from availability.

Any hard-gate failure records `FAIL` and blocks Phase E closure and canonical promotion.

### Quality, stability, and architecture gates

- At least `6/7` answerable full-workflow gate cases score usefulness `2`.
- False abstention is at most `1/7`; abstention quality is `3/3`.
- Counterevidence satisfaction is `2/2` in the main gate and passes every stability repeat.
- Relevant valid action coverage reaches at least 50% of action-eligible cases and includes both corpora.
- Full workflow does not regress citation validity, semantic entailment, abstention recall, or directionality relative to Planner–Analyst.
- Full workflow improves at least one of entailment, counterevidence, premise correction, or abstention quality; otherwise Critic/Guide are recorded as not empirically justified.
- Stability: disposition agreement `1.00`, directionality/counterevidence repeat-pair agreement `1.00`, and Critic-verdict variance at most `1/3`.
- Full-workflow median latency is at most 600 seconds and p95 at most 900 seconds; structured failures are at most 10% and retries at most 20%.

Quality/performance failure is recorded as `FAIL` or `BLOCKED` per the E7 report and prevents Phase E closure, even when the harness itself is implemented correctly.

## Required pass/fail record

Complete this block after review and scoring; do not pre-fill outcomes:

```text
Validation run ID:
Candidate report SHA-256:
Prior canonical SHA-256 or BOOTSTRAP:
Benchmark registry/case SHA-256:
Corpus package SHA-256 values:
Provider/model name, version, digest:
Reviewer A ID / review SHA-256:
Reviewer B ID / review SHA-256:
Adjudicator ID / adjudication SHA-256:
Blinding intact: PASS | FAIL
Review completeness: PASS | FAIL
Hard historical-safety gates: PASS | FAIL (list failing case/check IDs)
Quality gates: PASS | FAIL (list failing case/check IDs)
Stability gates: PASS | FAIL (list failing case/check IDs)
Performance gates: PASS | FAIL (include counts, median, nearest-rank p95)
Regression comparison: PASS | FAIL | NO_BASELINE
Critic/Guide justification: JUSTIFIED | NOT_JUSTIFIED | INCONCLUSIVE
Overall Phase E validation: PASS | FAIL | BLOCKED
Decision rationale:
Recorded by / timestamp:
```

The Markdown canonical report must reproduce each line from typed JSON and show every numerator/denominator, missing/incomplete observation, failing case slug, review hash, and baseline/candidate hash. `plans/current-phase.md` and `docs/delivery/phase-e-ai-core-plan.md` must link the completed record and state the same decision.

## Invalid validation conditions

The validation is invalid—not merely failed—if strategy identities are revealed before review finalization, gold rubrics enter prompts, required judgments are missing, answer/citation text changes after export, run/model/corpus/prompt identities are mixed, candidate and baseline hashes are identical, a report is promoted before review, or a human edits generated scores rather than the typed judgments. Fix the protocol breach and repeat affected review/run work before making a Phase E decision.
