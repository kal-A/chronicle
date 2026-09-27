# Real 7B model-quality baseline (bounded)

A bounded, pre-registered real-model baseline: the actual four-agent pipeline
(`full_workflow`) on **`qwen2.5:7b-instruct`** via the existing E7 harness, scored with the
existing deterministic metrics over a representative subset of the versioned cases. No
prompts, scoring, product behavior, dataset expectations, or metrics were changed. Failures
and abstentions are reported as results, not fixed.

Companion to [`evaluation-harness.md`](./evaluation-harness.md) (dataset, metrics, and the
deterministic + 3B baselines).

## Case selection (pre-registered before the run)

Six of the 24 `e7-v1` cases, fixed **before** running to avoid post-hoc cherry-picking
(manifest: `backend/benchmarks/e7/baseline/qwen7b-subset.json`): 3 per curated corpus,
varied categories, **4 answerable** (retrieval/grounding-dependent) and **2 expected
abstentions** (one per corpus).

| Case | Corpus | Category | Expected |
|---|---|---|---|
| direct-source-date | concert-of-europe | direct_evidence | answer |
| relationship-doctrine-to-intervention | concert-of-europe | relationship_trace | answer |
| actor-knowledge-unsupported-personal | concert-of-europe | actor_knowledge | **abstain** |
| direct-reported-assurance | blank-cheque | direct_evidence | answer |
| actor-knowledge-supported-awareness | blank-cheque | actor_knowledge | answer |
| missing-exact-receipt-hour | blank-cheque | missing_evidence | **abstain** |

## Method

- Model `qwen2.5:7b-instruct` (pulled for this run), strategy `full_workflow`, provider
  `ollama`, one repeat. Dev machine: Ryzen 5 6600H, CPU-only, 13.69 GB RAM.
- Command (also in the manifest):

```bash
CHRONICLE_OLLAMA_MODEL=qwen2.5:7b-instruct \
  chronicle evaluate run --profile deterministic_full --provider ollama \
    --strategies full_workflow \
    --cases direct-source-date,relationship-doctrine-to-intervention,actor-knowledge-unsupported-personal,direct-reported-assurance,actor-knowledge-supported-awareness,missing-exact-receipt-hour \
    --output evaluation-runs/qwen7b-baseline
chronicle evaluate report evaluation-runs/qwen7b-baseline \
  --json benchmarks/e7/baseline/qwen7b-subset-report.json \
  --markdown benchmarks/e7/baseline/qwen7b-subset-report.md
```

## Results — deterministic metrics only

Semantic answer quality is **not** evaluated here (no automatic judge); it would need the
blinded human review track. The run produced no answers to review — every case abstained.

### Per case

| Case | Expected | Status | Recall | Citations | Abstention correct |
|---|---|---|---|---|---|
| direct-source-date | answer | abstained | 0/1 | 0 | ✗ |
| relationship-doctrine-to-intervention | answer | abstained | 0/2 | 0 | ✗ |
| actor-knowledge-unsupported-personal | **abstain** | abstained | — | 0 | ✓ |
| direct-reported-assurance | answer | abstained | 0/1 | 0 | ✗ |
| actor-knowledge-supported-awareness | answer | abstained | 0/2 | 0 | ✗ |
| missing-exact-receipt-hour | **abstain** | abstained | — | 0 | ✓ |

### Aggregate (where meaningful)

| Metric | Value | n/d |
|---|---|---|
| abstention_correct | 0.333 | 2/6 |
| required_evidence_recall | 0.000 | 0/7 |
| citation_validity / coverage | not_applicable | 0/0 |
| forbidden_evidence_hits | 0.000 | 0/6 |
| cross_corpus_leakage | 0.000 | 0/6 |
| unacceptable_claims | 0.000 | 0/6 |

Gates: `no_forbidden_evidence` and `no_cross_corpus_leakage` **pass**;
`required_evidence_recall` and `abstention_correctness` **fail**; `citation_*`
`not_applicable`; `semantic_entailment` / `usefulness` **incomplete** (no LLM judge).

### Runtime

~319 s across the six cases (first-to-last result write), **~64 s/case average**, roughly
6–7 minutes total wall-clock, CPU-only. (Per-case `ExecutionMeasurements` are not persisted
by the eval path, so runtime is measured from result-file timestamps.)

## Findings (results, not fixed)

1. **7B abstained on all six cases**, including the four answerable ones — so
   `abstention_correct` is 2/6 (correct only on the two expected-abstention cases) and
   evidence recall is 0/7.
2. **No fabrication.** Forbidden-evidence, cross-corpus-leakage, and unacceptable-claim hits
   are all 0 — the deterministic safety invariants hold on the real 7B run: it abstains
   rather than inventing evidence.
3. **Interpretation caveat (factual, not changed here):** the E7 `full_workflow` strategy
   builds retrieval as `InvestigationRunner(registry, store=store)` — with the **default**
   execution policy and **without** the retrieval floor that the deployed
   `create_default_app` enables (`retrieval_floor=True`, tightened budgets). So this baseline
   measures the harness strategy *as defined*, which abstains more readily than the deployed
   configuration. Reconciling the eval strategy with the deployed config is a separate,
   later decision — deliberately not made in this baseline phase.

## Separation of automated vs semantic

Everything above is deterministic and machine-checked. **Semantic answer quality is
unevaluated** and remains so until a manual/blinded review — and in this run there were no
grounded answers to review. No LLM judge was used.

## Reproducibility & limitations

- Reproducible with the command above given a running Ollama daemon and `qwen2.5:7b-instruct`
  pulled (~5 GB). Absolute runtime is hardware-specific (CPU-only here).
- Intentionally bounded to 6 cases × one strategy — a representative baseline, not the full
  24 × 4 matrix. A larger 7B/14B run across strategies (the CHR-AI-011 comparison) remains
  future work.
