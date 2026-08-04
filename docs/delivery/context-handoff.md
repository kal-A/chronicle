# Chronicle Context Handoff

> **Pre-pivot historical handoff.** For current direction read `docs/product/ai-first-product-definition.md`, `docs/delivery/current-prototype-salvage.md`, `docs/delivery/revised-development-phases.md`, and `plans/current-phase.md`.

## Current State

Chronicle remains pre-implementation. No application code, dependencies, database, tests, commits, or pushes have been created.

The repository contains a product, historical-research, architecture, design, delivery, and planning foundation. All repository files are currently untracked because the repository has no initial commit.

The active state is documented in `plans/current-phase.md`.

## Product Direction

Chronicle is an interactive historical systems atlas combining:

- Guided narrative
- Timeline
- Historical map
- Focused relationship graph
- Evidence explorer
- Evidence-grounded investigation assistant

Chronicle Explore is built before Chronicle Studio. The first investigation is the July Crisis of 1914.

The first implementation will be frontend-only and will validate the synchronized exploration experience before any backend, database, authentication, upload workflow, or live AI is built.

## Initial Repository Review

The entire repository structure and relevant documentation were reviewed using `.codex/phase-review-prompts.md`.

The review identified these original blockers:

- Phase 0 historical content was incomplete.
- Review/publication states contradicted each other.
- The domain model did not fully define Source or passage-level evidence associations.
- Private/public visibility inheritance was unclear.
- Phase 1 lacked measurable user-validation criteria.
- Narrative enrichment from future evidence was not structurally defined.
- Several cross-references and roadmap boundaries were inconsistent.

## Architecture Changes

The domain architecture was expanded and reconciled.

### Review and Publication Model

Canonical review statuses are:

- `proposed`
- `reviewed`
- `disputed`
- `rejected`

Clarifications:

- `accepted` is an action that transitions a proposal to `reviewed`.
- `revised` is an operation that creates a new immutable revision, not a status.
- `disputed` content may appear publicly only after human review and must retain its label and rationale.
- Public records must be `reviewed` or `disputed`, publicly visible, and attached to a published presentation.
- Public endpoint handlers use a deny-by-default repository interface rather than optional endpoint-level filters.

### Source and Evidence Model

The architecture now distinguishes:

- `Source`: global bibliographic identity.
- `Document`: a particular scan, edition, transcription, translation, or uploaded representation.
- `Passage`: an exact evidence span.
- `Claim`: a historical assertion.
- `Relationship`: a classified relationship between historical records.
- `EvidenceLink`: connects a Claim or Relationship to a Passage as supporting evidence, counterevidence, or context.
- `KnownAtTime`: evidence-backed actor/institution awareness.
- `NarrativeBlock`: an evidence-linked, versioned unit of investigation prose.
- `NarrativeRevisionProposal`: a proposed evidence-driven change to narrative text.

Every material Claim must have supporting evidence. Significant relationships retain supporting and opposing evidence, scope, classification, and provenance.

### Visibility

Sources and derived records are not assumed public merely because they were reviewed.

The architecture separates:

- Rights status
- Processing needs
- Review status
- Workspace visibility
- Publication status

A derived record may not become more public than the evidence needed to support it. Promotion to public visibility is explicit and reviewed.

## Source-to-Narrative Enrichment

The canonical contract is `docs/architecture/source-to-narrative-enrichment.md`.

It guarantees that sources can be added for any historical period, including periods with no existing Chronicle investigation.

The workflow is:

```text
Add source
→ acquire document and passages
→ extract evidence/claim proposals
→ human evidence review
→ find potentially affected investigations
→ create ImpactReviews
→ propose narrative revisions
→ human reviews text diff
→ explicitly publish a new presentation version
```

New evidence may be classified as:

- Supporting
- Contradicting
- Contextual
- Qualifying
- Duplicate
- Unrelated

Important invariants:

