# Revised AI-First Development Phases

This roadmap supersedes `development-phases.md` for active sequencing. The older roadmap remains historical context until reconciled/archived.

## Phase A — Freeze, Audit, and Salvage

Freeze manual scene expansion; inventory reusable code and hard-coding; preserve passing tests; define the Blank Cheque golden-fixture migration. Output: `current-prototype-salvage.md` and approved pivot architecture. Completion: documentation is internally consistent and current tests are baselined.

## Phase B — Generated-Investigation Contract and Generic Renderer

Define Zod `GeneratedInvestigation`/report/map/interaction schemas, version strategy, JSON golden fixture, generic loader, normalized frontend store, and package-driven route. Output: current UI renders the golden JSON with no July Crisis imports in generic renderer/provider code. Tests: package schema/references/version failures plus preserved UI/E2E behavior.

**Status (2026-08-03):** Complete. Contract, golden fixture, generic renderer, automated verification, manual browser walkthrough, and Codex handoff are recorded.

## Phase C — Deterministic Generation CLI Skeleton

Create Python/Pydantic package mirrors, mock model/discovery providers, persisted workflow state, CLI generate/resume/inspect, validation, and JSON/report output. Output: a mock Concert of Europe request produces a valid package rendered by the frontend. No live external calls.

## Phase D — Real Discovery and Assessment

Implement provider protocols, selected scholarly/archive adapters, query provenance, candidate registry, deterministic dedupe, assessment rubric, rights metadata, and accepted/rejected/deferred reports. Output: a bounded request produces a traceable candidate corpus. No snippet-as-evidence.

## Phase E — Acquisition and Corpus Retrieval

Implement rights-respecting HTML/PDF/OCR/IIIF acquisition, immutable originals, hashes, page mappings, stable passages, lexical retrieval, then embeddings and diversity controls when justified. Output: searchable passage corpus with stable citations and resumable failures.

## Phase F — Extraction, Entity Resolution, and Timeline

Implement typed extraction, aliases, date/time roles, communications, claims, places, event relevance, timeline and knowledge-state foundations, using deterministic fixtures/evals. Output: evidence-backed structured investigation draft.

## Phase G — Relationships, Critic, and Conclusions

Implement mechanism proposals, evidence ledgers, counterevidence, alternatives, adversarial critic, qualitative conclusion classes, and abstention. Output: explainable qualified relationships with measured overstatement/rejection rates.

## Phase H — Geographic and Map Generation

Implement historical place resolution, map candidate registry, rights/period/georeference checks, typed MapScenes, and geographic verification. Output: evidence-backed interactive map specifications, with honest fallback when assets are unsuitable.

## Phase I — Generation-First UX

Build request, scope approval, visible workflow, candidate-source inspection, progressive investigation canvas, coverage/limitations report, resume/failure UX, and responsive accessibility. Output: user submits a supported request and receives/inspects a generated draft.

## Phase J — Grounded Assistant

Implement typed tools, query planning, evidence comparisons, knowledge-state/dispute/gap questions, verified citations, and typed UI actions. Output: four polished grounded question classes.

## Phase K — Private Source Enrichment

Implement secure upload/link intake, private processing, effect classification, ImpactReview/NarrativeRevisionProposal, and explicit publication protections. Output: a user sees how a new source may affect an investigation without silent public mutation.

## Cross-Phase Gates

Every phase requires deterministic mocks, automated tests, a manual flow, failure/partial states, provenance preservation, rights/visibility checks where relevant, delivery-doc updates, and a Codex handoff. Live providers cannot precede the mock package pipeline. Domain expansion requires the gate in `supported-domain-strategy.md`.
