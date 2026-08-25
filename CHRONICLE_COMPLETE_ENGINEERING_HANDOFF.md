# Chronicle — Complete Product and Engineering Handoff

**Updated:** 2026-08-24

**Repository:** https://github.com/kal-A/chronicle

**Branch to use:** `phase-e-ai-core`

**Current checkpoint:** `482a4e6`
**Product state:** local pre-alpha; E6 working vertical slice; E7 planned but not implemented

This document is the single onboarding packet for an engineer joining Chronicle. It covers the product, current implementation, architecture, AI methodology, investigation/search infrastructure, UI, phase history, limitations, risks, setup, and next work. The repository contains deeper records, but they are not prerequisites for understanding the project.

## 1. Product in one page

Chronicle is an AI-powered historical investigation generator and interactive systems atlas. A user begins with a historical question. Chronicle’s intended full system bounds the question, discovers and assesses sources, builds a traceable corpus, constructs claims/events/relationships/knowledge states, and turns those records into a versioned investigation that can be explored through a synchronized map, timeline, evidence system, source inspector, relationship view, and grounded assistant.

Chronicle is designed to bridge two weak extremes:

- Static historical articles are trustworthy but usually flatten disagreement, actor knowledge, causal uncertainty, geography, and evidence chains into a single narrative.
- General chatbots are flexible but can invent facts, citations, relationships, and confidence.

Chronicle’s differentiator is not chat by itself. It is a durable historical model whose claims, sources, chronology, geography, uncertainty, and revisions are inspectable.

The two current investigations—the July Crisis/Blank Cheque and Concert of Europe—are benchmark packages and product demonstrations. Chronicle is not specific to either event, Europe, or one period. The initial reliable domain is intentionally narrower: European diplomatic and political history, 1814–1914.

### Target users

1. Curious history readers following structured historical rabbit holes.
2. Students and serious enthusiasts interrogating claims and evidence.
3. Later: historians and trusted editors reviewing sources, AI proposals, and publication revisions.
4. A secondary portfolio audience evaluating the project’s product judgment, engineering quality, AI rigor, and interface craft.

### What Chronicle is not

- A generic history chatbot.
- A Wikipedia replacement.
- An autonomous historian.
- A strategy game or alternate-history simulation.
- A graph visualization looking for a purpose.
- A one-prompt research agent.
- An unrestricted web scraper.
- A professional archival/publication platform in its current state.

## 2. What currently works

### User-facing product

- An animated map-first landing page with a historical question field.
- Typed headline/intro motion synchronized with a progressively drawn Atlantic coastline.
- Sourced Natural Earth coastline geometry rather than invented map shapes.
- Scope and generation-transition presentation.
- Deterministic routing to two disclosed curated investigation packages.
- A responsive map-first investigation workspace.
- Desktop dock and mobile bottom sheet with Ask, Explore, Evidence, and Sources tabs.
- Timeline/lens/map/source/evidence focus synchronization.
- Inspector mode preserving the deeper narrative, timeline, graph, claims, and evidence presentation.
- A live in-investigation Ask feature connected to the Python backend.
- Visible Scope → Retrieve → Analyze → Verify → Compose progress.
- Cited answers, limitations, tool activity, typed map actions, safe abstention, resume, and recovery states.

### Backend and AI

- TypeScript/Zod and Python/Pydantic versions of the versioned `GeneratedInvestigation` contract.
- Cross-record verification for IDs, evidence, claims, relationships, publication status, rights, dates, and geographic precision.
- A deterministic/resumable Python generation workflow and CLI foundation.
- Two package-backed corpora with corpus isolation.
- Deterministic lexical passage search.
- Ten bounded evidence/time/source/map/relationship tools.
- A provider-neutral model interface.
- A deterministic model provider for normal tests.
- Ollama integration using `qwen2.5:7b-instruct` locally.
- Four bounded LLM roles: Planner, Analyst, Critic, and Guide.
- File-backed durable agent runs.
- One sequential worker, progress journal, resume, cancellation boundaries, polling, and SSE.
- A narrow FastAPI interface consumed by the React Ask panel.

### What does not work yet

