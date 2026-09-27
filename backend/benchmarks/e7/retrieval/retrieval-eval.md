# Frozen retrieval evaluation — passages-only draft corpora

Retrieval measured in isolation (before answer quality): lexical-only corpus vs.
the recall-additive `HybridCorpus`, at the **deployed** budget (`maxResults=2`), over a synthetic subject-free draft corpus with a
deterministic embedder (no Ollama — reproducible byte-for-byte).

## Aggregate

- Relevant passages available (labeled): **5**
- Relevant retrieved — lexical: **2** (recall 0.4) → hybrid: **4** (recall 0.8)
- **Recall gain: +2 relevant passages**
- Duplicate passages returned (across lanes): 0 (fusion dedupes by id)

## Per case

| Case | Query | Relevant avail. | Lexical rel. | Hybrid rel. | Gain | Distinct src (lex→hyb) | Dup ids | Hybrid ms |
|---|---|---|---|---|---|---|---|---|
| reworded-relevant | `harbor blockade` | 3 | 1 | 2 | +1 | 2→2 | 0 | 0.579 |
| pure-recall-lexical-empty | `mountain railway` | 1 | 0 | 1 | +1 | 0→1 | 0 | 0.341 |
| aligned-no-regression | `harbor festival regatta` | 1 | 1 | 1 | +0 | 2→2 | 0 | 0.4 |
| absent-evidence | `diplomatic congress protocol` | 0 | 0 | 0 | +0 | 0→0 | 0 | 0.212 |

### What each case shows

- **reworded-relevant** — Relevant evidence is worded differently from the query; lexical can reach only one of three relevant sources, the rest are semantic-only.
- **pure-recall-lexical-empty** — Query shares no token with any source; the one relevant source is reachable only semantically (lexical returns nothing relevant).
- **aligned-no-regression** — Lexical already reaches the single relevant source; hybrid must retain it and not displace it (control).
- **absent-evidence** — No source is about the query's concept; neither lane should find relevant evidence (measures the precision cost of unconditional semantic recall).

## Design & honest limits

- The reserve guarantees up to `floor(k/2)` slots to the *most-similar* passages the
  lexical lane missed, while the top `k - reserve` lexical hits are always kept — so a
  strong lexical hit is never fully displaced (see the **aligned-no-regression** control:
  its result is identical to lexical).
- A semantic-only passage is admitted only when cosine similarity is strictly positive.
  On the **absent-evidence** case (query orthogonal to every source) this guard suppresses
  recall entirely, so hybrid returns exactly what lexical does — no noise is injected.
  This is a similarity guard, not a tuned threshold: real embeddings return positive
  similarities for the nearest passages, so in production the reserve is filled by the
  genuinely-most-similar missed passages, and the critic/grounding still gate synthesis.
- Latency here reflects the frozen embedder (~free). Real `nomic-embed-text` embedding
  latency on CPU is measured in the Anaconda end-to-end trace, not here.
