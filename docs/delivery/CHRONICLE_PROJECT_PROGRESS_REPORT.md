# Chronicle Project Progress and Engineering Handoff

**As of:** 2026-08-24
**Repository:** https://github.com/kal-A/chronicle
**Active branch:** `phase-e-ai-core`
**Audience:** engineering collaborator onboarding to product, architecture, implementation, and next-phase decisions

## 1. Executive status

Chronicle is an AI-powered historical investigation generator and interactive systems atlas. The working product is now substantially beyond the original static July Crisis viewer: it has a versioned investigation package, two package-backed benchmark investigations, a map-first responsive workspace, an Inspector mode, a typed Python corpus/tool layer, four bounded LLM roles, a local Ollama/Qwen provider, persisted sequential orchestration, a narrow FastAPI/SSE boundary, and a live investigation Ask panel.

The implementation is still pre-alpha. It does **not** yet search the web, archives, scholarly databases, or uploaded documents; generate a genuinely new investigation from an arbitrary landing-page query; use a production database; provide authentication or an editorial Studio; or have a hosted production deployment. The landing page currently routes to one of two curated investigation packages. The in-investigation Ask feature is real and corpus-grounded.

The current engineering priority is Phase E7: determine, with repeatable evidence, whether the four-agent architecture improves historical correctness, citation validity, abstention quality, and usefulness enough to justify its latency and complexity. E7 is planned but not implemented.

## 2. What a collaborator can run and inspect

### Current product flow

1. The `/` route presents the Chronicle atlas-style question surface.
2. The typed hero copy and sourced Atlantic coastline draw in together, with reduced-motion handling.
3. A question is matched against the two curated packages and passes through the visible scope/progress transition.
4. The investigation opens in a map-first workspace with time navigation, lenses, and a docked desktop panel or mobile bottom sheet.
5. Ask, Explore, Evidence, and Sources operate over the same validated package and focus state.
6. Ask submits the active question and workspace context to FastAPI, shows Scope/Retrieve/Analyze/Verify/Compose progress, and renders a cited answer, limitations, abstention, recovery, tool activity, and validated map actions.
7. Inspector preserves the deeper narrative/timeline/relationship/evidence presentation.

### Current routes

- `/`
- `/investigations/:packageId/scenes/:sceneId`
- `/investigations/:packageId/scenes/:sceneId/inspector`

### Current backend surface

- `GET /health`
- `GET /api/corpora`
- `POST /api/investigations/{investigation_id}/questions`
- `GET /api/agent-runs/{run_id}`
- `GET /api/agent-runs/{run_id}/events`
- `POST /api/agent-runs/{run_id}/resume`
- `POST /api/agent-runs/{run_id}/cancel`

## 3. Product and architecture pivots

### Pivot 1: static Explore viewer to generation-first product

The original application was a hand-authored July Crisis investigation viewer. The first pivot made `GeneratedInvestigation`—not manually authored scenes—the canonical product boundary. The existing experience became a golden fixture and generic renderer regression case. This prevented content expansion from disguising the absence of a reusable generation system.

### Pivot 2: article-first to map-first investigation workspace

The article/timeline/graph presentation was useful for inspection but did not express the intended “historical systems atlas” experience. Phase D made a bounded map the primary workspace, added historical lenses and a persistent assistant/evidence dock, and preserved the prior renderer as Inspector. The interaction inspiration is Paradox-style strategic-map legibility and layered systems thinking, without game mechanics, simulation, or alternate-history claims.

### Pivot 3: source-pipeline-first to LLM-agent-system-first

The roadmap originally placed broad discovery and acquisition before proving the AI reasoning core. ADR-003 reversed that dependency: first build and evaluate the domain-specialized agent workflow against controlled corpora; then add live discovery and acquisition through the same typed boundaries. This reduces the chance of constructing expensive infrastructure around an unproven reasoning product.

### Pivot 4: hosted/frontier model assumptions to local open-weight development

The no-paid-infrastructure constraint and the development machine’s approximately 13.69 GB RAM led to Ollama plus `qwen2.5:7b-instruct`. A provider protocol keeps the runtime replaceable. The project accepted slower local inference to gain reproducibility, privacy, zero provider billing, and an inspectable portfolio implementation. E7 must determine whether this tradeoff is viable.

## 4. Phase status