- The landing page cannot investigate an arbitrary new question.
- No live web, archive, library, or scholarly-database search exists.
- No URL/file/PDF ingestion, OCR, embeddings, hybrid search, or reranking exists.
- No PostgreSQL/pgvector/PostGIS runtime exists.
- No authentication, accounts, collaboration, or editorial Studio exists.
- No production deployment exists.
- No automatic historical-boundary or map-experience generation exists.
- Current packages remain `prototype-curated`, not professionally reviewed publications.

## 3. Current end-to-end flow

```text
Landing question
→ deterministic match against two registered packages
→ scope/progress presentation
→ cartographic transition
→ map-first investigation workspace
→ user asks a question with map/time/lens/selection context
→ FastAPI creates a persisted agent run
→ Planner chooses one permitted typed tool call
→ deterministic tool retrieves bounded package evidence
→ Analyst proposes cited statements
→ grounding validator checks record/citation/time/geography/knowledge constraints
→ Critic accepts, downgrades, rejects, requests one bounded retrieval, or abstains
→ Guide presents only approved material
→ final validator checks citations and map-action targets
→ UI renders answer or abstention with evidence, limitations, actions, and audit progress
```

The assistant can investigate the active package. It cannot currently build a corpus for an arbitrary topic.

## 4. Architecture

```text
React / TypeScript / Vite
  Ask landing + Map workspace + Inspector
  MapLibre + Cytoscape + Zod
            │ HTTP + SSE/polling
            ▼
Python / FastAPI / Pydantic
  AgentRunManager (one bounded worker)
  SequentialAgentWorkflow
            │
   ┌────────┼─────────┐
   ▼        ▼         ▼
Agents   Typed tools  File-backed run store
   │        │
   │        └── PackageBackedCorpus
   ▼
ModelProvider
  ├── DeterministicModelProvider (tests)
  └── OllamaModelProvider → qwen2.5:7b-instruct
```

### Architectural boundaries

- The frontend never talks directly to Ollama.
- LLMs handle ambiguous language and bounded proposals.
- Deterministic software owns validation, record identity, permissions, workflow state, citations, geography, dates, action references, publication rules, and failure boundaries.
- Model output is never historical ground truth.
- No autonomous agent swarm is permitted.
- Private chain-of-thought is neither requested nor stored.
- Current corpus and agent persistence is file-based; database architecture is a future target.

## 5. Canonical investigation package

`GeneratedInvestigation` is the versioned interchange boundary between research/generation and rendering. It is not a database dump.

It contains or references:

- Request and bounded scope.
- Sources, documents, passages, and locators.
- Entities and historically named places.
- Events, decisions, claims, relationships, and evidence links.
- Actor knowledge records.
- Narrative blocks and claim ledgers.
- Timeline records with explicit date roles.
- Map assets, locations, precision, period, attribution, and limitations.
- Interaction specifications and optional `InvestigationExperiencePlan`.
- Generation/verification report and abstention/coverage information.

Both TypeScript and Python validate this contract. Significant prose must be traceable to structured evidence-backed claims.

## 6. Historical-integrity rules

These are non-negotiable:

- Chronological adjacency never proves causation.
- Relationships preserve classifications such as direct, indirect, contextual, correlational, disputed, speculative, or insufficient evidence.
- Supporting evidence, counterevidence, and context are distinct.
- Event time, report time, sent time, received time, actor-awareness time, discovery time, and interpretation time must not be collapsed.
- Information existing somewhere does not prove an actor knew it.
- City/region evidence cannot become a precise building pin.
- Modern political borders cannot masquerade as historical geography.
- Search metadata and snippets are discovery leads, never evidence.
- Unsupported output must become partial, hedged, or abstained.
- New sources must eventually enter impact review; they may not silently rewrite a published investigation.
- Published/reviewed versions must be immutable and superseded through explicit revision.

## 7. LLM methodology and why it was selected

### The four roles

1. **Investigation Planner**
   - Receives the user question and workspace/corpus context.
   - Chooses a bounded investigation goal and eligible typed tool call.
   - Cannot invent arbitrary tools or out-of-corpus record IDs.

2. **Evidence Analyst**
   - Receives only retrieved evidence.
   - Produces structured statements and exact citation tuples.
   - Must disclose truncation and preserve evidence/time/geography/knowledge classifications.

