# Performance benchmark report

Measured wall-clock for a Chronicle investigation, end to end and by stage. Every
number here is **measured** on the hardware below — either freshly with the committed
benchmark tools or mined from the timings the pipeline already records on every run.
Nothing is estimated. This phase is measurement only; no optimization was performed.

## Environment

| | |
|---|---|
| CPU | AMD Ryzen 5 6600H — 6 cores / 12 threads, **CPU-only inference** (no GPU offload) |
| RAM | 13.69 GB total (~1.1 GB free during runs; other apps hold the rest) |
| OS | Windows 11 Home |
| Runtime | Python 3.14.3, Ollama 0.34.4 |
| Models | `qwen2.5:3b-instruct` (fresh runs — the only model that fits free RAM); `qwen2.5:7b-instruct` and `qwen2.5:14b-instruct` (historical runs on disk) |

Absolute numbers are specific to this machine; the **shape** (which stage dominates, cache
effect, model-size scaling) is the transferable result.

## What is measured, and how

The pipeline already records per-stage timing on every run — `AgentStageRecord.latencyMs`,
`PromptMeasurement`, and per-`ModelCallRecord.latencyMs` (see
[`request-trace.md`](./request-trace.md)). The benchmark tools drive real runs and read
those fields; **no product code was changed to measure**. Each stage is decomposed into
**model-generation time** (`sum(modelCalls[].latencyMs)`) and **deterministic overhead**
(`latencyMs − model time` = prompt/context prep + deterministic validation/finalization).

Tools (committed, from `backend/`):

| Tool | Measures | Runs |
|---|---|---|
| `benchmarks/perf/time_acquisition.py` | Phase A: discovery + fetch + chunk + build, cold vs warm cache | 1 cold + 1 warm |
| `benchmarks/perf/run_investigation_benchmark.py` | Phase B: four-agent workflow over a fixed corpus/question, per stage + end-to-end | 3 repeats (3B) |
| `benchmarks/perf/summarize_run_history.py` | Phase B: aggregates the 55 timed run records already on disk (7B/14B evidence) | reads 55 runs |

Raw outputs are committed under `backend/benchmarks/perf/results/`.

## Results

### Phase A — acquisition (`time_acquisition.py`)

Topic "Congress of Vienna", 1814–1815, `max_sources=6`, lexical path (no enrichment, no
embeddings, no model). Discovered 5, acquired 4, produced 109 passages.

| Run | Wall clock |
|---|---|
| **Cold** (empty cache, network-bound) | **79.9 s** |
| **Warm** (content-addressed cache populated) | **1.9 s** |

The content-addressed `FetchCache` makes a rebuild **~42× faster** — acquisition cost is
almost entirely the one-time network fetch, not local processing.

### Phase B — investigation, freshly measured (3B, 3 repeats)

Corpus `concert-of-europe-1814-1822`, fixed question, `qwen2.5:3b-instruct`. All three runs
**failed at the analyst grounding gate** — the documented small-model capacity limit
(see [`failure-modes-and-trade-offs.md`](./failure-modes-and-trade-offs.md) §3), not a
benchmark defect — so only the stages up to the analyst execute on 3B here.

| Stage | Mean | Min–Max | Stdev | Model-gen | Deterministic overhead |
|---|---|---|---|---|---|
| planner | 23.8 s | 22.7–24.6 | 1.0 s | 23.8 s | ~0.00 s |
| retrieval | 0.23 s | 0.08–0.34 | 0.13 s | 0 | 0.23 s |
| analyst | 99.9 s | 86.7–112.9 | 13.1 s | 99.9 s | ~0.00 s |
| **end-to-end (wall)** | **125.3 s** | 111.4–140.3 | 14.5 s | | |

**Wall-clock is ~98% local model generation.** Retrieval is deterministic tool execution
(~0.2 s); deterministic validation/prep overhead is **sub-0.01 s per stage**.

### Phase B — investigation, historical evidence (7B / 14B, 55 timed runs)

Mined from persisted run records (`summarize_run_history.py`). Heterogeneous — varied
corpora, questions, configs, and outcomes — so these are **central tendencies with real
variance**, not a controlled experiment. "End-to-end" here = sum of stage latency.

