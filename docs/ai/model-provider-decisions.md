# Model Provider Decisions

Records why Chronicle's Phase E model layer (`backend/src/chronicle/ai/models/`) is shaped the way it is, and the concrete hardware/model tradeoffs behind the Ollama-first decision recorded in `docs/decisions/ADR-003-llm-agent-system-is-product-core.md`.

## Ollama-first + provider-agnostic + deterministic-testable

- **Ollama-first**: the real model provider is local and open-weight, via a locally-running Ollama daemon. This satisfies `AGENTS.md` §5's existing "no paid infrastructure required to develop or demo the project" constraint exactly as written — no cost exception was requested or needed.
- **Provider-agnostic**: `ModelProvider` (`models/protocol.py`) is a structural `typing.Protocol`, not a base class. `DeterministicModelProvider` and `OllamaModelProvider` share zero implementation, only this shape. A future hosted provider, a different local runtime, or a fine-tuned Chronicle task model (Phase I) can be added later without changing `protocol.py` or any agent that consumes it.
- **Deterministic-testable**: every agent built on top of this layer (Planner/Analyst/Critic/Guide, E3-E4) gets a `DeterministicModelProvider` test double with zero network dependency, per `AGENTS.md` §6. `OllamaModelProvider`'s own test suite (`backend/tests/ai/models/test_ollama.py`) uses `httpx.MockTransport` exclusively — no test in this repository has ever made, or now makes, a live model call.

## Hardware audit (recorded at E1 planning time, 2026-08-05)

| | |
|---|---|
| OS | Windows 11 Home 64-bit, build 26200 |
| CPU | AMD Ryzen 5 6600H, 6 cores / 12 logical processors |
| RAM | 13.69 GB total |
| GPU | AMD Radeon integrated graphics (iGPU, no dedicated VRAM) |
| Ollama acceleration | None expected — ROCm's Windows/consumer-APU support doesn't cover this hardware class, so inference is CPU-only |

This is a real, load-bearing constraint on model choice, not a formality: 13.69 GB total RAM shared with the OS, IDE, browser, and Node dev servers realistically leaves roughly 6-8 GB for a model, ruling out anything meaningfully above 7-8B parameters at Q4 quantization — and even that runs at CPU-only speed (a few tokens/second on this hardware), not the near-instant response a hosted API gives.

## Model selection

**Primary: `qwen2.5:7b-instruct`** (Q4_K_M, ~4.7 GB on disk), reused sequentially across all four agent roles — one model, four prompts, not four separately-loaded models, which this hardware cannot hold concurrently. Chosen for the strongest structured-output/JSON-schema reliability available at a size this hardware can actually run, which matters directly: the Analyst's `AnalysisDraft` and the Critic's `CriticDecision` contracts (`docs/ai-core-instructions/02_AGENT_ARCHITECTURE.md`) are both non-trivially nested, and unreliable structured output at the model layer would corrupt every evaluation result built on top of it (`docs/ai-core-instructions/04_DOMAIN_GENERALIZATION_AND_EVALUATION.md` §9's requirement that the multi-agent design be justified by *measured* improvement, not novelty, only holds if the underlying model can reliably produce the structured output being measured).

**Fallback: `qwen2.5:3b-instruct`** (~1.9 GB), switchable via `OllamaModelProvider(model=...)` with no code change — for the Investigation Guide specifically (the least reasoning-demanding of the four roles, since it only reformats already-critic-approved material) or for faster local iteration during E3-E4 development.

## Why one model is reused sequentially across roles

Four agent roles do not mean four models. This hardware cannot hold more than one 7-8B model resident at once, and running four sequential prompts against one shared Ollama daemon (loading/evicting as needed, or keeping the single model warm) is both the practically necessary design here and, independently, the more honest evaluation setup for E7: it isolates "does splitting one model's work across four bounded, typed roles improve grounding/citation validity" from "did we just use a bigger model for one of the roles," which is exactly the comparison document `04` §9 wants to make.

## Known limitations, disclosed rather than discovered later

- **Structured-output risk**: a 7B model is measurably less reliable at complex nested schemas than a frontier hosted model. `orchestration/policies.py`'s bounded retry-with-feedback (`MAX_STRUCTURED_OUTPUT_ATTEMPTS = 2`) exists specifically because of this risk, not as generic defensive coding.
- **Latency**: CPU-only inference on this hardware is slow relative to a hosted API. E7's evaluation harness must record latency as a first-class metric (already planned per document `04` §8's "System performance" section), not treat it as incidental.
- **Context window**: practically ~8K tokens comfortable on the 7B model given this RAM budget — E2's corpus tools (E2) must return bounded, relevant excerpts, not large unfiltered dumps, or the Planner/Analyst will silently truncate context.
- **No meaningful GPU acceleration**: confirmed by the hardware audit, not assumed — worth re-checking if this code ever runs on different hardware (a discrete-GPU machine would materially change the model-size ceiling).

