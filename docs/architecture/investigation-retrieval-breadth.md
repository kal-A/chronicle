# Investigation-grade retrieval breadth (E10)

Follows [`higher-recall-retrieval.md`](./higher-recall-retrieval.md). That phase proved semantic
recall works but the Anaconda acceptance query still abstained because an acquired corpus of 79
passages across 3 sources was reduced to ~2 passages from 1 source before synthesis. This phase
makes the retrieval/orchestration path assemble **enough distinct, relevant, complementary
evidence** for a real investigation while preserving Chronicle's grounding, critic, citation, and
abstention guarantees.

Two coupled changes: (1) a **breadth mechanism** (multiple complementary searches) and (2) an
**analyst-schema compaction** that the breadth exposed as necessary. No grounding/critic/citation
behavior was weakened, no retrieval budget or the 24k analyst-prompt ceiling was raised, and no
subject-specific logic was added.

## 1. The bottleneck (traced to code)

A planner+retrieval probe on the real Anaconda corpus showed one search returning 2 passages from
1 source, using only 2986 of the 8000-char retrieval budget. Three reducers:

1. **`planner_schema.py` `plannedToolCalls maxItems = 1`** — the structured-output schema
   hard-capped the plan to **one** tool call, even though the runner is already budgeted for
   `maxInitialToolCalls=3` / `maxTotalToolCalls=4` / `maxAggregateResults=16` / 8000 chars. The
   multi-search machinery existed; the schema forbade using it.
2. **`maxResultsPerTool=2`** — that one search returned ≤2 passages.
3. **No breadth/diversity mechanism** — the retrieval floor only *backstopped* (fired when no
   search existed); the single follow-up was critic-gated.

## 2. The breadth mechanism (uses existing budget; no constants raised)

