# Frozen retrieval-breadth evaluation (E10 → E11)

E10 lexical token-partition decomposition (**before**) vs E11 evidence-facet
decomposition (**after**), over passages-only draft corpora at the deployed budget
(`maxResults=2` per search, ≤3 searches: a broad query
plus derived sub-queries), with a deterministic embedder (no Ollama). Diversity is
relevance-gated: off-topic / namesake sources are never pulled in.

| Case | Relevant avail. | Distinct relevant (before→after) | Aspects (before→after) | Relevant sources (before→after) | Noise (before/after) | Broad overlap (before→after) | Derived searches (before→after) |
|---|---|---|---|---|---|---|---|
| overlap-recoverable | 6 | 2→6 | 1→3 | 1→3 | 0/0 | 2→0 | 2→2 |
| single-source | 6 | 2→6 | 1→3 | 1→1 | 0/0 | 2→0 | 2→2 |
| noisy-sources | 6 | 2→6 | 1→3 | 1→3 | 0/0 | 2→0 | 2→2 |
| single-dimension | 4 | 2→2 | 1→1 | 1→1 | 0/0 | 2→0 | 2→0 |

### Exact queries and top-k (after = E11 facet decomposition)

**overlap-recoverable** — _How did the program operate and what consequences did it cause for the region_
- `program region overview account` → psg-0000-0000(1.0), psg-0000-0001(1.0)
- `program region how it worked in practice` → psg-0001-0000(1.0), psg-0001-0001(1.0)
- `program region effects and outcomes` → psg-0002-0000(1.0), psg-0002-0001(1.0)

**single-source** — _How did the program operate and what consequences did it cause for the region_
- `program region overview account` → psg-0000-0000(1.0), psg-0000-0001(1.0)
- `program region how it worked in practice` → psg-0000-0002(1.0), psg-0000-0003(1.0)
- `program region effects and outcomes` → psg-0000-0004(1.0), psg-0000-0005(1.0)

**noisy-sources** — _How did the program operate and what consequences did it cause for the region_
- `program region overview account` → psg-0000-0000(1.0), psg-0000-0001(1.0)
- `program region how it worked in practice` → psg-0001-0000(1.0), psg-0001-0001(1.0)
- `program region effects and outcomes` → psg-0002-0000(1.0), psg-0002-0001(1.0)

**single-dimension** — _When was the program established in the region_
- `program region overview account` → psg-0000-0000(1.0), psg-0000-0001(1.0)

### What each case shows

- **overlap-recoverable** — A broad query and the E10 token-partition sub-queries overlap on the subject passages; E11 facet sub-queries instead recover distinct mechanism and consequence evidence.
- **single-source** — All relevant evidence lives in one source spanning subject, mechanism and consequence aspects; facet decomposition improves passage/aspect coverage while relevant source diversity legitimately stays 1.
- **noisy-sources** — One relevant source set plus two larger namesake noise sources (mirrors the Anaconda films). Facet decomposition must NOT pull noise passages to diversify.
- **single-dimension** — A straightforward factoid question invokes no analytical evidence dimension, so the backstop derives no extra searches and retrieval stays at one query.

## Notes

- **Overlap recovered:** the token-partition `before` lands its sub-queries back on the
  subject passages (high broad overlap, one aspect); facet `after` sub-queries reach distinct
  mechanism/consequence aspects (broad overlap drops, aspects rise).
- **Relevance-gated diversity:** the noisy-sources case retrieves **zero** namesake-noise
  passages after decomposition — breadth never trades relevance for source spread.
- **Breadth ≠ source count:** the single-source case gains distinct relevant passages and
  aspects with relevant source diversity fixed at 1.
- **Factoid gate:** the single-dimension question derives **no** extra searches (retrieval
  stays at one query), so simple lookups are not over-decomposed.
- Latency reflects the frozen embedder (~free); real embedding latency is in the Anaconda trace.
