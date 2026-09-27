# Higher-recall retrieval for passages-only draft corpora

The [eval ↔ deployed reconciliation](./eval-deployed-config-reconciliation.md) traced the
Anaconda acceptance query's abstention to **retrieval recall**, not acquisition, grounding,
or validation: acquisition is healthy, but lexical passage-search over a passages-only draft
corpus exposes only a couple of overlapping passages, so the critic correctly rejects an
under-supported synthesis. This documents the smallest principled retrieval change that lifts
recall on those corpora, the frozen retrieval evaluation that measures it in isolation, and
the end-to-end Anaconda re-run.

**No grounding, critic, validation, or abstention gate was changed. No retrieval budget or
contract cap was raised.** This changes *which* passages fill the caller's existing result
slots — adding relevant recall — not the number of slots.

## 1. What already existed (reused, not rebuilt)

Chronicle already carried a complete local-semantic substrate, all free/local:

| Piece | File |
|---|---|
| Local embeddings (`nomic-embed-text`, no key/cost) | `acquisition/embeddings.py` |
| SQLite vector store + cosine query | `acquisition/vector_store.py` |
| RRF fusion + `SemanticReranker` | `acquisition/retrieval.py` |
| `HybridCorpus` decorator, wired in `CorpusBuildService`, gated by `CHRONICLE_ENABLE_SEMANTIC` | `acquisition/hybrid_corpus.py`, `acquisition/build_service.py`, `api/app.py` |

The gap was one property, stated in `HybridCorpus`'s own docstring: it **re-ranked only within
the lexical candidate set**, so it "does not add recall for passages the lexical lane misses
entirely." Its root cause is two lines: `corpus/search.py` drops any passage with **zero query-token
overlap** (no score factors → skipped), and `HybridCorpus` inherited that miss because it only
reordered what lexical returned.

## 2. The change: recall-additive `HybridCorpus`

`SemanticReranker` gained a `recall(query, k)` that returns the nearest passage ids over the
**whole** vector store (not just a lexical candidate set). `HybridCorpus.search_passages` now,
when its reranker exposes `recall`:

1. gathers the expanded lexical candidates (as before);
2. queries the semantic index over the whole corpus;
3. **guarantees up to `floor(k/2)` result slots** to the most-similar passages the lexical
   lane missed (the recall gain), while **always keeping the top `k − reserve` lexical hits**
   (so a strong lexical hit is never fully displaced);
4. admits a semantic-only passage only when cosine similarity is **strictly positive** (a
   similarity guard, not a tuned threshold — orthogonal passages are never "recalled");
5. orders the chosen passages by RRF fusion; materialises a `PassageSearchHit` for any
   semantic-only passage from the corpus protocol's own getters.

**Boundary — synthesized corpora are untouched.** `HybridCorpus` is only ever attached (in
`CorpusBuildService`) to auto-acquired **passages-only draft** corpora. Curated/synthesized
corpora are never wrapped, so their retrieval — and the E7 deterministic regression that runs
on them — is byte-for-byte unchanged. Draft corpora carry no claims/relationships/evidence-links/
dates, which is why a semantic-only hit is materialised with empty links/dates by construction.

The recall path is opt-in via `CHRONICLE_ENABLE_SEMANTIC=1` (plus a pulled `nomic-embed-text`);
with the flag off, deployment serves lexical-only exactly as before.

## 3. Frozen retrieval evaluation (independent of answer quality)

A deterministic eval (`backend/benchmarks/e7/retrieval/run_retrieval_eval.py`, frozen by
`tests/acquisition/test_retrieval_eval.py`) measures retrieval in isolation on a synthetic,
subject-free passages-only draft corpus at the **deployed** budget (`maxResults=2`), with a
frozen embedder (no Ollama — reproducible byte-for-byte). Run:

```bash
python benchmarks/e7/retrieval/run_retrieval_eval.py \
  --json benchmarks/e7/retrieval/retrieval-eval.json \
  --markdown benchmarks/e7/retrieval/retrieval-eval.md
```

| Case | Query | Relevant avail. | Lexical rel. | Hybrid rel. | Gain | Dup ids |
|---|---|---|---|---|---|---|
| reworded-relevant | `harbor blockade` | 3 | 1 | 2 | +1 | 0 |
| pure-recall-lexical-empty | `mountain railway` | 1 | 0 | 1 | +1 | 0 |
| aligned-no-regression | `harbor festival regatta` | 1 | 1 | 1 | +0 | 0 |
| absent-evidence | `diplomatic congress protocol` | 0 | 0 | 0 | +0 | 0 |

Aggregate: relevant retrieved **2 → 4** (recall 0.4 → 0.8), **+2 relevant passages**, **0**
duplicate passages. The controls matter as much as the gains: `aligned-no-regression`'s hybrid
result is *identical* to lexical (a strong lexical hit is not displaced), and `absent-evidence`
injects **no** passage (the positive-similarity guard suppresses recall when nothing is even
weakly similar). This is a real recall gain, not a scoring change.

## 4. Anaconda acceptance query — end-to-end re-run (real model)

Deployed path with semantic on (`nomic-embed-text`), CPU-only:

| Stage | Result |
|---|---|
| Acquisition + index | 3 on-topic sources, **41 passages** embedded; 16-passage batch embed **1.6 s**, per-query embed **0.19 s** |
| Retrieval breadth (k=2) | lexical `[psg-…0000, psg-…0018]` vs recall-additive `[psg-…0000, psg-…0020]` — **overlap 1, one distinct passage surfaced by the semantic lane** the lexical top-2 missed |
| End-to-end (7B, ~298 s) | planner ✓ → retrieval ✓ (2 passages, 1 source, truncated) → analyst ✓ → **critic rejects** → **abstains** |

So on the real corpus the recall path **activates** (it substitutes the second lexical passage
with a semantically-selected passage the lexical lane did not rank in the top-2) at negligible
latency, and grounding/critic/abstention are **unchanged** — the query still abstains. This is
the stated success criterion: *retrieval supplies broader relevant evidence while safety is
unchanged; the final answer may still abstain when evidence remains insufficient.*

### Honest residual

At the deployed `maxResults=2` over a corpus whose relevant passages cluster in a single
source, one substituted passage is a modest breadth gain, not a source-diversity gain — two
passages from one source remain thin, so the critic still (correctly) abstains. The remaining
levers are a larger retrieval budget and multi-source / query-diversified retrieval; both were
explicitly out of scope here ("do not increase arbitrary budgets"), and neither is a grounding
or validation change. The recall-additive mechanism is proven in isolation (§3) and confirmed
active in production (§4); widening the budget is a separate, deliberate decision.

## Definition-of-done status

- ✅ Inspected existing retrieval/acquisition infra; reused embeddings + vector store + RRF (no parallel system).
- ✅ Smallest principled change: recall-additive `HybridCorpus`, gated to passages-only draft corpora; synthesized corpora unchanged.
- ✅ Retrieval evaluated independently (frozen, deterministic): recall 0.4 → 0.8, no regression, no noise, no duplicates; latency reported.
- ✅ Anaconda re-run end-to-end: recall path active, grounding/critic safety unchanged, abstention preserved.
- ✅ Full backend suite (903 passed) and CI green; anti-topic-branching guard green.