3. **Historical Critic**
   - Accounts for every Analyst statement.
   - Accepts, downgrades, rejects, requests at most one bounded evidence retry, or abstains.
   - Exists to challenge fluent but incomplete or misleading synthesis.

4. **Investigation Guide**
   - Receives Critic-approved material only.
   - Produces the user-facing answer and closed typed UI actions.
   - Cannot introduce a new material historical claim.

### Why not one prompt?

One prompt is cheaper and faster but mixes planning, retrieval, reasoning, criticism, and presentation into one opaque failure boundary. It remains an E7 baseline.

### Why not basic RAG?

Retrieval relevance does not prove that a statement is entailed, that the direction of support is correct, that counterevidence was accounted for, or that temporal/knowledge distinctions survived synthesis. Basic RAG also remains an E7 baseline.

### Why not an agent swarm?

Unbounded agents increase latency, nondeterminism, cost, permissions risk, and debugging complexity. Chronicle uses four named sequential roles, typed contracts, ten deterministic tools, bounded retries, and durable audit records.

### Why Ollama and Qwen?

The project must remain developable without paid runtime infrastructure. The development machine has roughly 13.69 GB RAM and no practical dedicated GPU acceleration for Ollama. A quantized 7–8B model is therefore the realistic ceiling.

`qwen2.5:7b-instruct` was selected for locally viable instruction-following and structured JSON behavior. One model is reused sequentially for all roles. The provider protocol allows future replacement with another local, hosted, or task-specific model without rewriting the agents.

Tradeoff: local control, privacy, reproducibility, and zero provider billing are gained at the cost of multi-minute CPU inference and weaker reasoning than a frontier hosted model.

### What the current Qwen result proves

- A selected-evidence full workflow produced `answer_ready` with an exact supporting citation.
- A broader corpus question completed all roles and safely abstained.
- The system can produce valid structured/cited output.
- It does **not** yet prove reliable open-ended historical answering.
- A live run exposed a semantic-direction risk: lexically grounded material can still reverse who supported whom.
- Safe abstention can also become overly conservative and unhelpful.

E7 exists to quantify these issues before the architecture expands.

## 8. Current search and retrieval

Current search is deterministic lexical retrieval over one validated package at a time. It has no web request, embedding, database, or document acquisition path.

### Registered tools

1. `search_passages`
2. `get_source_metadata`
3. `compare_sources`
4. `get_claim_evidence`
5. `find_counterevidence`
6. `get_relationship_evidence`
7. `trace_relationships`
8. `get_timeline_context`
9. `get_actor_knowledge_state`
10. `get_map_context`

### Safety properties

- Every invocation is bound to corpus ID, manifest, tool input, and execution context.
- Results are bounded by count and serialized character limits.
- Ranking is deterministic and records score factors.
- Date filtering uses explicit roles and interval overlap.
- Tool errors produce sanitized audit records.
- Relationship traversal is depth/path bounded and cycle-safe.
- Map results preserve exact stored precision and limitations.
- Actor-knowledge results return stored records only.

## 9. How online research will actually enable new investigations

This capability is planned in Phases F–K. It is not hidden inside the current Ask feature.

```text
Question
→ bounded scope proposal
→ provider-aware query plan
→ selected archive/library/scholarly discovery adapters
→ candidate registry with query provenance and deterministic deduplication
→ source assessment (relevance, authority, rights, access, period/geography fit)
→ accept / reject / defer candidates
→ rights-respecting HTML/PDF/IIIF acquisition
→ immutable original + content hash
→ OCR/text extraction with page/image mappings and confidence
→ stable passage segmentation
→ lexical retrieval first; embeddings/hybrid search only if evaluation justifies them
→ entity/event/claim/relationship/knowledge-state proposals
→ deterministic validation + Historical Critic + human review
→ geographic/experience-plan generation
→ versioned draft GeneratedInvestigation
→ Explore inspection
→ explicit review/publication
```

### Phase F: autonomous source discovery

