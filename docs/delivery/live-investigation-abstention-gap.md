# Scoping — Live investigations abstain over auto-acquired corpora

**Status:** scoped, not started
**Owner cue:** raised after a live "Anaconda Plan" search returned no answer despite good sources.
**Related fixes already landed:** discovery topic-relevance ranking (`8a7c0dd`), planner result-limit clamping (`04d5977`).

## Symptom

Typing an arbitrary question (e.g. *"what was the Anaconda Plan about?"*) runs the full live path — scope → acquire → build corpus → four agents — but the investigation **abstains with no answer**, which reads as "the engine only works for the two curated topics." It is not topic-restricted: acquisition and retrieval both work. The investigation layer is where it fails.

## Evidence (measured, not inferred)

For the live-built corpus `acq-anaconda-plan-712171af0d0a`:

- **Acquisition is good.** 3 sources, **41 passages**; the first passage is the exact definition (*"The Anaconda Plan was a strategy outlined by the Union army … proposed by General-in-Chief Winfield Scott"*); 'anaconda' appears 55×, 'blockade' 51×.
- **Retrieval is good.** Direct `search_passages("anaconda plan")` returns **40 matches**, top hit being that definition passage.
- **The planner is the failure.** The corpus exposes only two tools — `get_map_context`, `search_passages` — because an auto-acquired corpus is a *draft*: **passages + events only, 0 claims / 0 relationships / 0 knowledge-states**. The 3B planner classified the question as `DISPUTED_INTERPRETATION` and planned a **single `get_map_context` call — never `search_passages`**. `get_map_context` yields no answer-bearing evidence here, so retrieval returned **0 passages** and the analyst abstained ("the available evidence did not support a grounded answer").

Two upstream brittleness bugs were found and fixed along the way (already committed): discovery pulled in namesakes ("Anaconda (1997 film)") with no relevance gate; and the planner rejected the *entire* plan when a tool asked for a result limit one over the budget. Neither was the core of this gap — the core is **planner tool-selection over passages-only corpora**.

## Root cause

The four-agent planner is designed around a **fully-synthesized** corpus (claims, relationships, knowledge-states, evidence links — what the two curated corpora have and what the E3/E6 work was tuned against). An **auto-acquired corpus is a draft**: it has raw passages and a thin timeline but none of the synthesized records. Over that shape:

1. Most typed tools are (correctly) filtered out, leaving `search_passages` as effectively the only answer-bearing tool.
2. But nothing **guarantees** `search_passages` runs. The planner is free to pick `get_map_context` (or misclassify the question), and a small local model frequently does — producing a valid plan that retrieves nothing.

So the pipeline has no **retrieval floor**: a weak plan yields zero evidence instead of falling back to the obvious "just search the corpus text for the question."

## Contributing factors

- **Small-model planning quality.** On 3B (used here for memory), question-type classification and tool selection are unreliable. 7B is better but does not fit this machine's free RAM (~1.8 GB vs ~5 GB needed), and even 7B is not guaranteed to pick `search_passages`.
- **Draft vs synthesized corpus mismatch.** Acquisition stops at passages+events; the investigation layer expects more. Either acquisition should synthesize more, or the investigation layer should degrade gracefully to passage-only evidence.

## Options

- **A — Guaranteed passage-retrieval floor (recommended).** The retrieval runner always executes a baseline `search_passages` on the user's question and merges it into the evidence bundle, regardless of the planner's tool choices. Model-independent; directly fixes the observed failure (the 41 passages reach the analyst even when the planner picks the wrong tool). Must respect the existing budget/citation contracts so grounding still holds.
- **B — Planner steering for draft corpora.** When the corpus offers only `search_passages`/`get_map_context`, bias the prompt (or a deterministic post-step) to always include a `search_passages` call for descriptive/definitional questions. Cheaper than A but still leans on the model doing the right thing.
- **C — Synthesize more at acquisition time.** Extend the acquisition enrichment to generate claims/relationships so the corpus is no longer a draft. Largest scope; overlaps existing enrichment work; higher latency and more local-model calls (worse on constrained hardware).
- **D — Require a capable planning model.** Document/enforce 7B+ for live investigations. Doesn't fix the "planner may still skip search_passages" root cause and is blocked by this machine's memory.

## Recommendation

**A, then B.** A gives a robust, model-independent retrieval floor so "search anything" reliably returns *something* grounded in the acquired passages; B improves plan quality so the floor is rarely the only thing that fires. Defer C (synthesis) as a separate, larger track and treat D as a docs/ops note, not a fix.

## Proposed slices

1. **S1 — Passage-retrieval floor.** In the retrieval runner, after executing the planned calls, if no `search_passages` result is present, run one bounded `search_passages(question)` and merge its hits into the bundle/reference index under the existing per-tool and aggregate budgets. Tests: a plan that omits `search_passages` over a passages-only corpus still yields a non-empty reference index; budgets and citation validity are unchanged; a plan that already searched is not double-charged.
2. **S2 — Planner steering.** Prompt/heuristic so descriptive questions over a draft corpus plan a `search_passages` call; verify with a deterministic-provider planner test.
3. **S3 — Re-verify live.** Re-run the Anaconda investigation end to end (7B when memory allows, else 3B) and confirm a cited answer, not an abstention.

## Verification target

The Anaconda corpus already on disk is the fixture: with S1, the four-agent run over it must reach `answer_ready` with ≥1 citation resolving to one of its 41 passages — no re-acquisition, no larger model required.

## Explicitly out of scope here

Acquisition-side synthesis of claims/relationships (option C), any change to the grounding/citation contracts, and the memory/hardware constraint (a separate ops concern).
