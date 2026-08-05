# Claude Chat Handoff — Phase E1 Closeout

**Written:** 2026-08-05, by the Claude Code session that implemented Phase E1, because that session's context had grown too large to safely continue in. Everything below was verified directly against the repository (`git status`, `git log`, `pytest`, `npm run typecheck/lint`, `npx vitest run`, `npm run build`, `npm run test:e2e`) at write time — not copied from prior chat memory. If anything here conflicts with what you observe in a fresh check, trust your own observation and flag the discrepancy; this document can be stale by the time you read it.

This document is self-contained. You do not have access to the chat history that produced it.

---

## 1. Project purpose

Chronicle's primary objective is **not** "build a historical investigation viewer about the Concert of Europe." It is:

- Building a **domain-specialized LLM system**: a small, bounded, tool-using multi-agent architecture that answers real historical questions with cited, verified evidence and typed map actions.
- Learning and implementing **multiple bounded AI agents** — currently four: Investigation Planner, Evidence Analyst, Historical Critic, Investigation Guide (none exist yet — see §7).
- Using **history as the domain and evaluation context**, not the end product. The Concert of Europe and Blank Cheque investigations are benchmark corpora the agent system is developed and measured against.
- Using **the map** (`InvestigationWorkspace`, lenses, `MapView`/`GraphView`) as the primary interaction surface for a user asking a question.
- Using **Inspector** (the preserved article-first narrative/timeline/map/graph/evidence renderer) as the evidence and trust surface — where a user can independently verify what the agent claims.

This reorientation is recorded in `docs/decisions/ADR-003-llm-agent-system-is-product-core.md` (accepted 2026-08-05). Before ADR-003, Chronicle was drifting toward "a well-built historical content viewer with a placeholder assistant." ADR-003 corrects that: **the AI-agent system is the product focal point.** The historical UI, the generated-investigation contract, the deterministic Python pipeline, and the curated Concert of Europe content are all infrastructure *for* the AI system — not the deliverable themselves. A frontend freeze is in effect (no new investigations, no new lenses without an AI consumer, no more hand-authored provider sets) until the AI core (Phase E) lands.

---

## 2. Authoritative reading order

Read in this order before doing anything else:

1. **`AGENTS.md`** (repo root) — canonical product purpose, historical-integrity rules, architecture boundaries, cost constraints (§5 — no paid infrastructure), testing/security requirements (§6 — deterministic tests, no live network in ordinary tests), git restrictions (§9 — never commit/push without per-instance approval), definition of done.
2. **`CLAUDE.md`** (repo root) — Claude-specific workflow rules layered on top of `AGENTS.md`: plan mode before substantial multi-file changes, read docs before editing, state assumptions explicitly, smallest complete vertical slice, update delivery docs after each slice.
3. **`plans/current-phase.md`** — the live, detailed, chronological status log of every sub-plan across Phases B through E1, each with its own "Built" / "Explicitly not in X" / "Verification" / "No commit, no push" sections. This is the single most information-dense document in the repo for understanding *how* the project got here. Read at least from "## Completed: Phase E0" (near the end) onward; skim earlier sections for pattern/precedent.
4. **`docs/delivery/revised-development-phases.md`** — the current roadmap (Phase A through Phase K). Phase E is "Real LLM Agent Core," sequenced E0-E9.
5. **`docs/ai-core-instructions/00_START_HERE.md` through `06_CLAUDE_CODE_EXECUTION_INSTRUCTIONS.md`** — the six-document instruction set Kamal supplied that triggered ADR-003. These are the frozen source of truth for the AI-core direction (four-agent architecture, retrieval/tool design, domain-generalization requirements, the Phase E implementation plan, execution instructions). Read all six; they are not superseded by anything except explicit later approval from Kamal.
6. **`docs/decisions/ADR-003-llm-agent-system-is-product-core.md`** — the decision record: why the pivot, the two conflicts it resolved (cost-constraint compliance via Ollama; the Phase E-L → E-K roadmap replacement), what's absorbed where, explicit exclusions.
7. **`docs/ai/agent-architecture.md`** — the living, code-adjacent restatement of the four-agent contracts, current status (only the provider layer exists), and why agent orchestration is a separate module from the existing package-generation engine.
8. **`docs/ai/model-provider-decisions.md`** — the Ollama-first rationale, the full hardware audit, the model comparison table, known limitations, the path to a future fine-tuned model.
9. **`docs/ai/learning-log.md`** — dated, additive lessons (currently one entry, Phase E1's).
10. **`docs/architecture/generated-investigation-contract.md`** — the `GeneratedInvestigation` package contract the AI system's tools (E2) will read from and the Guide agent's answers must cite into.
11. **`backend/src/chronicle/contracts/experience_plan.py`** / **`src/features/investigation/model/experiencePlan.ts`** — the `InvestigationExperiencePlan` contract (lenses, story sequences, system paths) — no dedicated architecture doc exists for this; the contract source files and `docs/product/map-first-workspace-instructions.md` are authoritative.
12. **`docs/product/map-first-workspace-instructions.md`** — the map-first workspace source instructions, including §15's `AssistantAction` type (already fully specified, unchanged by E1) and §17.1's accessible-equivalent requirement.
13. **`docs/architecture/provenance-and-review.md`** — read with the caveat already flagged inside it (and in ADR-003 Consequences): it describes a Postgres/pgvector/human-review "Studio" system that **does not exist**. Only file-based, no-database persistence exists today (`RunStore`). E2's corpus service will query the already-generated `GeneratedInvestigation` package's own embedded records, not a database.
14. **`docs/delivery/phase-e-ai-core-plan.md`** — the E0-E9 sub-plan tracker table (stable index; `plans/current-phase.md` has the live detail).
15. **This document's own §5** is the closest thing to a "Phase E1 implementation report" — no separate report file exists; the full write-up lives in `plans/current-phase.md` under "## Completed: Phase E1 — Model Provider Foundation" (lines 267-293 as of this writing).

---

## 3. Repository and Git state (verified 2026-08-05, this session)

```
Current branch:        phase-e-ai-core
Branch base:            43d2b94 (created from phase-c-python-foundation at that commit)
phase-e-ai-core upstream: NONE — this branch has never been pushed to origin
```

**Commit history (`git log --oneline`, all branches):**

| Commit | Message | Pushed? |
|---|---|---|
| `1ee3541` | Initial commit: Chronicle historical investigation viewer | Yes — `origin/master` |
| `89a130d` | Phase C0-C3: Python deterministic-generation backend + real curated package | Yes — on `origin/phase-c-python-foundation` |
| `b0380e2` | Phase D0.1-D0.6: map-first investigation workspace | Yes — on `origin/phase-c-python-foundation` |
| `43d2b94` | Phase E0: reorient toward the LLM-agent-system-is-product-core correction | Yes — on `origin/phase-c-python-foundation`, and this is also `phase-e-ai-core`'s branch point |

`git branch -vv` confirms: `phase-c-python-foundation` tracks `origin/phase-c-python-foundation` at `43d2b94`, exactly matching local HEAD (nothing to push on that branch). `phase-e-ai-core` has no `[origin/...]` marker — it is a local-only branch, not yet pushed to the remote at all (this includes the branch itself, separate from whether E1's commit exists on it — no commit has been made on it either, see below).

**Working tree status (`git status --porcelain`):**

```
 M backend/pyproject.toml
 M plans/current-phase.md
?? .env.example
?? backend/src/chronicle/ai/
?? backend/tests/ai/
?? docs/ai/
?? docs/delivery/phase-e-ai-core-plan.md
```

- **Nothing is staged** (`git diff --cached --stat` is empty).
- **No unrelated changes** — every modified/untracked path is Phase E1 work. `backend/pyproject.toml`'s only diff is adding `"httpx>=0.27",` to `dependencies`. `plans/current-phase.md`'s diff is +35/-5 lines (the Phase E1 write-up).
- **What must not be lost:** all of it. This is the entire, complete, tested Phase E1 slice — the `ai/` package, its tests, four new docs, and the delivery-doc updates. None of it is committed anywhere. If this working tree is discarded, Phase E1 has to be rebuilt from scratch.

**Do not commit or push any of this without Kamal's separate, explicit approval** — this was an explicit standing instruction for E1 specifically, restated in `plans/current-phase.md`'s own E1 write-up ("No commit, no push of E1 — awaiting your separate explicit approval").

---

## 4. Completed work through Phase E0

Summarized only to the depth needed to understand current architecture — full detail is in `plans/current-phase.md`.

- **`GeneratedInvestigation` contract** (Phase B/C0): a versioned Zod (TS) / Pydantic (Python) package contract — entities, events, claims, relationships, sources, documents, passages, evidence links, a claim ledger, a generation report. Field-for-field parity between the two languages, proven by shared invalid fixtures both languages reject identically.
- **Python/TypeScript parity**: `backend/src/chronicle/contracts/` mirrors `src/features/investigation/model/generatedInvestigation.ts` exactly, including the same 20+ imperative cross-record validation rules (`validation.py` ↔ `generatedInvestigation.ts`'s `validateGeneratedInvestigation()`).
- **Resumable deterministic package-generation engine** (Phase C1): `backend/src/chronicle/workflow/engine.py`'s `generate()`/`resume()`/`run_pipeline()` drives a fixed, linear 8-stage pipeline (`SCOPE_PROPOSED → ... → VERIFIED`), with file-based `RunStore` persistence (`backend/runs/<run-id>/...`, gitignored), hash-based reuse-vs-rerun per stage, and a CLI (`chronicle generate/resume/inspect/validate`).
- **Curated and mock providers** (Phase C2/C3): `providers/mock/` — 9 deterministic, topic-agnostic, disclosed-synthetic providers proving the pipeline works for any topic. `providers/curated/concert_of_europe/` — a second, real, hand-researched investigation ("The Concert of Europe and Revolutionary Intervention, 1814-1822") plugged into the same 8-stage engine contract, with real sourced documents, a genuinely disputed relationship (with counterevidence), and honestly disclosed gaps (no Verona primary source, no period map for the intervention scene).
- **Map-first workspace** (Phase D0.1-D0.6): `src/features/investigation/workspace/` — a persistent bounded map/graph canvas driven by `InvestigationExperiencePlan` "lenses," a docked (desktop, resizable/collapsible)/bottom-sheet (mobile) assistant panel with Ask/Explore/Evidence/Sources tabs.
- **Persistent assistant-panel shell**: `AskTab.tsx` inside the docked panel is a **disclosed placeholder** — it does not call any model. It stays exactly as-is until Phase E6.
- **Inspector**: `src/features/investigation/inspector/InspectorView.tsx` — the original article-first narrative/timeline/map/graph/evidence renderer, preserved unchanged, reachable at `/investigations/:packageId/scenes/:sceneId/inspector`. This is the evidence/trust surface referenced in §1.
- **Experience Plan**: `InvestigationExperiencePlan` (`experiencePlan.ts` / `experience_plan.py`) — optional/additive on `GeneratedInvestigation`. Defines lenses, story sequences, system paths (labelled-graph relationship views), perspective comparisons, and disclosed limitations. Generated by the curated Python pipeline for Concert of Europe (D0.4); hand-authored for Blank Cheque (no generation pipeline behind that package).
- **Ask entry prototype** (D0.5): `/` is now a keyword-match entry surface (`src/features/investigation/ask/topicMatch.ts`) against the two existing investigations — explicitly **not** live generation. An honest "not available in this prototype" message on no match. This is disclosed prototype behavior, not the real Planner/Guide pipeline E3-E6 will build.
- **Benchmark fixtures**: `fixtures/blank-cheque.golden-investigation.json` (hand-migrated original prototype content) and `fixtures/concert-of-europe.generated-investigation.json` (frozen curated-pipeline output, byte-identical across independent generations). These two packages are the only "corpora" that exist right now — see §8's generalization warning.
- **Roadmap reorientation** (E0): checkpoint-committed all of the above (`89a130d`, `b0380e2`), added the six `docs/ai-core-instructions/` documents, wrote ADR-003, replaced the roadmap's Phase E-L section with the new Phase E-K sequence, fixed cascading stale phase-letter references across several architecture docs, and flagged `provenance-and-review.md`'s aspirational database description.

**Which components are AI-system infrastructure, concretely:** the `GeneratedInvestigation` package *is* the retrieval corpus E2's tools will query; its schema *is* the structured-output contract the Guide agent must conform citations to; the map-first workspace *is* the interaction surface typed `AssistantAction`s will drive; the Inspector *is* the independent-verification surface a user falls back to; the deterministic Python pipeline's patterns (file-based `RunRecord`/`StageRecord` persistence, hash-based dedup) *are* the template E1's `ai/orchestration/` scaffolding reused — but not its code path (see §7).

---

## 5. Phase E1 implementation status — COMPLETE, UNCOMMITTED

Phase E1 ("Model Provider Foundation") built the provider-agnostic model layer the four future agents will call. **No agent exists yet.** This is foundation only.

### What was built

**`ModelProvider` protocol** (`backend/src/chronicle/ai/models/protocol.py`): a `@runtime_checkable`, synchronous `typing.Protocol` (not a base class):
```python
class ModelProvider(Protocol):
    def generate_structured(self, *, system_prompt, user_prompt, response_model: type[T],
                             prompt_version: str, temperature: float = 0.0) -> StructuredGenerationResult[T]: ...
    def generate_text_from_verified_records(self, *, system_prompt, user_prompt, prompt_version) -> TextGenerationResult: ...
    def health_check(self) -> ProviderHealth: ...
    @property
    def provider_metadata(self) -> ProviderMetadata: ...
```
Synchronous throughout, matching 100% of the existing codebase (async deferred to E5's FastAPI layer, which can run a sync call in a threadpool — a deliberate sequencing choice, not a gap).

**`DeterministicModelProvider`** (`ai/models/deterministic.py`): zero network calls, a FIFO-scripted queue (`enqueue_value`, `enqueue_text`, `enqueue_malformed`, `enqueue_schema_invalid`, `enqueue_error`) so every future agent's tests can run with no live inference dependency (`AGENTS.md` §6).

**`OllamaModelProvider`** (`ai/models/ollama.py`): talks to a local Ollama daemon over `httpx`. Sends `response_model.model_json_schema()` as Ollama's `format` parameter (schema-constrained generation), validates the response through Pydantic again as a second gate. On malformed JSON or schema-invalid output: retries once with the validation error appended to the message list as concise feedback, then raises `RetryExhaustedError` honestly (`__cause__` set to the underlying error) rather than looping. Base URL from `CHRONICLE_OLLAMA_BASE_URL` env var (`resolve_base_url_from_env()`), defaulting to `http://localhost:11434`. No agent-specific business logic lives here — it only knows how to talk to Ollama and enforce a schema.

**Structured Pydantic/JSON-schema output**: both providers return `StructuredGenerationResult[T]` (`ai/contracts/structured_generation.py`), a plain generic `dataclass` (not Pydantic — it's an in-process return value, never serialized) wrapping the validated `T` plus a `ModelCallRecord`.

**Retry-with-validation-feedback**: `ai/orchestration/policies.py` — `MAX_STRUCTURED_OUTPUT_ATTEMPTS = 2`, and a named `RETRYABLE_ERROR_TYPES` tuple: `(MalformedOutputError, SchemaValidationError, ProviderTimeoutError, RateLimitError)`. Both providers import and use the same constants, so retry behavior is consistent and independently testable rather than each provider inventing its own rule.

**Error taxonomy** (`ai/models/errors.py`) — a `ModelProviderError` base with explicit subclasses, every one of them actually raised somewhere in the two providers, never a bare `Exception`:
`ProviderUnavailableError`, `ModelUnavailableError`, `ProviderTimeoutError`, `RateLimitError`, `MalformedOutputError`, `SchemaValidationError`, `RetryExhaustedError`, `InvalidConfigurationError`, `UnsupportedCapabilityError`, `RequestCancelledError`.

**Provider/model/prompt metadata, latency, usage** (`ai/models/metadata.py`): `ModelCallRecord` (deliberately shaped like `workflow/state.py`'s existing `StageRecord` — same `attemptCount`/`startedAt`/`completedAt`/`errorType`/`errorMessage` fields) records `providerName`, `providerVersion`, `modelName`, `modelVersion`, `promptVersion`, `status`, `attemptCount`, `startedAt`/`completedAt`, `latencyMs`, `usage: TokenUsage | None` (never fabricated — `None` when Ollama's response doesn't report token counts), `errorType`/`errorMessage`. `ProviderMetadata` and `ProviderHealth` round out provider-level capability/health reporting.

**Health checks**: `OllamaModelProvider.health_check()` GETs `/api/tags`; `DeterministicModelProvider.health_check()` always reports healthy.

**Dynamic agent-run persistence scaffold** (`ai/orchestration/{statuses,run_models}.py`): `AgentRunStatus` (created/running/ready/partial/abstained/failed — same shape as `workflow/stages.py`'s `RunStatus`), `AgentRunRecord` (question, `investigationPackageId`, `sceneId`, status, a list of `ModelCallRecord`s, warnings, abstention reason). **Scaffolded only — no runner exists.** Nothing constructs, drives, or persists an `AgentRunRecord` yet.

**Separation from the fixed package-generation engine**: this is the load-bearing architectural decision of E1 — see §7.

### Tests added

`backend/tests/ai/models/`:
- `test_deterministic.py` — 11 tests: valid generation, every configured failure mode, retry-then-succeed, retry exhaustion, text generation, health check, metadata.
- `test_ollama.py` — 19 tests, **all** via `httpx.MockTransport` (zero real network calls, confirmed by grep in this session — see §9): request construction (JSON schema present), valid/malformed/schema-invalid responses, retry-after-invalid-output (asserts the retried request's messages contain the feedback), retry exhaustion, connection-refused → `ProviderUnavailableError` not retried, 404 → `ModelUnavailableError` not retried, timeout retried and can succeed, timeout exhaustion, 429 → `RateLimitError` retried, **500 → `ProviderUnavailableError` not retried** (see §10's bug), health check healthy/unhealthy, text generation sends no `format` field, invalid base URL/empty model rejected at construction, metadata reports local/no-API-key.
- `test_protocol_compliance.py` — 4 tests: both providers satisfy `ModelProvider` via structural `isinstance()`; env-var base-URL default and override.

**33 new tests total.** Combined with the pre-existing 76, backend is at **109 passed** (verified this session — see §9).

### Documentation added

- `docs/ai/model-provider-decisions.md` (new)
- `docs/ai/agent-architecture.md` (new)
- `docs/ai/learning-log.md` (new, one dated entry)
- `docs/delivery/phase-e-ai-core-plan.md` (new — E0-E9 tracker)
- `plans/current-phase.md` (updated — full E1 write-up appended, lines 267-293)

### Main files created (all currently untracked)

```
backend/src/chronicle/ai/__init__.py
backend/src/chronicle/ai/models/{__init__,protocol,deterministic,ollama,metadata,errors}.py
backend/src/chronicle/ai/orchestration/{__init__,statuses,run_models,policies}.py
backend/src/chronicle/ai/contracts/{__init__,structured_generation}.py
backend/tests/ai/__init__.py
backend/tests/ai/models/{__init__,test_deterministic,test_ollama,test_protocol_compliance}.py
docs/ai/{model-provider-decisions,agent-architecture,learning-log}.md
docs/delivery/phase-e-ai-core-plan.md
.env.example
```

### Main files modified

```
backend/pyproject.toml     (+1 line: "httpx>=0.27" dependency)
plans/current-phase.md     (+35/-5 lines: Phase E1 write-up)
```

---

## 6. Hardware and local-model decision (verified at E1 planning time, 2026-08-05)

| | |
|---|---|
| OS | Windows 11 Home 64-bit, build 26200 |
| CPU | AMD Ryzen 5 6600H, 6 cores / 12 logical processors |
| RAM | **13.69 GB total** (1.59 GB free at audit moment — a heavy dev session; expect more free with fewer apps open) |
| GPU | AMD Radeon integrated graphics (iGPU) — **no dedicated VRAM**, shares system RAM |
| Acceleration | **None expected** — ROCm's Windows/consumer-APU support does not cover this hardware class; inference is CPU-only |
| Disk | 534.83 GB free on `D:` |
| Ollama installed | **No** — confirmed twice this project (not on PATH; `curl http://localhost:11434/api/tags` refused/timed out both times, most recently this session) |

This is a real, load-bearing constraint, not a formality: 13.69 GB shared with OS/IDE/browser/Node dev servers realistically leaves ~6-8 GB for a model, ruling out anything meaningfully above 7-8B parameters at Q4 quantization — and even that runs CPU-only (a few tokens/second, not hosted-API speed).

**Approved model direction:**
- **Ollama-first** — local, open-weight, satisfies `AGENTS.md` §5's "no paid infrastructure" constraint exactly as written; no cost exception requested or needed.
- **Provider-agnostic** — `ModelProvider` is a structural `Protocol`; a future hosted provider or fine-tuned Chronicle model can be added without touching `protocol.py` or any agent.
- **Deterministic-testable** — every agent (E3+) gets a `DeterministicModelProvider` test double; `OllamaModelProvider`'s own tests use `httpx.MockTransport` exclusively.

**Currently proposed/configured models** (in `backend/src/chronicle/ai/models/ollama.py`):
- **Primary: `qwen2.5:7b-instruct`** (`DEFAULT_MODEL` constant) — Q4_K_M, ~4.7 GB on disk. Chosen for strongest available structured-output/JSON-schema reliability at a size this hardware can run. Intended reused sequentially across all four future agent roles (one model, four prompts — not four concurrently-loaded models, which this hardware cannot hold).
- **Fallback: `qwen2.5:3b-instruct`** — ~1.9 GB, switchable via `OllamaModelProvider(model=...)` with no code change. Documented for the Investigation Guide role (least reasoning-demanding — reformats already-critic-approved material) or fast local iteration.
- **Comparison point, not selected: `llama3.1:8b-instruct`** — documented in `docs/ai/model-provider-decisions.md` for E7's future evaluation-methodology comparison, not an initial pick.

**State, stated plainly:**
- **No model has been downloaded.**
- **Ollama has not been installed.**
- **Installing Ollama and downloading any model both require Kamal's separate, explicit approval** — not implied by the model comparison having been presented and implicitly accepted via plan approval.
- **Automated tests must never require Ollama or live network access.** This is currently true (verified — see §9) and must stay true as E2+ lands: any new test touching `OllamaModelProvider` must use `httpx.MockTransport` or an equivalent mock.

---

## 7. Important architectural decisions (do not silently relitigate these)

- **The existing package-generation workflow (`backend/src/chronicle/workflow/engine.py`, `run_pipeline()`) remains separate and untouched.** It is shaped for one fixed, linear 8-`StageName` sequence that produces a *new* `GeneratedInvestigation` package. This is the right shape for `chronicle generate <topic>`. It is the **wrong** shape for an interactive agent run.
- **Interactive question-answering agents use a new, sibling `chronicle.ai.orchestration` module**, not `engine.py`. An agent run *answers a question against a package that already exists* via a dynamic, bounded tool-calling loop (question → planner → dynamic tool calls → analyst → critic → bounded retrieval loop → guide) — a genuinely different control-flow shape than a fixed pipeline. `ai/orchestration/` reuses `engine.py`'s *patterns* (file-based `RunRecord`/`StageRecord`-shaped persistence, `createdAt`/`updatedAt`/`touch()`, hash-based dedup idioms) as a sibling module — not its literal `StageName` enum or `run_pipeline()` code path. This was a genuine audit finding during E0, not an assumption — recorded in ADR-003's Consequences and restated in `docs/ai/agent-architecture.md`.
- **The first four agents will be**, in this order of implementation (E3 then E4):
  1. **Investigation Planner** — converts a question + workspace context into a typed `InvestigationPlan` (contract not yet defined — E3 work).
  2. **Evidence Analyst** — builds a structured `AnalysisDraft` from retrieved evidence (contract not yet defined — E3 work).
  3. **Historical Critic** — produces a `CriticDecision` (approve/downgrade/reject/abstain) challenging the Analyst's draft (contract not yet defined — E4 work).
  4. **Investigation Guide** — turns critic-approved material into a user-facing `AgentAnswer` with citations and typed `AssistantAction`s (`AssistantAction` itself **is already fully specified**, `docs/product/map-first-workspace-instructions.md` §15, unchanged by any of this work).
- **Retrieval tools remain deterministic typed software** (E2), not LLM calls — `search_passages`, `get_claim_evidence`, etc., are plain Python functions over the existing `GeneratedInvestigation` package's embedded fields, no database.
- **One local model may be reused sequentially across all four agent roles** — a stated assumption (documented in `docs/ai/model-provider-decisions.md` and flagged again in `docs/ai/learning-log.md`), not yet a measured result. E7's evaluation should check whether this holds.
- **Agents must use structured outputs** — every agent role calls `generate_structured()` with a typed Pydantic `response_model`, never freeform text parsing for anything that drives an application decision.
- **Loops must be bounded** — `MAX_STRUCTURED_OUTPUT_ATTEMPTS = 2` at the provider layer; the future Critic/retrieval loop (E4) must have its own explicit bound, not an open-ended agent loop (`AGENTS.md` §4's "no autonomous agent swarms" binds here).
- **Private chain-of-thought must not be stored.** No component built so far stores or persists a model's raw reasoning trace — `ModelCallRecord` stores metadata (provider/model/prompt version, timestamps, latency, usage, error info), never the model's internal reasoning. Keep it that way in E3+.
- **Answers require valid evidence references** — the future Guide agent's `AgentAnswer` must cite into the existing package's real Source/Passage/Claim records; this is what E7's evaluation will measure (citation validity).
- **Map actions must be typed and validated** — `AssistantAction` (already specified) is the contract; no free-form map manipulation from agent output.
- **No topic-specific branching is permitted anywhere** — see §8.

---

## 8. Concert of Europe generalization warning

**Concert of Europe is one benchmark corpus, not a product feature to keep expanding.** Alongside Blank Cheque, it is currently the *only* corpus that exists — this is a real risk the project has been explicit about since ADR-003.

Safeguards already decided and currently upheld (verify these still hold before adding anything):
- **History topics are benchmark corpora, not providers.** Nothing in `chronicle.ai.*` should be written to know it's "about" the Concert of Europe or the Congress of Vienna specifically.
- **No `if topic == ...` application branching** anywhere in the Python backend or the AI orchestration layer.
- **No investigation-ID branching in React** — `InvestigationWorkspace`, `AskEntryPage`, etc. must stay generic over whatever package/scene ID they're given, exactly as the existing generic-renderer discipline from Phase B/C already established (verified by Phase B/C's "hard-coding acceptance search" precedent — worth repeating for any new AI-facing frontend code in E6).
- **Prompts must not be dominated by Troppau/Laibach/Concert examples.** When E3 writes the Planner/Analyst prompts, few-shot examples (if any) should not lean disproportionately on Concert of Europe content, or the model will silently overfit to that corpus's shape.
- **Agent tests must become cross-corpus.** E2's corpus-service tools must be tested against *both* existing packages (blank-cheque, concert-of-europe) from day one — this is already planned in `docs/delivery/phase-e-ai-core-plan.md`'s E2 scope description, not deferred.
- **At least one materially different corpus must be added** before Phase E can be considered complete (Phase E8, "domain generalization"). Not started.
- **One corpus should eventually be held out** from prompt/example authoring specifically to test generalization, per `docs/ai-core-instructions/04_DOMAIN_GENERALIZATION_AND_EVALUATION.md`.
- **No single topic should dominate evaluation or training data.** This becomes directly relevant once E7's evaluation harness and (much later) Phase I's fine-tuning dataset exist.

**Phase gate, stated verbatim in `docs/delivery/phase-e-ai-core-plan.md`:** *"Phase E does not pass on one corpus or one question working."* Required before Phase E is considered complete: real agent workflow operates across at least two materially different corpora; unsupported questions abstain; citation validity is measured; map actions validate; no topic-specific application branching exists; agent workflow is compared against single-prompt and basic-RAG baselines; results and lessons are documented.

---

## 9. Verification state (all commands re-run and confirmed this session, 2026-08-05)

| Check | Command | Result |
|---|---|---|
| Backend tests | `cd backend && .venv/Scripts/python.exe -m pytest -q` | **109 passed** (76 pre-existing + 33 new in `tests/ai/`) |
| Frontend typecheck | `npm run typecheck` | Clean, no errors |
| Frontend lint | `npm run lint` (oxlint) | Clean, no errors |
| Frontend unit tests | `npx vitest run` | **101 passed** (13 test files) — known, pre-existing `HTMLCanvasElement.getContext()` jsdom warnings only (MapLibre in jsdom; not a regression) |
| Frontend build | `npm run build` | Succeeds — known pre-existing chunk-size advisory for the MapLibre bundle (not new) |
| End-to-end tests | `npm run test:e2e` (Playwright) | **14 passed** across `concert-of-europe-journey`, `ask-entry-journey`, `gate1-journey`, `keyboard-navigation`, `workspace-journey`, `investigation.spec.ts` |
| No live network in AI tests | `grep -rn "localhost:11434\|http://\|https://" backend/tests/ai/` | Every match is either a fake/mock URL (`http://fake-ollama:11434`, `http://fake:11434`) passed alongside an explicit mock `client=`, an env-var-override assertion, or a construction-time validation test that raises `InvalidConfigurationError` **before** any client is used (`test_empty_model_name_is_rejected_at_construction`, which passes a real-looking `localhost:11434` URL but never reaches the network — confirmed by reading the test). **No test in this repository makes a real network call.** |
| Ollama reachability | `where ollama` / `curl http://localhost:11434/api/tags` | Not on PATH; connection refused/timed out — **confirmed not installed/running** |

**Known warnings, not regressions:** jsdom's `Not implemented: HTMLCanvasElement's getContext()` (MapLibre rendering in a non-browser test environment — pre-existing, harmless, accessible fallbacks are what's actually being tested); Vite's "chunks larger than 500 kB" build advisory (pre-existing, MapLibre + Cytoscape bundle size, not related to E1).

---

## 10. Known bugs, risks, and lessons

- **The retry-eligibility bug, found and corrected during E1's own test-writing (not shipped):** an early draft mapped HTTP 5xx to `ProviderUnavailableError` but had inconsistent test expectations about whether it should retry. Resolved: HTTP 5xx and connection-refused are **both** treated as non-retryable (`ProviderUnavailableError`, not in `RETRYABLE_ERROR_TYPES`) — a local Ollama daemon returning 500 usually means something is actually broken (crashed model process, OOM, malformed request), not a transient blip worth a same-millisecond retry. Documented in `docs/ai/learning-log.md`'s first entry. **The actual lesson, worth internalizing before E2+ adds more error-prone integrations:** retry-eligibility needs to be a named, reasoned-about, per-error-type set (`orchestration/policies.py`'s `RETRYABLE_ERROR_TYPES`), individually tested — not inferred ad hoc per call site.
- **Local-model structured-output risk is real and untested against a real model.** `OllamaModelProvider`'s retry-with-feedback mechanism is verified only against `httpx.MockTransport` (scripted responses) — this proves the *mechanism* works, not that real Qwen2.5:7b-instruct output actually improves when shown its own validation error. First thing to check once Ollama is installed (§13's smoke test is the minimal version of this check; a fuller check needs E3's Planner to exist).
- **Limited hardware** (§6) means CPU-only inference at a few tokens/second for a 7-8B model. This will materially affect development iteration speed for E3+ and must be treated as a first-class evaluation metric (latency) in E7, not an incidental footnote.
- **Danger of building another infrastructure phase without ever making a real model call.** E0 and E1 are both infrastructure/scaffolding phases — genuine, tested infrastructure, but neither has made one real call to a real model. This is explicitly the risk §13's minimal smoke test exists to retire before E2 begins — do not let E2 (more scaffolding: corpus tools) start before at least one real Ollama call has been made and reported.
- **Risk of overfocusing on Concert of Europe** — see §8 in full. Not yet manifested as a code problem (no topic branching exists anywhere checked so far), but the risk grows with every corpus-adjacent line of code until a second, materially different corpus exists (E8).
- **The fixed workflow engine (`engine.py`) is unsuitable for dynamic agent loops** — this is a *resolved* risk (the E0 audit caught it before any code was written against the wrong shape), not an open one, but worth restating so nobody in a future session tries to "simplify" by wiring `ai/orchestration/` into `run_pipeline()`. Don't.
- **No stale documentation or unresolved inconsistencies were found this session.** The E0 documentation sweep already caught and fixed three stale Phase E-L cross-references (`system-overview.md`, `frontend-architecture.md` ×2, `generated-investigation-contract.md`) before E1 began. This session's fresh read of `docs/ai/*.md`, `docs/decisions/ADR-003-*.md`, `docs/delivery/revised-development-phases.md`, and `plans/current-phase.md` found them internally consistent with each other and with the actual `git log`/file tree.

---

## 11. Pending decisions requiring Kamal's approval

Do not assume any of these. Each needs a separate, explicit yes.

1. **Approve committing Phase E1** (the untracked/modified files listed in §3, as one commit on `phase-e-ai-core`).
2. **Approve pushing the Phase E1 commit** — and separately, note that `phase-e-ai-core` itself has never been pushed, so this is also the first push of the branch.
3. **Approve installing Ollama** on this machine.
4. **Approve downloading the selected initial model** (`qwen2.5:7b-instruct`, ~4.7 GB) — or a different model, if Kamal prefers.
5. **Approve the exact first real-model smoke test** — see §13 for its proposed minimal definition; confirm scope before running it.
6. **Approve beginning Phase E2** (corpus service + typed tools) — only after E1 is committed, pushed, and the smoke test (§13) has actually run against a real model and been reported.

---

## 12. Exact recommended next actions for the new session

1. Read the documents in §2's order.
2. Independently check Git state (`git status`, `git log --oneline -8`, `git branch -vv`) — do not trust §3's numbers without re-verifying; time has passed.
3. Review the uncommitted E1 diff (`git status --porcelain`, spot-check a couple of the new files in `backend/src/chronicle/ai/`).
4. Run the E1 verification suite: `cd backend && .venv/Scripts/python.exe -m pytest -q`, `npm run typecheck`, `npm run lint`, `npx vitest run`, `npm run build`, `npm run test:e2e`.
5. Report any discrepancy from this handoff document plainly — do not silently patch over it or silently trust this document over what you actually observe.
6. Summarize the exact current state back to Kamal in your own words (don't just restate this document verbatim).
7. Present the immediate E1 closeout plan: commit → push, in that order, each requiring separate approval per §11 items 1-2.
8. **Wait for explicit approval before**: committing, pushing, installing Ollama, downloading a model, running the smoke test, or starting E2. None of these should happen from inertia or because "the plan already covers it" — each is a separate ask per §11.

---

## 13. Minimal Ollama smoke-test definition

Once Kamal separately approves Ollama installation and a model download (§11 items 3-4), the **smallest useful live-model test** is:

1. Call `OllamaModelProvider().health_check()` against the real local daemon — confirm `healthy: True`.
2. Confirm the configured model (`qwen2.5:7b-instruct`, or whatever was actually pulled) is present — e.g. via the health check's `/api/tags` response, or `ollama list`.
3. Submit **one** small, simple Pydantic structured-output request (a trivial schema — a couple of scalar fields, not a nested agent contract like the future `AnalysisDraft`) via `generate_structured()`.
4. Validate the response parses and matches the Pydantic model — i.e., confirm the real path that mock tests only simulated actually works end to end.
5. Record latency (`ModelCallRecord.latencyMs`) and full metadata (provider/model/prompt version, attempt count, usage if reported) from the real call.
6. If the model returns malformed output, confirm the retry-with-feedback path engages **only** up to `MAX_STRUCTURED_OUTPUT_ATTEMPTS = 2` — do not let it retry indefinitely, and do not manually intervene to force a success.
7. **Do not** have this smoke test make any agent-shaped claim (no Planner/Analyst/Critic/Guide behavior — none of those exist yet), and no web-search claim of any kind.
8. Write a short implementation report (a few paragraphs — real latency observed, whether structured output succeeded first-try or needed the retry, any surprises) into `docs/ai/learning-log.md` as a new dated entry.

**Do not**, as part of this smoke test: download multiple models, begin any benchmarking, or treat a single successful call as proof the four-agent architecture will work — it only proves the wiring is correct.

---

## 14. Phase E2 preview (not implemented — do not build this as part of this handoff)

Phase E2 is expected to build a deterministic corpus service and agent-callable typed tools over the fields already embedded in an existing `GeneratedInvestigation` package (no database — the corpus *is* the already-generated package, per the E0/ADR-003 audit finding about `provenance-and-review.md`'s aspirational database). Planned tools, from `plans/current-phase.md`'s "Next Vertical Slice — Phase E2" section and `docs/delivery/phase-e-ai-core-plan.md`:

`search_passages`, `get_source_metadata`, `get_claim_evidence`, `get_relationship_evidence`, `get_timeline_context`, `get_actor_knowledge_state`, `compare_sources`, `find_counterevidence`, `trace_reviewed_relationships`, `get_map_context`.

Phase E2 must work across **more than one benchmark corpus from day one** (blank-cheque and concert-of-europe, at minimum — see §8) — cross-corpus parameterization from the start, not retrofitted for E8 later.

This handoff does not implement any of this. It is context for what comes after E1's closeout (§11 item 6).

---

## 15. Standing rules (apply throughout, not just to E1)

- Do not commit without explicit approval.
- Do not push without explicit approval.
- Do not install software without explicit approval.
- Do not download models without explicit approval.
- Do not introduce paid APIs (`AGENTS.md` §5 — any paid dependency needs a written justification and Kamal's approval first).
- Do not begin live web search yet (deferred to Phase F).
- Do not modify unrelated UI (frontend freeze in effect per ADR-003 §5 until the AI core lands).
- Do not rewrite historical content (the curated Concert of Europe content's accuracy is a human-review concern, not something to silently "improve").
- Preserve all existing tests and accessibility foundations — every phase in this project has run the full regression suite before considering a slice done; keep doing that.

---

## 16. Copy-paste starter prompt

Paste the following into a fresh Claude Code session in this repository:

```
Read docs/delivery/claude-chat-handoff-phase-e1.md in full — it is a complete handoff for resuming Chronicle's Phase E1 (AI model-provider foundation) work, written by the session that just finished implementing it.

Then, before doing or proposing anything else:

1. Read the documents listed in the handoff's §2 "Authoritative reading order," in that order: AGENTS.md, CLAUDE.md, plans/current-phase.md (at least from "## Completed: Phase E0" onward), docs/delivery/revised-development-phases.md, docs/ai-core-instructions/00 through 06, docs/decisions/ADR-003-llm-agent-system-is-product-core.md, docs/ai/agent-architecture.md, docs/ai/model-provider-decisions.md, docs/ai/learning-log.md, docs/architecture/generated-investigation-contract.md, the InvestigationExperiencePlan contract files, docs/product/map-first-workspace-instructions.md, and docs/architecture/provenance-and-review.md (noting its aspirational-database caveat).

2. Independently verify the repository and Git state against the handoff's §3 — run git status, git log --oneline -8, git branch -vv yourself. Do not trust the handoff's numbers without re-checking; time has passed since it was written.

3. Review the uncommitted Phase E1 diff (git status --porcelain, and read a couple of the new files under backend/src/chronicle/ai/ directly).

4. Run the full E1 verification suite: backend pytest, npm run typecheck, npm run lint, npx vitest run, npm run build, npm run test:e2e.

5. Report any discrepancy between what the handoff claims and what you actually observe — plainly, not silently patched over.

6. Summarize the exact current state back to me in your own words.

7. Present the immediate E1 closeout plan (commit, then push — each a separate approval per the handoff's §11).

Then STOP and wait for my explicit approval before: committing anything, pushing anything, installing Ollama, downloading any model, running the real-model smoke test (handoff §13), or starting Phase E2 (handoff §14, preview only — do not implement it yet). Do not assume any prior approval carries forward from this handoff document itself — each of those six actions needs its own yes from me, per the handoff's §11 and §15.
```