- A Source can exist without an Investigation.
- Ingestion never changes published narrative text.
- New evidence can add context, corrections, qualifications, or competing accounts.
- Conflicting accounts remain parallel and attributed.
- Narrative is composed from versioned `NarrativeBlock` records.
- Material narrative statements link to reviewed Claims, Relationships, or KnownAtTime records.
- AI-generated narrative is always a proposal.
- Accepting a proposal creates a draft revision.
- A separate human action publishes the new presentation atomically.
- Old narrative versions and rejected proposals are retained.
- If evidence becomes private or unavailable, dependent content is flagged for review rather than silently erased.

## Historical Review Standard

A formal content review protocol exists in `docs/research/review-standard.md`.

It replaces the earlier simplistic rule of “one primary source or two secondary sources.”

The new standard evaluates:

- Passage-level traceability
- Source edition and translation
- Source limitations
- Temporal distinctions
- Geographic scope and precision
- Direct versus inferred status
- Evidence classification
- Counterevidence
- Source independence
- Actor-knowledge support
- Rights and visibility
- Reviewer identity, timestamp, and notes

A primary source can establish that its author made a statement without automatically proving that statement true, sincere, representative, received, or causally decisive.

During solo development, Kamal may perform owner review, but Chronicle must disclose that this is not independent domain-expert review.

## Historical Research Draft

A 20-source initial register exists at `docs/research/july-crisis-source-register.md`.

It includes:

- Austro-Hungarian and German diplomatic documents
- The German “blank cheque” report
- Ultimatum-planning correspondence
- Moltke’s 29 July memorandum
- The Austro-Hungarian ultimatum and Serbian reply
- The declaration-of-war telegram
- British diplomatic correspondence
- US diplomatic records
- German, Austro-Hungarian, Serbian, and Russian documentary collections
- Specialist works by Otte, Clark, Mombauer, Fischer, Williamson, McMeekin, MacMillan, and others

Every entry records intended evidentiary use and limitations. Entries are honestly marked as identified, acquired, or curated. None has been falsely marked historically reviewed.

Remaining research gaps include:

- Exact passage extraction
- Edition/translation verification
- Stronger French and Russian internal records
- More Sarajevo/Serbian primary evidence
- Contrasting specialist passages for the first scene’s causal interpretation

## Phase 1 Scene Outline

A four-scene outline exists at `docs/research/phase-1-scene-outline.md`.

The scenes are:

1. Sarajevo: event, reporting, and initial awareness.
2. Vienna and Berlin: the “blank cheque.”
3. The ultimatum and Serbian reply.
4. From local war to general European war.

Each scene specifies:

- Time range
- Places and precision
- Actors
- Central decision
- Temporal/awareness behavior
- Disputed relationship
- Initial source coverage

Scene 2, the “blank cheque,” was selected as the first vertical slice because it provides:

- Two-capital geography
- Direct diplomatic evidence
- Sent/received/report-time distinctions
- Actor-awareness questions
- A compact graph
- A genuinely disputed causal interpretation

Before Scene 2 content is implemented, the content gate requires:

- Exact passages from `jc-src-001` and `jc-src-002`.
- Two contrasting specialist interpretations.
- Edition, translation, and locator metadata.
- Evidence links and limitations.
- Owner-review notes.

## Historical Date and Map Contracts

The frontend focus model uses a serializable `HistoricalDate` structure rather than JavaScript `Date` objects.

It supports:

- Exact
- Approximate
- Range
- Disputed

Each value carries earliest/latest bounds and can be persisted deterministically in URLs.

The Phase 1 map must use:

- City-level precision
- Period-accurate place naming
- A border-suppressed or explicitly labelled orientation base
- No modern political boundaries presented as historical geography
- No building-level pins from city-level evidence

## Phase 1 Validation Plan

The validation plan is `docs/delivery/phase-1-validation-plan.md`.

### Gate 1

