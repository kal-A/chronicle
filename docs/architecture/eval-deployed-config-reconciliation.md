# Eval ↔ deployed reconciliation, and the Anaconda acceptance trace

Two things this documents: (1) the E7 `full_workflow` evaluation strategy and the deployed
`create_default_app` pipeline now build through **one shared factory**, so evaluation
measures the production configuration rather than a drifted one; and (2) an end-to-end
acceptance trace of an evidence-rich live query ("How did the Union's Anaconda Plan shape
the strategy and course of the American Civil War?"), including exactly why it still
abstains and where that abstention originates.

No grounding or validation gate was weakened anywhere in this work.

## 1. The reconciliation (shared factory)

Before, the E7 `full_workflow` strategy hand-built the workflow with **different settings**
than the deployed app:

| Aspect | Deployed (`create_default_app`) | E7 `full_workflow` (before) |
|---|---|---|
| Execution policy | `maxResultsPerTool=2`, `maxAggregate=8000` | agent defaults (`4`, `14000`) |
| Retrieval floor | `retrieval_floor=True` | **off** |
| Planner tool-spec representation | `COMPACT` | default |

Fix: [`ai/orchestration/factory.py`](../../backend/src/chronicle/ai/orchestration/factory.py)
exposes `default_execution_policy()` + `build_default_workflow(provider, store, *, policy=None)`,
which encode the production configuration once. Both `create_default_app` **and** the E7
`FullWorkflowStrategy` now call it — the eval exercises production-equivalent logic through
shared code, not a copied parallel config.

Verification:
- Full backend suite green (897 passed). One eval test fixture was aligned to the shared
  config (its scripted draft now discloses the retrieval truncation the tight aggregate
  budget causes — grounding still fully enforced, just an accurate production-config draft).
- The deterministic regression profile (`deterministic_full`, 24×4) is **byte-identical** to
  the committed baseline: the reconciliation does not perturb the deterministic gate.

### 6-case 7B subset — before vs after reconciliation

Same frozen subset, `qwen2.5:7b-instruct`, `full_workflow`:

| Case | Expect | Before (drifted) | After (reconciled) |
|---|---|---|---|
| direct-source-date | answer | abstained | abstained |
| relationship-doctrine-to-intervention | answer | abstained | **partial, 1 cite** |
| actor-knowledge-unsupported-personal | abstain | abstained ✓ | abstained ✓ |
| direct-reported-assurance | answer | abstained | **partial, 2 cites** |
| actor-knowledge-supported-awareness | answer | abstained | abstained |
| missing-exact-receipt-hour | abstain | abstained ✓ | abstained ✓ |

Aggregate after reconciliation (`benchmarks/e7/baseline/qwen7b-reconciled-report.json`):
`citation_validity 1.000 (3/3)`, `citation_coverage 1.000 (3/3)`, `abstention_correct
0.333 → 0.667 (4/6)`, `required_evidence_recall 0 → 0.143 (1/7)`; safety gates
(`no_forbidden_evidence`, `no_cross_corpus_leakage`, `unacceptable_claims`) all pass. So the
reconciliation moved 2 of 4 answerable cases from **total abstention → grounded partial
answers with valid citations**, with grounding still enforced. This is a real improvement,
not a scoring change.

## 2. Anaconda Plan acceptance query — end-to-end trace

Run through the faithful deployed path (7B): scope resolution → acquisition → the reconciled
workflow.

| Stage | Result |
|---|---|
| Scope resolution (7B) | terms: *Anaconda Plan, Union strategy, American Civil War, blockade, railroad, Mississippi River* |
| Acquisition | **3 on-topic sources** (Anaconda Plan, Union blockade, Turning Point of the ACW), **79 passages**. With the resolved terms the namesake **snake-movie sources are correctly dropped** (they survived only when no terms were supplied). **civilwardigital.com is surfaced as a reference**, not ingested (its full text is not retrievable) — no hard-coding. |
| Retrieval | ~**2 passages**, 1 source, 0 evidence links, truncated |
| Analyst | **succeeded** — produced grounded, cited statements with the truncation disclosed (grounding `valid:true`) |
| Critic | **rejected** — "the analysis overclaims … details and impacts not supported by the retrieved evidence" |
| Guide | abstains (0 approved statements) |

### Where the abstention originates

Not in acquisition (good: 79 on-topic passages), and **not** in analysis / grounding /
validation (those work — the analyst grounds, and the critic correctly refuses an
under-supported synthesis). It originates in **retrieval recall**: the analyst receives only
~2 passages, so its synthesis over-reaches what those two passages support and the critic
rejects it. The system fails **safe** — it abstains rather than shipping an overclaim.

### Why retrieval recall is capped here (the genuine, documented limit)

- A **single tool result is contract-capped at 6000 characters** by
  `ToolResultEnvelope.serializedCharacters` (`le=6000`) — roughly 2 Wikipedia passages. This
  is a hard schema ceiling, independent of the execution policy.
- On a **passages-only draft corpus**, lexical passage-search is the only evidence tool, and
  additional searches (e.g. a broad question-level search alongside the planner's narrower
  one) **overlap on the same top passages**, so they add little unique recall.
- Net: ~2 unique passages reach the analyst regardless of the retrieval *budget*.

An attempt to raise the retrieval budget for draft corpora (gated by corpus shape, per the
agreed approach) was implemented and then reverted: it does **not** address this limit,
because the binding constraint is the 6000-char single-result contract cap plus lexical
overlap, not the budget. Raising the per-result cap would violate the contract; raising only
results/aggregate is inert when searches overlap.

### The genuine remaining fix (a separate, larger track)

Higher-recall retrieval for draft corpora — semantic/embedding retrieval
(`CHRONICLE_ENABLE_SEMANTIC` + a pulled embedding model) to surface *distinct* relevant
passages, and/or query diversification that returns non-overlapping passages, and/or a
deliberate revisit of the 6000-char single-result contract cap. Each is a scoped retrieval
change with a latency trade-off and uncertain payoff on CPU-only hardware; none is a
grounding or validation change. This is deliberately **not** undertaken here — this phase
reconciled configuration and diagnosed the acceptance failure precisely; forcing the answer
by weakening grounding/validation was explicitly out of scope.

## Definition-of-done status

- ✅ Eval and deployed configuration aligned through shared logic (the factory).
- ✅ Deterministic regression profile intact (byte-identical).
- ✅ Frozen 6-case 7B subset rerun; before/after recorded above.
- ✅ Anaconda acceptance query exercised end-to-end; full trace above.
- ✅ Citations/grounding remain enforced (never weakened).
- ⚠️ Evidence-rich Anaconda query still abstains — traced to a **retrieval-recall** limit
  (6000-char single-result contract cap + lexical overlap on a draft corpus), with the
  higher-recall fix scoped as a separate track above. The abstention is the validation spine
  working on thin evidence, not an incorrect abstention from sufficient evidence.
- ✅ Tests and CI green.
