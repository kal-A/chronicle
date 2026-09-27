# Evaluation harness and baseline

Chronicle's AI evaluation is the **E7 harness** (`backend/src/chronicle/ai/evaluation/`)
run over a **versioned benchmark of the two curated corpora**. This document records the
dataset design, the metrics and why they were chosen, the harness architecture, the exact
commands, and the **measured baseline** — deterministic and a small real-model slice.

This phase established the baseline only. No prompts were tuned and no product behavior
was changed to improve scores; the one code change was enabling the `ollama` provider in
the eval CLI so the real pipeline can be scored against the same cases.

## Dataset design

`backend/benchmarks/e7/cases.json` (`benchmarkVersion e7-v1`) — **24 cases** over the two
curated corpora (`concert-of-europe-1814-1822` ×12, `blank-cheque-golden` ×12), spanning
11 categories:

| Category | n | Includes expected abstention |
|---|---|---|
| direct_evidence | 7 | |
| missing_evidence | 3 | ✅ |
| out_of_corpus | 2 | ✅ |
| invalid_premise | 2 | ✅ |
| source_comparison | 2 | |
| timeline_ordering | 2 | |
| actor_knowledge | 2 | |
| relationship_trace / counterevidence / explanation / disputed_interpretation | 1 each | |

**7 of 24 cases expect a principled abstention** (`missing_evidence`, `invalid_premise`,
`out_of_corpus`) — the "insufficient-evidence / difficult" cases. Each case carries
machine-checkable expectations: `requiredEvidenceIds`, `forbiddenEvidenceIds`,
`expectedCitationRoles`, `expectedAbstention`, `unacceptableClaims`, `temporalConstraints`,
`acceptableTools`, and `requiresCounterevidence`. Cases are tagged into **profiles**
(`deterministic_full`, `qwen_gate`, `qwen_stability`, …) so a run can select a subset.

## Metrics and why

All scored metrics are **deterministic** — computed from the run's structured records
against each case's declared expectations, never from a model's opinion. Human-only
dimensions are surfaced as `incomplete`, not guessed. This maps directly to the requested
dimensions:

| Requested dimension | Metric(s) | Why deterministic |
|---|---|---|
| Retrieval relevance / recall | `required_evidence_recall` (cited required IDs ÷ required), `temporal_coverage` | required IDs are declared per case; recall is a set intersection |
| Citation / source grounding | `citation_validity` (each citation resolves in the `RetrievedReferenceIndex`), `citation_coverage` | resolvability is a lookup, not a judgment |
| Unsupported claims | `unsupported = 1 − coverage`, `unacceptable_claims` (declared phrase hits) | statement-without-valid-citation is countable |
| Abstention behavior | `abstention_correct` (`abstained == expectedAbstention`) | both sides are booleans |
| Deterministic contract / validation | `plan_valid`, acceptable-tool-selection, `no_forbidden_evidence`, `no_cross_corpus_leakage`, budget observations | contract checks, not quality |
| End-to-end answer quality (reliable rubric) | the deterministic subset above; **`semantic_entailment` and `usefulness` are left `incomplete`** | no reliable automatic rubric — see below |

**No LLM judge.** Semantic entailment and usefulness need judgment we cannot compute
defensibly, so the harness marks them `incomplete` and defers them to a single blinded
human review (`chronicle evaluate export-review`) rather than substituting an LLM judge
whose own errors would be unaudited. Deterministic metrics and this human track are kept
strictly separate.

## Harness architecture

```
cases.json + registry.json            ← versioned dataset (benchmarks/e7/)
        │
   strategies.py   single_prompt · basic_rag · planner_analyst · full_workflow
        │          (built with a ProviderFactory: deterministic | ollama)
   runner.py       run_benchmark() → resumable, byte-stable per-result JSON + manifest
        │
   metrics.py      score_result() → raw numerator/denominator per dimension
        │
   reporting.py    aggregate → gates (pass/fail/not_applicable/incomplete) → JSON + Markdown
        │
   cli/evaluation.py   `chronicle evaluate run | status | report | export-review`
```

Four **strategies** let the four-agent pipeline (`full_workflow`) be compared against
simpler baselines (single-prompt, basic RAG, planner+analyst) — the CHR-AI-011 question of
whether the full workflow earns its complexity. The **`deterministic` provider** is a
fast, reproducible null/scripted provider (a floor + safety baseline); the **`ollama`
provider** runs the real local model over the same cases and metrics.