Build one scene and test it with at least five non-contributor target users.

Tasks cover:

- Understanding the scene’s central decision
- Identifying location and time
- Opening evidence
- Distinguishing documentary fact from causal interpretation
- Using cross-facet selection
- Navigating backward
- Finding uncertainty or limitations

Proceed only if at least four of five participants:

- Complete the core evidence tasks without intervention.
- Distinguish documentary fact from disputed interpretation.
- Successfully use and understand synchronized focus.

Any design that makes users more certain than the evidence allows is a blocking defect.

### Gate 2

After Gate 1 passes, expand to four scenes and test with at least five additional participants.

Phase 2 begins only after a dated validation report records a `proceed` decision.

## Phase 1 Implementation Plan

The executable plan is `plans/phase-1-static-prototype.md`.

The plan is divided into:

1. Historical content fixture gate.
2. React/Vite walking skeleton and quality harness.
3. Runtime-validated domain contract and static provider.
4. Central focus and URL synchronization.
5. One-scene narrative/timeline/map/graph/evidence experience.
6. Accessibility and Gate 1 testing.
7. Conditional four-scene and mocked-assistant expansion.

Planned technologies:

- React
- TypeScript
- Vite
- Tailwind CSS
- React Router
- TanStack Query with a static asynchronous provider
- MapLibre GL JS
- Cytoscape.js
- Vitest
- React Testing Library
- axe-core
- Playwright
- npm

Phase 1 explicitly excludes:

- Backend
- Database
- Authentication
- Source-upload UI
- Live AI
- Vector database
- Political-border polygons
- Phase 2+ infrastructure

## Phase 2+ Requirements

Phase 2 must implement and test:

- Global Sources that do not require Investigation foreign keys.
- Source/Document/Passage persistence.
- Evidence-linked NarrativeBlocks.
- Immutable narrative revisions.
- Public visibility filtering.
- Persistence of a source unrelated to any existing investigation.

Later phases will add:

- Global source-library intake.
- Extraction and evidence review.
- Cross-investigation ImpactReviews.
- NarrativeRevisionProposals.
- Explicit versioned publication and rollback.

## Major Files Updated or Added

- `docs/architecture/domain-model.md`
- `docs/architecture/provenance-and-review.md`
- `docs/architecture/backend-architecture.md`
- `docs/architecture/system-overview.md`
- `docs/architecture/spatial-architecture.md`
- `docs/architecture/frontend-architecture.md`
- `docs/architecture/source-to-narrative-enrichment.md`
- `docs/product/shared-evidence-network.md`
- `docs/delivery/development-phases.md`
- `docs/delivery/definition-of-done.md`
- `docs/delivery/phase-0-product-foundation.md`
- `docs/delivery/phase-1-static-prototype.md`
- `docs/delivery/phase-1-validation-plan.md`
- `docs/research/review-standard.md`
- `docs/research/july-crisis-source-register.md`
- `docs/research/phase-1-scene-outline.md`
- `plans/current-phase.md`
- `plans/phase-1-static-prototype.md`
- `plans/completed/README.md`

## Verification Performed

- All local Markdown links resolve.
- Source register contains 20 entries.
- Scene outline contains four scenes.
- Duplicate source IDs were not found.
- Contradictory review-status terminology was removed.
- Incorrect section references were corrected.
- Phase 1 acceptance criteria cover URL state, evidence traceability, uncertainty, precision, accessibility, failure states, and user-validation gates.

## Current Approval Gate

Before application code begins, Kamal should approve or revise:

1. `docs/research/review-standard.md`.
2. `docs/research/phase-1-scene-outline.md` and the selection of Scene 2.
3. `docs/delivery/phase-1-validation-plan.md`.
4. `plans/phase-1-static-prototype.md`.

After approval, execute Plan 0 and Plans 1–5 through the one-scene Gate 1 checkpoint.

Do not commit or push without separate, explicit approval.
