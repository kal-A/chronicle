# Phase E4 — Historical Critic and Investigation Guide

**Status:** implemented and verified locally on `phase-e-ai-core`; uncommitted and unpushed.

## Delivered

- `CriticDecision` with approve, downgrade, retrieve-more, reject, and abstain outcomes; every non-abstained final review must disposition every Analyst statement exactly once.
- A corpus-blind `HistoricalCritic` that checks chronology/causation, projected knowledge, source dependence and role confusion, counterevidence, disputed interpretations, date/location precision, generalization, unsupported claims, and failure to abstain.
- One bounded Critic retrieval path. The Critic may request exactly one registered tool call; Chronicle reruns the Analyst and Critic once. A second retrieval request becomes an explicit deterministic abstention.
- `AgentAnswer` and all twelve map-first `AssistantAction` variants from the product contract.
- A closed `ActionReferenceIndex` derived from the validated package. Location, event, lens, relationship, system path, actor, evidence, source, and time actions are rejected if unsupported by the current investigation.
- A critic-approved Guide boundary: rejected statements are never included in its prompt; exposed statement text stays exact; limitations must originate with Analyst/Critic material.
- Canonical citation attachment. The model selects approved statement IDs, but Chronicle mechanically reattaches the complete grounded citations. Model-omitted or model-invented citation fields never reach the final answer.
- E4 audit persistence in `AgentRunRecord`/`AgentRunStore`: Critic decisions and validations, final answer and action validation, model/tool calls, named stages, retries, latency, and abstention state.

## Verification

- E4 focused suite: 14 tests passed.
- Complete AI/tool/provider plus agent-run-storage suite: 354 passed, 1 skipped, and 2 opt-in local-Ollama tests deselected in the ordinary run.
- Opt-in real local model smoke (`qwen2.5:7b-instruct`): Critic verdict `approve`, Guide status `answered`, canonical citation validation passed, 78.69 seconds for Critic → Guide on the CPU-only development machine.
- Python compilation and `git diff --check` passed for the E4 source/test slice.

The first live attempts exposed two useful failures that the deterministic provider could not reveal: the Critic initially approved without dispositioning the statement, and the Guide initially omitted optional citation fields. The contract/prompt now names every required statement ID, and citations are attached deterministically rather than copied by the model.

## Known blocker outside E4

The repository-wide backend suite cannot currently collect because the tracked legacy `backend/src/chronicle/storage/run_store.py` is deleted in the existing working tree; three remaining package-generation/workflow tests still import it. E4 does not restore or include that unrelated deletion. The complete AI slice is green independently.

## Next

Phase E5 should add the first FastAPI/streaming boundary around the four-agent workflow, including named progress events and cancellation. Phase E6 then connects the landing search and investigation Ask panel. With the measured local latency, streaming visible stage progress is a product requirement rather than polish.
