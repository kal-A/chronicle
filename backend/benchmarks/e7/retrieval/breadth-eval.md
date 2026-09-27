# Frozen retrieval-breadth evaluation (E10)

Single broad query vs decomposed sub-query retrieval over passages-only draft
corpora, at the deployed budget (`maxResults=2` per search), with a
deterministic embedder (no Ollama). Diversity is relevance-gated: off-topic /
namesake sources are never pulled in.

| Case | Relevant avail. | Distinct relevant (single→dec.) | Aspects covered (single→dec.) | Relevant sources (single→dec.) | Noise pulled (single/dec.) | Dup rate | Ctx chars (single→dec.) |
|---|---|---|---|---|---|---|---|
| multi-aspect | 6 | 2→6 | 1→3 | 1→3 | 0/0 | 0.0 | 1000→4386 |
| dominant-relevant-source | 6 | 2→6 | 1→3 | 1→1 | 0/0 | 0.0 | 1000→4386 |
| dominant-noise-source | 4 | 2→4 | 1→2 | 1→2 | 0/0 | 0.0 | 1000→2876 |

### What each case shows

- **multi-aspect** — Answer needs evidence from three aspects, each in its own source; one broad query reaches one aspect, decomposition reaches all three.
- **dominant-relevant-source** — All relevant evidence lives in one source spanning three aspects; breadth improves distinct relevant passages even though source diversity stays 1.
- **dominant-noise-source** — One relevant source plus two larger namesake noise sources (mirrors the Anaconda films). Decomposition must NOT pull noise passages to diversify.

## Notes

- **Relevance-gated diversity:** the dominant-noise-source case retrieves **zero** noise
  passages under decomposition — breadth never trades relevance for source spread.
- **Breadth ≠ source count:** the dominant-relevant-source case gains distinct relevant
  passages with source diversity fixed at 1, showing breadth is measured in evidence, not sources.
- Latency reflects the frozen embedder (~free); real embedding latency is in the Anaconda trace.