| Phase | Status | Output |
|---|---|---|
| A | Complete | Audit/salvage of the original prototype and AI-first pivot foundation. |
| B | Complete | Versioned Zod `GeneratedInvestigation`, golden package, generic repository/route/renderer, cross-reference and historical-integrity validation. |
| C0-C3 | Complete | Pydantic contract parity, deterministic resumable workflow/CLI, mock providers, and a curated Concert of Europe package. |
| D0.1-D0.6 | Implemented; human usability gate still outstanding | Map-first workspace, `InvestigationExperiencePlan`, lenses, responsive dock/sheet, Inspector preservation, landing Ask prototype. |
| E0 | Complete | Product/core reorientation, ADR-003, revised E-K roadmap. |
| E1 | Complete | `ModelProvider`, deterministic provider, Ollama provider, structured generation, audit metadata, real Qwen smoke. |
| E2 | Complete and previously pushed | Package-backed corpus, deterministic lexical search, ten typed evidence/time/map/relationship tools, corpus isolation and bounds. |
| E3 | Implemented locally/checkpoint scope | Investigation Planner, retrieval execution, Evidence Analyst, grounding validation, persisted audit records. |
| E4 | Implemented locally/checkpoint scope | Historical Critic, one bounded evidence retry, Investigation Guide, validated answer/citations/actions, real Critic→Guide smoke. |
| E5 | Implemented locally/checkpoint scope | FastAPI, one sequential worker, polling/SSE progress, persisted resume and safe-boundary cancellation. |
| E6 | Working vertical slice; not formally closed | Live Ask panel, context snapshot, stage progress, citations, limitations, actions, abstention, history and recovery. Semantic usefulness and latency remain open gates. |
| E7 | Planned, not implemented | Comparative single-prompt/basic-RAG/Planner–Analyst/full-workflow evaluation, blinded review and regression thresholds. |
| E8 | Planned | Formal cross-domain/holdout generalization and no-topic-branching gate. |
| E9 | In progress through accumulated notes | Consolidated AI methodology and learning documentation. |
| F | Planned | Selected live source discovery adapters, query provenance, candidate assessment and rights metadata. No snippet-as-evidence. |
| G | Planned | Rights-respecting document acquisition, stable passages/OCR mappings, then justified lexical/hybrid retrieval. |
| H | Planned | AI-proposed actors, events, claims, knowledge states and relationships from the acquired corpus. |
| I | Optional/evidence-gated | Fine-tune one bounded historical reasoning task, not the entire assistant. |
| J | Planned | AI-generated geographic scope, lenses, routes and experience plans. |
| K | Long-term | New topic through discovery, corpus, historical model, map experience, review and publication. |

## 5. Implemented technology

### Frontend

- React 19, TypeScript, Vite and React Router.
- Zod contracts and cross-reference validation.
- MapLibre GL JS for mapped investigation assets; sourced Natural Earth coastline geometry for the landing atlas.
- Cytoscape.js for focused relationship/system views.
- TanStack Query is installed as the intended server-state library; the current assistant controller also uses fetch, SSE and polling directly.
- Tailwind tooling plus a large project-specific CSS layer.
- Vitest, React Testing Library, user-event, axe-core and Playwright.

### Backend and AI runtime

- Python 3.11+ target, Pydantic v2, FastAPI, Uvicorn and HTTPX.
- File-backed package, workflow and agent-run persistence; no production database.
- Ollama with `qwen2.5:7b-instruct`; no runtime API key or provider charge.
- Deterministic model provider for ordinary tests.
- pytest with live-Ollama tests opt-in and excluded from normal runs.

### Planned rather than implemented

PostgreSQL, SQLAlchemy, Alembic, pgvector, optional PostGIS, Docker Compose, GitHub Actions, authentication/authorization, object storage, a review/publication service and hosted infrastructure remain architectural targets. They must not be described as current capabilities.

## 6. LLM methodology

Chronicle uses four sequential roles over one model:

1. **Investigation Planner** converts a question and workspace context into a typed plan and one bounded initial tool call.
2. **Evidence Analyst** produces structured statements and exact citations constrained to retrieved records.
3. **Historical Critic** evaluates every statement, handling support, counterevidence, chronology, actor knowledge and uncertainty; it may request at most one additional retrieval.
4. **Investigation Guide** presents only Critic-approved material and emits closed, package-validated UI actions.

Ten deterministic tools expose passages, sources, claims, counterevidence, relationships, traversal, timelines, actor knowledge and map context. The model never receives arbitrary code execution or unrestricted browsing. Structured output is validated by Pydantic and again by deterministic domain-specific gates. Private chain-of-thought is neither requested nor stored.

The architecture was chosen over a single prompt because it separates planning, evidence use, historical criticism and presentation into inspectable failure boundaries. It was chosen over unconstrained agent swarms because Chronicle needs bounded latency, reproducibility, auditability and explicit responsibility. It was chosen over basic RAG alone because retrieval relevance does not prove entailment, preserve who knew what when, or handle disputed interpretations. Those are hypotheses, not settled facts: E7 compares all simpler alternatives under the same model and corpus.

## 7. Historical-integrity invariants