## Path to a fine-tuned Chronicle task model (Phase I)

`models/metadata.py` keeps provider identity and model identity as two separate record types, corrected here after an earlier draft of this document conflated them: `ProviderMetadata` carries provider-level identity and capability (`providerName`, `providerVersion`, `supportsStreaming`, `supportsStructuredOutput`, `isLocal`, `requiresApiKey`) — it has no `modelName`/`modelVersion` fields. Model identity belongs on `ModelCallRecord` instead, one call at a time: `modelName` is always populated (`OllamaModelProvider` records whatever model string it was configured with, e.g. `qwen2.5:7b-instruct`); `modelVersion` stays `None` until Ollama is actually installed and queried (`/api/show` or equivalent) for a real digest — nothing here invents a version or digest to fill the field. This is what Phase I's fine-tuning experiment needs: a corpus of real `ModelCallRecord`s (once E3+ agents are generating them, and once a runner exists to durably store them — see this document's "What is not yet durable" section below) to build a reviewed training/eval dataset from, and a provider slot (a hypothetical `FineTunedChronicleProvider`, satisfying the same `ModelProvider` protocol) to swap in for one bounded task (e.g. claim-evidence classification) without touching any agent code that calls `generate_structured()`. No agent-facing code needs to change when that day comes — that is the entire point of the protocol being structural rather than concrete.

## What is not yet durable, stated plainly

`ModelCallRecord` is an in-process return value, constructed and handed back by `generate_structured()`/`generate_text_from_verified_records()` on **success only**. Nothing in E1 writes it to disk, a database, or any other durable store, and nothing catches a provider's raised exception and turns it into a `FAILED`-status record — both providers raise a typed `chronicle.ai.models.errors.*` exception on failure instead of returning one. Concretely:

- `status`, `errorType`, `errorMessage` exist as fields on the contract and are exercised by validation, but no code path in E1 ever sets `status=FAILED` or populates `errorType`/`errorMessage` — there is no failure-persisting code yet, because there is no runner to call it.
- `AgentRunRecord`/`AgentRunStatus` (`orchestration/run_models.py`, `orchestration/statuses.py`) are the same story one level up: a validated shape, unit-tested for construction and rejection (`backend/tests/ai/orchestration/test_run_models.py`), but never constructed by anything outside those tests. No file is written; no run has ever actually happened.
- Turning both of these from "contract exists" into "failures and runs are actually recorded" is E3/E4 work — the dynamic agent runner is what will catch a provider's exception, build the `FAILED` `ModelCallRecord`, attach it to a real `AgentRunRecord`, and persist that record somewhere (most likely a file-based store mirroring `workflow/storage/run_store.py`'s existing pattern, per ADR-003, though the exact persistence mechanism is not yet decided).

## Cost recording

`ModelCallRecord.cost` (a `ProviderCost { amountUsd, basis }`, `models/metadata.py`) records **provider-billed inference cost only** — what the model provider charged for this specific call. It deliberately does not attempt to measure electricity, hardware amortization, or developer time; those are real costs of running inference on this machine, just not what this field is for.

Both providers currently in this codebase record `amountUsd=0.0` with `basis=CostBasis.NO_PROVIDER_CHARGE` on every successful call: `DeterministicModelProvider` makes no network call at all, and `OllamaModelProvider` talks to a local daemon with no billing relationship — there is no provider to invoice, so `0` is the accurate value, not a placeholder for "unknown." A future hosted provider (not in scope for Phase E, see ADR-003's alternatives-considered) would report a real amount under `basis=CostBasis.PROVIDER_BILLED` instead, without any change to `ModelCallRecord`'s shape.

Restated because it is easy to misread a `$0` cost field as "this is free to run": local inference on this hardware still costs real wall-clock time (`latencyMs`, already recorded and disclosed as slow — see the hardware audit above) and real electricity/hardware wear. `cost` does not measure either of those, on purpose — it answers one narrow question (did a provider bill Chronicle for this call), not "what did this call cost in any broader sense."