Phase F introduces typed adapters for a deliberately small set of scholarly, archive, library, or institutional providers. It records every query, provider, timestamp, result, rejection, deduplication decision, rights status, and assessment. The Planner receives tools; it does not receive unrestricted browser access.

Discovery output is a traceable candidate corpus—not historical evidence. Search snippets never support claims.

### Phase G: acquisition and RAG corpus

Phase G acquires permitted full text or images, preserves originals and hashes, creates stable page/passage mappings, records OCR confidence, and exposes the searchable corpus behind the existing `InvestigationCorpus` interface. Lexical search is the default. Embeddings, vector storage, hybrid search, and reranking are adopted only when benchmarks show a material benefit.

### Phase H: historical-model generation

Models propose actors, institutions, events, decisions, communications, claims, knowledge states, relationships, uncertainty, and research gaps from the acquired corpus. Deterministic validation and human review retain authority.

### Phase J: geographic and experience composition

The system proposes bounded map scope, period-specific places/boundaries, lenses, routes, sequences, system paths, and an `InvestigationExperiencePlan`. Geographic assertions require sourced historical data and explicit precision.

### Phase K: full investigation

An arbitrary supported question can proceed from scope through discovery, acquisition, corpus construction, historical modelling, map composition, review, and a versioned investigation without hand-authoring a package.

## 10. Source enrichment and narrative impact

Sources are global evidence records; narrative is versioned presentation.

A newly added source does not mutate prose. It may produce proposed evidence/claims and an `ImpactReview` classifying its effect as supporting, contradicting, contextual, qualifying, duplicate, or unrelated. A human reviewer may accept/revise/reject that impact. Accepted changes create a draft presentation revision. Publishing that revision is a separate explicit action. Older reviewed versions remain immutable.

This preserves the user’s requested invariant: sources can always be added to a period/event and can influence context and accounting, but only through traceable claims and reviewed narrative revision.

## 11. UX/UI and cartographic direction

The creative direction is an “Illuminated Atlas Table”:

- Deep ink and Prussian blue environmental field.
- Warm bone typography.
- Oxidized copper reserved for action, focus, and progress.
- Cyan registration/evidence cues.
- Barlow Condensed display typography with system body text.
- Square controls and one-pixel rules; circles reserved for directional/cartographic functions.
- Layered coastlines, routes, cartographic fragments, documents, temporal traces, and geographic depth.
- Strategic-map interaction inspiration from Paradox titles without adopting game mechanics.

Landing behavior:

- Question-first task plane remains readable over cartography.
- Title and intro type in while geography is genuinely drawn from no coastline to complete coastline.
- Different historical/map material can later phase in as provenance-cleared layers.
- Reduced-motion users receive a meaningful accelerated/static equivalent.
- The transition into an investigation geographically resolves toward the relevant local scope.

Investigation behavior:

- The map is bounded to the investigation, not a needlessly complicated whole-world canvas.
- Events, evidence, and places respond to the selected time/lens/focus.
- Ask/Explore/Evidence/Sources stay available in the dock/sheet.
- Inspector provides deeper provenance/narrative scrutiny.
- Map labels, scale, placement, period validity, and spelling are credibility gates.
- Generated or modern political borders must never be shown as historical truth.

## 12. Technology stack

### Implemented now

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite, React Router |
| Validation | Zod frontend; Pydantic backend |
| Maps | MapLibre GL JS, sourced GeoJSON/curated historical assets |
| Relationships | Cytoscape.js |
| Styling | Tailwind tooling plus Chronicle CSS/design tokens |
| API | Python 3.11+, FastAPI, Uvicorn, HTTPX |
| AI | Ollama, `qwen2.5:7b-instruct`, deterministic test provider |
| Persistence | JSON packages and local file-backed workflow/agent runs |
| Tests | Vitest, React Testing Library, axe-core, Playwright, pytest |

### Target, not built

- PostgreSQL, SQLAlchemy, Alembic.
- pgvector and optional PostGIS if justified by real queries.
- Durable object/source storage.
- Docker Compose local stack.
- GitHub Actions CI/CD.
- Authentication and authorization.
- Review/publication service and Chronicle Studio.
- Hosted public backend; hosting decision remains open.

## 13. API and runtime