- Material claims and relationships retain passage-level evidence and classification.
- Chronological adjacency never establishes causation.
- Supporting, counterevidence and contextual roles remain distinct.
- Event time, report time, sent time, received time, actor-awareness time and interpretation time are not collapsed.
- Actor knowledge is never inferred merely because information existed elsewhere.
- Geographic precision is explicit; region/city evidence cannot become a building pin.
- Modern borders cannot be displayed as historical political geography without period-specific sourcing.
- Search snippets and metadata are discovery material, not evidence.
- Unsupported output abstains or remains partial.
- New sources will eventually enter impact review; they must not silently rewrite published prose.

## 8. UX/UI state

The current design direction is an “Illuminated Atlas Table”: deep ink and Prussian blue, warm bone typography, oxidized copper as the restrained action signal, and cyan registration/evidence cues. The landing geography is drawn from sourced coastline data rather than invented shapes. The title types in as the map is progressively drawn. A particle/cartographic transition carries the question into the investigation.

The workspace continues the same material system rather than reverting to the earlier neutral prototype. A bounded map dominates; time and lens controls alter what is emphasized; the dock exposes Ask, Explore, Evidence and Sources. Mobile uses a bottom sheet. The app retains keyboard focus states, semantic controls, non-map alternatives and reduced-motion behavior.

Important limitation: the investigation maps and labels are only as accurate as their curated package assets. Automatic historical boundary/map generation is Phase J. Cartographic provenance and accuracy remain product credibility gates.

## 9. Current verification evidence

- E2’s last clean full-backend record: 514 passed, 4 skipped, 1 live-Ollama test deselected.
- E4 focused: 14 passed; AI/tool/provider/storage slice: 354 passed, 1 skipped, 2 live tests deselected.
- E5 focused workflow/manager/API: 13 passed; AI/API slice: 355 passed, 1 skipped, 2 live tests deselected.
- E6 AI/API/storage slice: 377 passed, 1 skipped, 5 live tests deselected.
- E6 frontend: 117 tests passed; typecheck, lint and production build passed.
- Real selected-evidence E6 run: full workflow returned `answer_ready` with one exact supporting citation.
- Real broader E6 run: retrieval and all roles completed, but the final result safely abstained.

### Current whole-tree blocker

On 2026-08-24, a fresh default backend collection stopped with three errors because tracked `backend/src/chronicle/storage/run_store.py` is deleted in the local working tree while retained workflow/provider tests import it. A larger set of legacy curated-provider and test files is also marked deleted. These removals are not an approved architectural change and must not be pushed as deletions. The newer E3-E6 slice remains independently green, but the whole backend cannot be called green until the working tree is reconciled and the full suite is rerun from the collaboration checkpoint.

The live-Ollama marker also produced unknown-marker warnings when pytest was invoked from the repository root without explicitly selecting `backend/pyproject.toml`; onboarding commands should use `-c backend/pyproject.toml` or run from `backend/`.

### Collaboration-checkpoint verification

The selective collaboration commit deliberately retained the legacy files instead of publishing their local deletions. That exact committed snapshot was checked out in an isolated worktree and the complete backend suite passed: **637 passed, 4 skipped, 5 opt-in live-model tests deselected**. This is the state collaborators receive from GitHub; the deletion-related collection failure applies to the owner’s still-dirty local worktree, not the published checkpoint.

## 10. Known limitations and likely future limits

### Current limitations

- Landing search is keyword matching over two packages, not open-ended research.
- Ask retrieves only from the active package; no web/archive/database access exists.
- Lexical retrieval has no embeddings, reranking or large corpus.
- A lexically related citation can still fail semantic entailment or reverse who acted on whom.
- Local CPU inference is slow: a complete broad four-role run can take several minutes.
- The Critic can be safely conservative but therefore unhelpful.
- File persistence is suitable for one local worker, not multi-user concurrency or hosting.
- No auth, accounts, workspace permissions, upload threat model, Studio review UI or deployment pipeline.
- Historical content is prototype-curated and has not completed professional historian validation.
- The frontend CSS and map bundles are large and should eventually be modularized/profiled.

### Future structural limits

- Historical source access is fragmented by rights, paywalls, unstable APIs, OCR quality and incomplete metadata.
- Universal history is not an achievable near-term support claim; domain expansion must be benchmarked.
- Historical maps require period-specific sourcing/georeferencing; automatic map composition cannot safely infer borders from modern data.
- Four sequential LLM calls may remain too expensive in latency even if quality improves; E7 may justify collapsing roles or using different models by role.
- A public version requires durable review/publication boundaries so unreviewed model output cannot leak into Explore.
- Human review and source curation may become the dominant bottleneck even after technical automation improves.

## 11. Highest-value engineering review areas

