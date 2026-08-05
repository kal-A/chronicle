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

## Phase E — Real Discovery and Assessment

Implement provider protocols, selected scholarly/archive adapters, query provenance, candidate registry, deterministic dedupe, assessment rubric, rights metadata, and accepted/rejected/deferred reports. Output: a bounded request produces a traceable candidate corpus. No snippet-as-evidence.

## Phase F — Acquisition and Corpus Retrieval

Implement rights-respecting HTML/PDF/OCR/IIIF acquisition, immutable originals, hashes, page mappings, stable passages, lexical retrieval, then embeddings and diversity controls when justified. Output: searchable passage corpus with stable citations and resumable failures.

## Phase G — Extraction, Entity Resolution, and Timeline

Implement typed extraction, aliases, date/time roles, communications, claims, places, event relevance, timeline and knowledge-state foundations, using deterministic fixtures/evals. Output: evidence-backed structured investigation draft.

## Phase H — Relationships, Critic, and Conclusions

Implement mechanism proposals, evidence ledgers, counterevidence, alternatives, adversarial critic, qualitative conclusion classes, and abstention. Output: explainable qualified relationships with measured overstatement/rejection rates.

## Phase I — Geographic and Map Generation

Implement historical place resolution, map candidate registry, rights/period/georeference checks, typed MapScenes, and geographic verification. Output: evidence-backed interactive map specifications, with honest fallback when assets are unsuitable.

## Phase J — Generation-First UX

Build request, scope approval, visible workflow, candidate-source inspection, progressive investigation canvas, coverage/limitations report, resume/failure UX, and responsive accessibility. Output: user submits a supported request and receives/inspects a generated draft.

## Phase K — Grounded Assistant

Implement typed tools, query planning, evidence comparisons, knowledge-state/dispute/gap questions, verified citations, and typed UI actions. Output: four polished grounded question classes.

## Phase L — Private Source Enrichment

Implement secure upload/link intake, private processing, effect classification, ImpactReview/NarrativeRevisionProposal, and explicit publication protections. Output: a user sees how a new source may affect an investigation without silent public mutation.

## Cross-Phase Gates

Every phase requires deterministic mocks, automated tests, a manual flow, failure/partial states, provenance preservation, rights/visibility checks where relevant, delivery-doc updates, and a Codex handoff. Live providers cannot precede the mock package pipeline. Domain expansion requires the gate in `supported-domain-strategy.md`.