Current local endpoints:

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Runtime health |
| GET | `/api/corpora` | Available package corpora |
| POST | `/api/investigations/{investigation_id}/questions` | Start an agent run |
| GET | `/api/agent-runs/{run_id}` | Inspect persisted state |
| GET | `/api/agent-runs/{run_id}/events` | SSE progress/replay |
| POST | `/api/agent-runs/{run_id}/resume` | Resume recoverable run |
| POST | `/api/agent-runs/{run_id}/cancel` | Request safe cancellation |

The API is local, unauthenticated development infrastructure. Do not expose it directly to the public internet.

## 14. Development history and status

| Phase | State | Meaning |
|---|---|---|
| A | Complete | Froze/audited original prototype. |
| B | Complete | Versioned package and generic renderer. |
| C | Complete | Python parity, deterministic workflow/CLI, second curated package. |
| D | Implemented; human usability gate remains | Map-first workspace and Inspector. |
| E0-E2 | Complete | AI reorientation, model provider, corpus/tools. |
| E3 | Implemented | Planner, retrieval runner, Analyst, grounding. |
| E4 | Implemented | Critic, Guide, bounded retry, answer/action validation. |
| E5 | Implemented | FastAPI, persistence, SSE/polling, resume/cancel. |
| E6 | Working slice; not formally closed | Live Ask UI; semantic usefulness and latency remain open. |
| E7 | Planned | Comparative evaluation harness and human review. |
| E8 | Planned | Generalization/holdout/no-topic-branching gate. |
| E9 | Partially accumulated | Final AI learning documentation. |
| F | Planned | Source discovery. |
| G | Planned | Acquisition and RAG corpus. |
| H | Planned | Historical-model generation. |
| I | Optional | Fine-tune one bounded task if evidence justifies it. |
| J | Planned | Geographic/experience generation. |
| K | Long-term | Complete new-topic investigation pipeline. |

## 15. Phase E7: immediate next phase

E7 compares four strategies using the same corpus, cases, model, settings, and evidence rules:

1. Single prompt.
2. Basic retrieval plus one answer call.
3. Planner + Analyst.
4. Planner + Analyst + Critic + Guide.

It measures:

- Citation validity and citation-role correctness.
- Statement entailment and directionality.
- Counterevidence and temporal handling.
- Actor-knowledge correctness.
- Safe and useful abstention.
- Map-action validity/relevance.
- Cross-corpus isolation.
- Latency, tokens, retries, failures, and provider-billed cost.
- Repeat stability and Critic agreement/correction value.

The live gate is sequential/resumable because Qwen is slow. Blinded human review is a real blocking checkpoint; implementation agents cannot manufacture those judgments. The four-agent design is retained only if measured benefits justify the additional latency and complexity.

## 16. Verification at the collaboration checkpoint

Checkpoint `482a4e6` was pushed to `origin/phase-e-ai-core`.

- Exact committed backend snapshot: **637 passed, 4 skipped, 5 live-model tests deselected**.
- E6 frontend: **117 passed**.
- Type checking passed.
- Lint passed.
- Production build passed.
- Existing advisory: MapLibre and Cytoscape produce large bundles.
- Existing warning: Starlette/FastAPI test client reports an HTTPX-related deprecation.

The owner’s local working tree still contains unexplained deleted legacy files plus `.impeccable/` working assets and an unclassified `chronicle user flow` binary. Those deletions/files were deliberately excluded from the published checkpoint. A fresh clone of the branch receives the green retained files.

## 17. Current limitations and risks

### Product

- The central value of synchronized map/time/evidence/assistant exploration still needs usability validation.
- The assistant could become the whole product and weaken direct exploration.
- Broad “model all history” ambitions can destroy credibility and evaluation quality.

### Historical quality

- Source curation/review is real expert labor.
- A relevant citation may not entail the generated wording.
- Historiographical disagreement can be flattened by fluent prose.
- Cartographic errors immediately undermine legitimacy.
- Universal-domain reliability is not a reasonable MVP claim.

### AI

- Qwen latency is several minutes for some full workflows.
- Four roles may not outperform simpler architectures enough.
- Structured-output success does not guarantee semantic correctness.
- Critic safety can become unhelpful over-abstention.
- Local inference cost is zero provider billing, not zero electricity/hardware/time cost.