1. Reconcile the unexplained deleted legacy files before any merge, then run the true full backend suite.
2. Implement E7 without altering production prompts first; measure before optimizing.
3. Review semantic statement segmentation, directionality and entailment gates—the current highest-risk correctness gap.
4. Profile per-role latency, tokens and retry behavior; compare role collapse, caching and smaller-model options.
5. Review run identity, model digest, prompt version, corpus hash and retry-attempt audit completeness.
6. Review SSE plus polling behavior, file-store locking and cancellation under browser reconnects.
7. Reduce frontend CSS/component concentration and MapLibre/Cytoscape bundle weight without diluting the visual system.
8. Define the smallest rights-safe Phase F provider set only after E7 establishes the reasoning architecture.
9. Introduce database/auth/deployment infrastructure only when a concrete F/G/Studio requirement makes it load-bearing.

## 12. Recommended dependency hierarchy

```text
Reconcile Git/worktree and establish a green checkpoint
→ E7 deterministic harness and provider audit
→ bounded live-Qwen benchmark run
→ blinded human review and architecture decision
→ E8 generalization/holdout gate
→ E9 consolidated AI lessons and Phase E closure
→ Phase F source discovery adapters
→ Phase G acquisition and durable RAG corpus
→ Phase H historical-model proposals
→ Phase J experience/map composition
→ Phase K end-to-end autonomous draft investigation
```

Phase I is an optional task-model experiment and should proceed only if evaluation traces reveal a stable bounded task worth fine-tuning.

## 13. Git and collaboration state

The canonical remote is `origin = https://github.com/kal-A/chronicle.git`.

Published history before this handoff checkpoint:

- `master` / `origin/master`: initial viewer (`1ee3541`).
- `phase-c-python-foundation` / remote: through C, D and E0 (`43d2b94`).
- `phase-e-ai-core` / remote: through E2 (`32955e1`) before the collaboration checkpoint described in this report.

The 2026-08-24 collaboration checkpoint includes E3-E6 code, current frontend/design/runtime assets, E4-E6 reports, the E7 plan/validation protocol, PRD, this progress report and an updated README. It explicitly excludes the unexplained tracked deletions, local `.impeccable/` working artifacts and the unclassified `chronicle user flow` binary.

Recommended workflow:

1. Read `AGENTS.md`; Claude users also read `CLAUDE.md`.
2. Fetch and branch from `origin/phase-e-ai-core` after the checkpoint lands.
3. Do not have two coding agents mutate the same working tree.
4. Work in bounded vertical slices with deterministic tests.
5. Do not commit secrets, add paid runtime dependencies, or expose local FastAPI/Ollama publicly.
6. Do not commit/push/merge without the owner’s explicit approval.

## 14. Local setup

### Frontend

```powershell
npm install
npm run dev
npm run typecheck
npm run lint
npm test -- --run
npm run build
```

### Backend

```powershell
py -3.11 -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -e "backend[test]"
backend/.venv/Scripts/python -m pytest -c backend/pyproject.toml backend/tests/ai backend/tests/api backend/tests/storage/test_agent_run_store.py -q
backend/.venv/Scripts/python -m uvicorn chronicle.api.app:app --app-dir backend/src --host 127.0.0.1 --port 8000
```

### Local model

Install Ollama separately, then pull the approved model:

```powershell
ollama pull qwen2.5:7b-instruct
ollama list
```

`CHRONICLE_OLLAMA_BASE_URL` defaults to `http://localhost:11434`. Copy `.env.example` to an ignored `.env` only if local configuration needs to differ. No API key is required.

Live tests are intentionally opt-in because they are slow and require the daemon/model. Consult `backend/pyproject.toml` and the E7 validation plan before running the multi-hour benchmark gate.

## 15. Essential reading order

1. `README.md`
2. `docs/product/CHRONICLE_PRODUCT_REQUIREMENTS.md`
3. This progress report
4. `AGENTS.md`
5. `docs/decisions/ADR-002-map-first-workspace.md`
6. `docs/decisions/ADR-003-llm-agent-system-is-product-core.md`
7. `docs/ai/agent-architecture.md`
8. `docs/ai/tool-registry.md`
9. `docs/delivery/phase-e7-evaluation-harness-plan.md`
10. `docs/delivery/phase-e-validation-plan.md`
11. `plans/current-phase.md`

## 16. Immediate decisions for the collaborators

- Does E7 show enough quality improvement to retain all four roles?
- What is the acceptable local/demo latency target, and which optimization preserves historical safety?
- Should semantic entailment remain human-evaluated, become a deterministic rubric, use a dedicated task model, or combine these approaches?
- Which two or three Phase F discovery providers have stable access, usable rights, and sufficient historical value?
- At what concrete capability does file persistence stop being adequate and justify PostgreSQL?
- What evidentiary standard and reviewer profile are required before any investigation can be labeled reviewed rather than prototype-curated?

The strongest near-term contribution is not adding more features. It is making the current core measurable, reproducible and semantically trustworthy, then using those results to simplify or strengthen the architecture before Chronicle expands its source surface.
