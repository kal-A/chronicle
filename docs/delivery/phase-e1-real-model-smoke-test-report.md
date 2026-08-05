# Phase E1 Real-Model Smoke Test Report

Records the one real Ollama call this project has ever made, run once during Phase E1 closeout (2026-08-05) after Kamal's explicit, separate approval to install Ollama, download `qwen2.5:7b-instruct`, and run exactly the minimal smoke test defined in `docs/delivery/claude-chat-handoff-phase-e1.md` §13. See `docs/ai/learning-log.md`'s matching dated entry for the lesson-oriented version of the same result.

## What this proves, and what it does not

**Proven by this test:**
- `OllamaModelProvider`'s wiring is correct end to end against a real, locally running Ollama daemon — request construction, JSON-schema submission, response parsing, Pydantic validation, `ModelCallRecord` construction (including the cost field added at closeout) all work against real Ollama output, not just `httpx.MockTransport`.

**Not proven by this test, on purpose (per the handoff's explicit scope limit):**
- Whether any of the four future agents (Planner/Analyst/Critic/Guide) will work — none exist yet.
- Whether the retry-with-feedback mechanism actually helps a real model self-correct — the model didn't need it this time.
- Whether a complex, deeply nested schema (e.g. `AnalysisDraft`, `CriticDecision`) produces reliable structured output — this test used a deliberately trivial 3-field schema.
- Historical reasoning, tool calling, or citation grounding of any kind.
- Behavior under sustained or repeated load, or with multiple concurrent requests.
- Phase E2 (corpus tools) — not started.

## Installation

| | |
|---|---|
| Method | `winget install --id Ollama.Ollama --scope user --accept-package-agreements --accept-source-agreements` |
| Ollama version | 0.32.5 |
| Installer source | `https://github.com/ollama/ollama/releases/download/v0.32.5/OllamaSetup.exe` (verified installer hash by winget) |
| Install scope | User-level, no admin elevation |
| Binary path | `C:\Users\naeema\AppData\Local\Programs\Ollama\ollama.exe` |
| Startup registration | Yes — `Ollama.lnk` added to the user Startup folder; launches on login |
| Bind address | `127.0.0.1:11434` only (confirmed via `Get-NetTCPConnection`) — not exposed to LAN/internet |
| Firewall rules added | None (checked; none found) |
| Firewall rules changed by this work | None |

## Model pulled

| | |
|---|---|
| Command | `ollama pull qwen2.5:7b-instruct` |
| Identifier | `qwen2.5:7b-instruct` |
| Digest | `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e` |
| Size on disk | 4,683,087,332 bytes (~4.7 GB decimal, ~4.36 GiB) |
| Parameters (Ollama-reported) | 7.6B |
| Quantization (Ollama-reported) | Q4_K_M — matches `docs/ai/model-provider-decisions.md`'s prediction |
| Context length (Ollama-reported) | 32768 tokens — the model's architectural maximum, not a claim about what's safely usable on this machine's RAM; unrelated to and not confirming/refuting the docs' separate "~8K practical" estimate |
| Embedding length (Ollama-reported) | 3584 |
| Capabilities (Ollama-reported) | `completion`, `tools` |
| Only model pulled | Yes — no 3B fallback, no Llama, no embedding model, no additional quantization |
| Disk free after pull (C:) | ~724 GB |

## Hardware at time of test

Unchanged from the original E1 audit: AMD Ryzen 5 6600H (6 cores/12 threads), 13.69 GB total RAM, integrated AMD Radeon graphics (no dedicated VRAM, no realistic Ollama GPU acceleration on Windows) — CPU-only inference, confirmed again, not re-assumed.

Free RAM was noticeably tighter than the original audit's snapshot at points during this session (as low as ~0.97 GB at one recheck, ~1.56 GB immediately before the smoke test, ~1.63 GB immediately after) — normal fluctuation from this session's own dev processes, not a hardware change. See "Memory observations" below for what was and wasn't actually measured during the call itself.

## The test

`backend/tests/ai/integration/test_ollama_smoke.py::test_real_ollama_structured_generation`, invoked explicitly with `pytest -m local_ollama_integration -s` (excluded from the default suite via `backend/pyproject.toml`'s `addopts`).

- **Schema:** `SmokeTestResponse { label: str, count: int, confirmed: bool }` — trivial, on purpose.
- **Prompt:** historically neutral ("Return a small structured object proving that the local model can follow a JSON schema...") — no Concert of Europe, Troppau, Laibach, Naples, or any benchmark-specific content, per instruction.
- **Prompt version:** `e1-smoke-v1`.
- **Temperature:** 0.0.

## Result

| | |
|---|---|
| Attempts | **1** — the model produced valid, schema-matching JSON on the first try; the bounded retry-with-feedback path was never exercised |
| Response value | `{'label': 'ready', 'count': 3, 'confirmed': True}` — exactly as requested |
| Validation | Passed, first try, no manual repair, no schema weakening |
| Latency (provider-measured, `ModelCallRecord.latencyMs`) | 20,954.2 ms (~21.0 s) |
| Wall-clock (test-measured) | 21.00 s |
| Usage (Ollama-reported) | `promptTokens=70`, `completionTokens=18` |
| Cost | `amountUsd=0.0`, `basis=NO_PROVIDER_CHARGE` |
| Errors | None |

## Memory observations

An attempt was made to sample RAM continuously during the call (a background `Start-Job` loop), but it produced zero samples — the job did not survive between separate tool invocations in this environment. This is a tooling gap in how the measurement was attempted, disclosed rather than papered over with an invented peak number.

What is actually known:
- Free RAM immediately before the call: ~1.56 GB. Immediately after: ~1.63 GB. Stable, not depleted.
- The Ollama daemon's working set was ~118 MB (combined `ollama`/`ollama app` processes) idle before the call, and ~29 MB after — the model did not remain resident in memory after the call completed.
- `Get-WinEvent` against `Microsoft-Windows-Resource-Exhaustion-Detector` (confirmed present on this system) returned zero events across the entire install+pull+test window (~20 minutes).
- The call completed in a normal ~21 s window with no hang, no timeout, no crash.

Together this is reasonable evidence against severe or sustained memory pressure during this one call — but it is not a measured peak-RAM number during model load/inference, which a future, more carefully instrumented run should capture properly (e.g. a monitor that logs from within the same long-running process rather than a separately-launched job).

## Practical usability assessment

For **one interactive, trivial structured-output call**, `qwen2.5:7b-instruct` on this hardware is practically usable: ~21 seconds is slow next to a hosted API but compatible with this project's own bounded, sequential (no-parallel-agents) design. This does not extend to complex nested agent contracts, sustained/repeated calls, or multi-agent sequencing (Planner → Analyst → Critic → Guide, each a separate call) — those remain untested and materially riskier for both latency (four sequential ~20s+ calls per question) and structured-output reliability on harder schemas.

## Recommendation

Keep `qwen2.5:7b-instruct` as the working model for E3+ development; there is no result here that argues for switching to the 3B fallback, and no separate 3B test was run (not approved, not needed — the 7B model succeeded cleanly). Revisit if E3/E4's actual agent contracts show structured-output failures the 3B model wouldn't meaningfully help with anyway, or if per-call latency across a real four-agent sequence proves impractical for interactive use.

## Explicitly not started

Phase E2 (corpus service, typed retrieval tools) and everything after it. This report and its underlying test change nothing about that — see `docs/delivery/phase-e-ai-core-plan.md` for the sub-plan tracker.