### Engineering

- File storage supports one local worker, not production concurrency.
- No auth/security boundary exists for public deployment.
- Frontend CSS is large and concentrated.
- Map/graph bundles need performance work.
- Discovery/acquisition will add significant rights, failure, and provenance complexity.
- Uploads will create an untrusted-input security boundary.

## 18. Recommended work hierarchy

```text
1. Work from the published clean checkpoint
2. Implement E7 contracts/runner/metrics without tuning prompts first
3. Run deterministic comparison tests
4. Run bounded live-Qwen gate
5. Complete blinded historical review
6. Decide whether to retain, collapse, or specialize the four roles
7. Close E8 generalization and E9 documentation
8. Select the smallest rights-safe Phase F provider set
9. Build Phase G acquisition/stable passage corpus
10. Introduce database infrastructure only when F/G/Studio makes it necessary
11. Build historical-model and geographic-generation phases
12. Attempt full new-topic investigation only after all earlier gates pass
```

High-value first engineering contributions:

- Review semantic statement segmentation, entailment, and directionality.
- Implement the reproducible E7 harness and provider/model digest audit.
- Profile per-role latency and evaluate role collapse/caching/smaller-model options.
- Review SSE/polling reconnects, file locking, and cancellation.
- Review frontend bundle/CSS modularity without diluting the visual system.
- Help choose Phase F providers based on access stability, rights, metadata, and historical usefulness.

## 19. Local setup

### Clone the correct branch

The repository is private; the owner must add the collaborator on GitHub.

```powershell
git clone --branch phase-e-ai-core https://github.com/kal-A/chronicle.git
cd chronicle
```

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
backend/.venv/Scripts/python -m pytest -c backend/pyproject.toml backend/tests -q
backend/.venv/Scripts/python -m uvicorn chronicle.api.app:app --app-dir backend/src --host 127.0.0.1 --port 8000
```

### Qwen

```powershell
ollama pull qwen2.5:7b-instruct
ollama list
```

`CHRONICLE_OLLAMA_BASE_URL` defaults to `http://localhost:11434`. Live-model tests are opt-in and intentionally excluded from ordinary test runs.

## 20. Collaboration rules

- Read `AGENTS.md` before changing the project; Claude Code also reads `CLAUDE.md`.
- Branch from `phase-e-ai-core`, not the outdated `master` branch.
- Keep work in bounded vertical slices with explicit acceptance gates.
- Do not have multiple coding agents edit the same working tree.
- Do not introduce paid runtime infrastructure without approval.
- Do not commit secrets or run artifacts.
- Do not expose local FastAPI/Ollama publicly.
- Do not treat snippets, metadata, or LLM knowledge as historical evidence.
- Do not add hand-authored investigations to simulate generation progress.
- Do not commit, push, merge, or rewrite history without the owner’s explicit approval.

## 21. Decisions the collaborators should make together

1. Does E7 justify all four roles?
2. What latency is acceptable for local development, portfolio demonstrations, and eventual users?
3. Should semantic entailment use human review, deterministic rules, a dedicated task model, or a combination?
4. Which initial Phase F providers are rights-safe, stable, and historically useful?
5. What exact evidentiary/reviewer standard permits “reviewed” rather than `prototype-curated`?
6. What concrete requirement triggers PostgreSQL instead of file persistence?
7. Which initial historical domains can be evaluated responsibly beyond 1814–1914 European diplomacy?
8. What deployment shape can preserve the free-development constraint without pretending local CPU inference is production hosting?

## 22. Bottom line

Chronicle has moved beyond a static mock. Its map-first interface and local four-agent assistant genuinely run against two validated historical corpora. The system can retrieve evidence, produce a cited answer, reject invalid output, and safely abstain. The project’s central technical risk is no longer “can we connect an LLM?” It is “does this architecture consistently produce semantically correct and useful historical investigations at acceptable latency?”

The correct next move is evaluation, not broader feature expansion. Once the agent architecture earns its place, Chronicle can responsibly add source discovery, acquisition, durable corpus infrastructure, historical-model generation, and eventually complete question-to-investigation workflows.