- **Planner decomposition** — `plannedToolCalls maxItems` now = `policy.maxInitialToolCalls`, and
  the planner prompt instructs decomposing an evidence-seeking question into up to 3 *distinct*
  complementary searches. (`maxItems=1` was an "E6 runtime" simplification, not a safety
  invariant; the planner's own validation already allowed up to `maxInitialToolCalls`.)
- **Deterministic breadth backstop** (`InvestigationRunner._augment_with_floor`) — for
  passages-only **draft** corpora only, if the plan under-decomposes, the runner adds complementary
  bounded `search_passages` calls (distinct sub-queries derived from the normalized question) up to
  `maxInitialToolCalls`. Gated on corpus shape (no claims/relationships/timeline/knowledge/map), so
  curated/synthesized corpora and the E7 harness are untouched.
- **Relevance-gated diversity** — breadth comes from complementary sub-queries plus #9's
  recall-additive `HybridCorpus` (positive-similarity guard). There is **no** naive source-quota
  that could pull off-topic passages in to inflate source counts.

Breadth stays within the already-provisioned budget: 3 searches × 2 = 6 passages ≈ 6000 chars < 8000.
`k=2`, aggregate 8000, and total ≤4 calls are unchanged.

## 3. Analyst-schema compaction (the breadth exposed a real ceiling)

The larger evidence bundle overflowed a **different** budget: the analyst prompt
(`maxPromptCharacters`, hard-capped at 24000). At 3 passages the prompt reached **25711** chars and
the analyst raised a boundary error *before any model call* → the run **failed** (worse than a clean
abstention). The dominant term was the bundle-derived response schema (**14233** chars), built from
two `oneOf`s that materialize one full variant per retrieved item:

| `$def` | Before | After | How |
|---|---|---|---|
| `AnalysisCitation` | 4181 (`oneOf`×10) | **~747** | one object with per-field enums over the retrieved values (same emitted fields) |
| `AnalysisStatement` | 6593 (`oneOf`×5) | **~1415** | one object with `statementKind` enum + `knowledgeAwareness` `Awareness|null` |
| **schema total** | **14233** | **~5506** | |
| **analyst prompt** | **25711 (FAILS)** | **~17000** (headroom ~7000) | |

**Why this is safe (duplication removed, not validation deleted).** Every constraint the `oneOf`s
encoded is independently and authoritatively re-enforced after generation:
- `grounding.validate_grounding` resolves each citation tuple/record against the bundle — unknown
  tool call, non-co-occurring passage/source/target tuple, unknown basis record, and role-without-
  evidence-link are all rejected there (grounding.py).
- The Pydantic `AnalysisStatement`/`AnalysisCitation` validators enforce KNOWLEDGE↔awareness,
  synthesis↔inferred, and "cite ≥1 retrieved record" at parse time (analysis.py).

The emitted `AnalysisCitation`/`AnalysisStatement` contracts are unchanged. Rejection-parity tests
assert the same invalid references are still rejected after compaction.

**No combinatorial cliff.** Schema growth is now linear in evidence breadth (enum entries), not
combinatorial (variant explosion). Measured across breadth (deployed `k=2`, 1→4 searches):

| distinct records | schema chars | citation | statement |
|---|---|---|---|
| 4 | 5242 | 560 | 1336 |
| 6 | 5347 | 633 | 1368 |
| 8 | 5452 | 706 | 1400 |
| 10 (budget max) | 5564 | 786 | 1432 |

~54 chars/record; the statement object is effectively constant. At the realistic maximum (10
records) the whole schema is ~5.5k — versus 14.2k at just 3 passages before.

## 4. Frozen breadth evaluation (independent of generation, no Ollama)

`backend/benchmarks/e7/retrieval/run_breadth_eval.py` (frozen by `tests/acquisition/test_breadth_eval.py`)
measures single-query vs decomposed retrieval at the deployed budget:

| Case | Distinct relevant (single→decomposed) | Aspects (single→dec.) | Noise pulled |
|---|---|---|---|
| multi-aspect | 2 → **6** | 1 → **3** | 0 |
| dominant-relevant-source | 2 → **6** | 1 → **3** | 0 (source diversity stays 1 — breadth ≠ source count) |
| dominant-noise-source | 2 → **4** | 1 → **2** | **0** (namesake noise never pulled — diversity is relevance-gated) |

## 5. Anaconda Plan — end-to-end trace (real 7B, semantic on, clean corpus)

| Stage | Result |
|---|---|
| Scope resolution (7B) | terms *Anaconda Plan, Union strategy, American Civil War, blockade, railroad, Mississippi River* |
| Acquisition (term-scoped) | **3 on-topic sources** (Anaconda Plan 25, Union blockade 36, Turning point 18), **79 passages**; namesake films dropped by the scope terms |
| Retrieval | **3 searches** (planner `query-anaconda-plan-strategy` + 2 backstop) → **3 distinct passages, 2 sources**, 5965/8000 chars (was 2 passages / 1 source pre-E10) |
| Analyst | **succeeded** (224 s), **grounding valid (0 issues)** — citations resolved, no prompt overflow |
| Critic | **reject** — "the retrieved passages do not provide direct evidence for the specific impact… the statements are inferred and lack direct support" |
| Guide | **principled abstention** |

The outcome now follows from **evidence quality (the critic)**, not prompt overflow. The analyst
executes and grounds; the critic judges 3 inferred passages insufficient for the question's specific
causal/impact claims and abstains. That is the validation spine working correctly — a legitimate
abstention, not weakened validation.

## 6. Remaining bottleneck & DoD

- **DoD met:** #10 retrieval gain preserved (2→3 passages, 1→2 sources); the analyst executes;
  citations resolve (grounding valid); grounding/critic unchanged; the final abstention follows from
  evidence quality, not prompt overflow. Full backend suite (919) and CI green.
- **Remaining bottleneck:** at the deployed `maxResultsPerTool=2`, three searches over this corpus
  still net only **3 distinct passages** — the planner's search and one backstop search overlap on
  the top passage (`psg-0000-0000`), and a third derived query added none. So the binding limit is
  now **per-search `k=2` plus cross-search query overlap**, not the schema or the analyst prompt.
  The critic reasonably abstains on 3 inferred passages for a detailed causal question. Further
  breadth (a higher per-search `k`, stronger query diversification to reduce overlap, or accepting
  inferred synthesis for descriptive questions) is the next lever — deliberately out of scope here,
  and none is a grounding or validation change.
