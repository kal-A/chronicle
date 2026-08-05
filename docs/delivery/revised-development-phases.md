# Revised AI-First Development Phases

This roadmap supersedes `development-phases.md` for active sequencing. The older roadmap remains historical context until reconciled/archived.

## Phase A — Freeze, Audit, and Salvage

Freeze manual scene expansion; inventory reusable code and hard-coding; preserve passing tests; define the Blank Cheque golden-fixture migration. Output: `current-prototype-salvage.md` and approved pivot architecture. Completion: documentation is internally consistent and current tests are baselined.

## Phase B — Generated-Investigation Contract and Generic Renderer

Define Zod `GeneratedInvestigation`/report/map/interaction schemas, version strategy, JSON golden fixture, generic loader, normalized frontend store, and package-driven route. Output: current UI renders the golden JSON with no July Crisis imports in generic renderer/provider code. Tests: package schema/references/version failures plus preserved UI/E2E behavior.

**Status (2026-08-03):** Complete. Contract, golden fixture, generic renderer, automated verification, manual browser walkthrough, and Codex handoff are recorded.

## Phase C — Deterministic Generation CLI Skeleton

Create Python/Pydantic package mirrors, mock model/discovery providers, persisted workflow state, CLI generate/resume/inspect, validation, and JSON/report output. Output: a mock Concert of Europe request produces a valid package rendered by the frontend. No live external calls.

## Phase D — Map-First Investigation Experience

Inserted 2026-08-04, ahead of the original Phase D (renumbered to Phase E, cascading through Phase L below), per `docs/decisions/ADR-002-map-first-workspace.md` and the source instructions preserved at `docs/product/map-first-workspace-instructions.md`. Turns the current article-first single-scene renderer into a map-first workspace: a persistent bounded historical map as the primary canvas, a docked/resizable (desktop) or bottom-sheet (mobile) assistant panel (Ask/Explore/Evidence/Sources tabs) beside it, historical "lenses" (Sequence/Positions/Knowledge/Systems/Sources/Uncertainty) driving what the map and timeline show, a new `InvestigationExperiencePlan` contract (Zod/Pydantic parity, additive/optional field), and an "Inspector" mode that preserves the current narrative/evidence/numbered-graph renderer rather than deleting it. Sequenced as sub-plans D0.1 (docs/ADR) → D0.2 (experience-plan contract) → D0.3 (workspace shell) → D0.4 (deterministic Concert of Europe experience plan through the existing curated pipeline) → D0.5 (initial Ask entry-surface prototype) → D0.6 (usability-gate test plan), each approved individually. Output: the Concert of Europe and Blank Cheque packages both render through the same generic map-first workspace, with the current article-first view still reachable as Inspector. No live search, live model calls, downloads, embeddings, or automatic map discovery in any D0 sub-plan.

## Phase E — Real LLM Agent Core

Replaces the former Phase E ("Real Discovery and Assessment") 2026-08-05, per `docs/decisions/ADR-003-llm-agent-system-is-product-core.md` and the source instructions preserved at `docs/ai-core-instructions/`. Corrects Chronicle's product framing: the domain-specialized LLM/multi-agent system is the product core, and the historical domain (existing curated investigations, reframed as benchmark corpora) is its proving ground, not the other way around. Build a real, evaluated, tool-using four-agent workflow (Investigation Planner → Evidence Analyst → Historical Critic → Investigation Guide) over the existing corpora — the first phase in this project to make real model calls (a local, open-weight model via Ollama, per `AGENTS.md` §5's no-paid-infrastructure constraint). Sequenced as sub-plans E0 (reconcile repository state, reorient documentation, checkpoint commit) → E1 (model-provider protocol + deterministic test provider + `OllamaProvider`) → E2 (corpus service + typed tools over existing packages) → E3 (Planner + Analyst) → E4 (Critic + Guide) → E5 (FastAPI + streaming agent runs) → E6 (real Ask-panel integration, replacing the disclosed placeholder) → E7 (evaluation harness comparing the 4-agent workflow against single-prompt/basic-RAG baselines) → E8 (domain-generalization: a second small benchmark corpus, no-topic-branching checks) → E9 (`docs/ai/` learning documentation), each approved individually. Output: a user question inside an existing investigation gets a cited, critic-verified answer with typed map actions, evaluated across at least two materially different corpora. No unrestricted live web research, production vector database, or fine-tuning in Phase E.

## Phase F — Autonomous Source Discovery

Absorbs the former Phase E's content ("Real Discovery and Assessment": provider protocols, selected scholarly/archive adapters, query provenance, candidate registry, deterministic dedupe, assessment rubric, rights metadata, accepted/rejected/deferred reports), resequenced behind the AI core instead of ahead of it. Output: a bounded request produces a traceable candidate corpus that Phase E's Planner/Analyst can retrieve against live, not only the fixed existing packages. No snippet-as-evidence.

## Phase G — Document Acquisition and RAG Corpus

Absorbs the former Phase F's content ("Acquisition and Corpus Retrieval": rights-respecting HTML/PDF/OCR/IIIF acquisition, immutable originals, hashes, page mappings, stable passages, lexical retrieval), plus embeddings, hybrid search, and reranking once justified. Output: a searchable passage corpus with stable citations and resumable failures, feeding the same corpus-service interface Phase E's tools already use.

## Phase H — Historical Model Generation

Generate actors, events, dates, decisions, communications, claims, knowledge states, timelines, and relationship proposals from the Phase F/G corpus — the AI-system-driven successor to the former Phase G/H's typed-extraction and critic/conclusion work, now expressed as agent-generated proposals passing through the same Historical Critic architecture Phase E establishes, not a separate extraction pipeline.

## Phase I — Chronicle Task Model Experiment

Create a reviewed dataset from Phase E's evaluation traces and fine-tune a small open-weight model for one bounded historical-reasoning task (e.g. claim–evidence classification, unsupported-claim detection, relationship classification). Do not fine-tune the entire assistant.

## Phase J — AI Geographic and Experience Composer

Generate map scope, lenses, routes, story sequences, system paths, and `InvestigationExperiencePlan` content via the AI system itself, closing the loop D0.4 opened by hand-writing one curated provider's experience-plan stage — the successor to the former Phase I/J's geographic-generation and generation-first-UX work.

## Phase K — Full Autonomous Investigation

A new topic proceeds from search through corpus construction, historical modelling, map generation, assistant interaction, review, and publication — the full pipeline Phases E-J built, run end to end without hand-curation. The former Phase K/L content (grounded-assistant question classes, private source enrichment/`ImpactReview`) is treated as superseded by this phase's broader scope rather than individually remapped; revisit if a narrower private-enrichment slice is needed sooner than Phase K.

## Cross-Phase Gates

Every phase requires deterministic mocks, automated tests, a manual flow, failure/partial states, provenance preservation, rights/visibility checks where relevant, delivery-doc updates, and a Codex handoff. Live providers cannot precede the mock package pipeline. Domain expansion requires the gate in `supported-domain-strategy.md`.