**`qwen2.5:7b-instruct` — 45 runs** (8 answer_ready, 20 abstained, 17 failed):

| Stage | Mean | Min–Max | Stdev | n |
|---|---|---|---|---|
| planner | 84.7 s | 48.9–138.9 | 25.8 | 46 |
| retrieval | 0.1 s | 0.0–0.3 | 0.1 | 35 |
| analyst | 212.6 s | 96.3–340.4 | 86.8 | 29 |
| critic | 131.6 s | 65.7–233.3 | 60.3 | 18 |
| guide | 72.6 s | 41.0–139.6 | 45.7 | 6 |
| **end-to-end** | **286.0 s (~4.8 min)** | 54.2–715.4 | 185.0 | 45 |

**`qwen2.5:14b-instruct` — 9 runs** (5 answer_ready, 1 abstained, 3 failed):

| Stage | Mean | Min–Max | Stdev | n |
|---|---|---|---|---|
| planner | 216.6 s | 108.1–365.0 | 94.2 | 9 |
| analyst | 497.6 s | 293.1–1202.3 | 324.5 | 7 |
| critic | 302.7 s | 240.9–396.8 | 51.2 | 6 |
| guide | 158.8 s | 84.3–381.3 | 114.8 | 6 |
| **end-to-end** | **911.4 s (~15.2 min)** | 182.9–1550.6 | 458.3 | 9 |

## The "~14 minute → ~4–5 minute" claim

**Not preserved as an optimization claim** — there is no recorded baseline for it anywhere
in the repository, docs, or git history, and inventing one is out of scope. What the
measured data *does* support: end-to-end scales with model size, and the two regimes in the
recorded runs line up with the remembered figures —

- **14B ≈ 15.2 min** mean end-to-end, and
- **7B ≈ 4.8 min** mean end-to-end.

So a "~14 min → ~4–5 min" change is **consistent with a 14B → 7B model downgrade** in the
recorded runs, **not** with a controlled pipeline optimization. Stated honestly: the
improvement is a **model-size trade-off**, evidenced by aggregate central tendencies across
heterogeneous runs (high variance; see stdev columns), not a measured before/after of a
code change.

## Identified bottleneck

Unambiguous and consistent across all three models: **model generation dominates, and the
analyst is the single largest stage** (7B: analyst 213 s ≫ critic 132 s > planner 85 s >
guide 73 s). Retrieval is deterministic and negligible (~0.1–0.2 s); deterministic
validation/finalization overhead is sub-second everywhere. Any future latency work belongs
at the analyst prompt/generation — **not** attempted in this phase.

## Limitations of this benchmark

- **Historical runs are not a controlled experiment** — different corpora, questions,
  policies, and outcomes are pooled per model. Treat the 7B/14B numbers as measured
  central tendencies with the reported variance, not an A/B result.
- **Fresh runs are 3B-only.** 7B is not currently pulled and OOMs on this machine (~5 GB
  vs ~1.1 GB free); 14B (9 GB) OOMs harder. So freshly measured critic/guide timings are
  unavailable here — those come from the historical 7B/14B records.
- **3B fails at analyst grounding** over the rich curated corpus, so its end-to-end (~125 s)
  is time-to-failure, not time-to-answer.
- **Acquisition numbers are live-network dependent** (source-API health, bandwidth), one
  topic, lexical path only (enrichment/embeddings off, which would add model + geo passes).
- **"End-to-end" differs by source:** fresh = wall clock around `workflow.run`; historical
  = sum of stage `latencyMs` (excludes queue wait and persistence). Neither includes the
  Phase A acquisition time or UI/SSE transport.
- All figures are CPU-only on one machine; a GPU host or different model would change the
  absolute numbers substantially.

## Reproduce

From `backend/` with the venv active and Ollama running:

```bash
python -m benchmarks.perf.time_acquisition --topic "Congress of Vienna" --earliest 1814 --latest 1815 --max-sources 6
python -m benchmarks.perf.run_investigation_benchmark --model qwen2.5:3b-instruct --repeats 3
python -m benchmarks.perf.summarize_run_history
```