## Exact commands

Deterministic floor (fast, no model, fully reproducible):

```bash
chronicle evaluate run                                   # profile deterministic_full, 24×4 = 96 identities
chronicle evaluate report evaluation-runs/latest \
    --json benchmarks/e7/baseline/report.json \
    --markdown benchmarks/e7/baseline/report.md
```

Real-model slice (needs Ollama running; slow, CPU-bound — bounded here to 3 cases):

```bash
CHRONICLE_OLLAMA_MODEL=qwen2.5:3b-instruct \
  chronicle evaluate run --profile qwen_gate --provider ollama \
    --strategies full_workflow --max-cases 3 --output evaluation-runs/ollama-3b
chronicle evaluate report evaluation-runs/ollama-3b \
    --json benchmarks/e7/baseline/ollama-3b-slice.json \
    --markdown benchmarks/e7/baseline/ollama-3b-slice.md
```

Committed baseline reports live under `backend/benchmarks/e7/baseline/`.

## Baseline results

### Deterministic floor — 24 cases × 4 strategies (96 identities)

All four strategies score identically (the null provider produces no answers):

| Metric | Value | n/d |
|---|---|---|
| required_evidence_recall | 0.000 | 0/40 |
| abstention_correct | 0.292 | 7/24 |
| citation_validity / coverage | not_applicable | 0/0 |
| forbidden_evidence_hits | 0.000 | 0/24 |
| cross_corpus_leakage | 0.000 | 0/24 |
| unacceptable_claims | 0.000 | 0/24 |

Gates: `no_forbidden_evidence` and `no_cross_corpus_leakage` **pass**;
`required_evidence_recall` and `abstention_correctness` **fail**; `citation_*`
`not_applicable`; `semantic_entailment` / `usefulness` **incomplete**. (8 gate failures =
4 strategies × 2.)

**What this baseline proves:** the harness computes every metric, and the **safety
invariants hold even at the floor** — nothing cites forbidden evidence, nothing leaks
across corpora, nothing emits an unacceptable claim. It is a regression + safety baseline,
**not** a model-quality measurement (the deterministic provider answers nothing).

### Real-model slice — 3 cases, `full_workflow`, `qwen2.5:3b-instruct`

| Metric | Value | n/d |
|---|---|---|
| abstention_correct | 0.000 | 0/3 |
| required_evidence_recall | 0.000 | 0/7 |
| citation_validity / coverage | not_applicable | 0/0 |
| forbidden / leakage / unacceptable | 0.000 | 0/3 |

All three cases (`counterevidence-extension-limits`, `direct-intervention-principle`,
`timeline-congress-intervention-order`) are answerable, and **3B abstained on all three**
(0 statements). So `abstention_correct` is 0/3 — the model wrongly abstains — but it
produces **no fabrication**: forbidden, leakage, and unacceptable-claim hits are all 0.

## Important failures / findings discovered

1. **The deterministic profile is a floor, not a quality signal.** Its `deterministic`
   provider is a null/scripted provider, so grounding and recall are 0 by construction. It
   is valuable as a reproducible regression + safety baseline, and it must not be read as
   real answer quality.
2. **3B is below the answering threshold on the curated corpora.** The real slice abstained
   on every answerable case — consistent with the documented small-model analyst-grounding
   limit (`failure-modes-and-trade-offs.md` §3, `performance-benchmark.md`). Crucially it
   **fails safe**: it abstains rather than fabricating.
3. **A capable-model baseline is the documented next step, hardware-bound here.** 7B OOMs
   and 14B is larger still on the dev machine (13.69 GB RAM); a `qwen_gate` / `qwen_full`
   run on a capable host is the meaningful model-quality baseline. The command is wired and
   documented above; only the run is deferred.
4. **Human dimensions remain open by design.** `semantic_entailment` and `usefulness` are
   `incomplete` pending a blinded human review; no LLM judge was introduced.

## Reproducing / limitations

- Deterministic run is byte-stable and fast; re-runnable anywhere with the backend
  installed. The real slice depends on a running Ollama daemon and the pulled model, and
  its absolute behavior is model- and hardware-specific.
- The real baseline here is intentionally tiny (3 cases, one strategy) to stay within the
  dev machine's time/RAM budget; it is a data point, not a full model-quality run.
- This document is a baseline, not a verdict on the four-agent design — that comparison
  needs a capable-model run across all strategies (CHR-AI-011), which is future work.
