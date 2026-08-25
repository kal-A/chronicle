<!-- generated-by: gsd-doc-writer -->

# Chronicle Product Requirements

**Document purpose:** technical product handoff for a software engineer joining Chronicle
**Repository:** [github.com/kal-A/chronicle](https://github.com/kal-A/chronicle)
**Current branch at time of writing:** `phase-e-ai-core`
**Status represented:** Phase E6 is implemented as a working local vertical slice; Phase E7 is planned but not implemented
**Last code/document review for this PRD:** 2026-08-24

## 1. Executive Summary

Chronicle is an AI-powered historical investigation generator and interactive systems atlas. A user should be able to begin with a historical question, approve a bounded scope, and receive a versioned draft investigation that can be explored through a synchronized map, timeline, evidence ledger, relationship view, source inspector, and evidence-grounded assistant.

The core product is not the current July Crisis or Concert of Europe content. It is the bounded and auditable system that can turn a question and a source corpus into a navigable historical model without presenting model output as historical truth. The two existing investigations are benchmark packages and renderer fixtures used to build and test that system.

Chronicle currently has a meaningful local vertical slice:

- A React/TypeScript map-first Explore interface and animated Ask landing page.
- A versioned `GeneratedInvestigation` package contract implemented in TypeScript/Zod and Python/Pydantic.
- Two registered package-backed corpora: Blank Cheque/July Crisis and Concert of Europe.
- A Python/FastAPI assistant runtime using four bounded agent roles, ten deterministic typed retrieval tools, file-backed resumable run records, polling, and server-sent progress events.
- A provider abstraction with deterministic tests and a real local Ollama integration using `qwen2.5:7b-instruct`.
- A live in-investigation Ask panel that can return a cited result when the evidence is sufficiently constrained and abstain when verification fails.

Chronicle is not yet a general historical search engine. The landing page routes questions to one of two existing packages through keyword overlap. The assistant cannot search the internet, library catalogues, scholarly databases, archives, or user-uploaded documents. There is no production database, authentication, hosted deployment, editorial Studio, review service, or autonomous new-topic investigation pipeline. These are planned later phases, not hidden capabilities.

The immediate engineering priority is Phase E7: measure whether the four-agent workflow improves semantic accuracy, citation validity, abstention quality, and usefulness enough to justify its latency and complexity compared with single-prompt and basic-RAG baselines.

## 2. Product Status Vocabulary

This document uses three explicit labels:

| Label | Meaning |
|---|---|
| **Implemented** | Present in the current working tree and backed by code/tests or a recorded local manual run. |
| **Planned** | Approved target behavior or architecture that is not yet implemented. |
| **Excluded** | Deliberately outside the current phase or product boundary. |

Unless a requirement says otherwise, product requirements describe the intended product, while the status column states whether the current implementation satisfies them.

## 3. Problem and Opportunity

### 3.1 Problem

Historical understanding is poorly served by the common choices available to a reader:

- Static articles and timelines present one linear account but obscure evidence chains, disagreement, uncertainty, actor knowledge, and systemic relationships.
- Search engines return disconnected documents and snippets rather than a durable investigation.
- General-purpose chatbots are flexible but can invent facts, citations, causal relationships, and false certainty.
- Specialist research workflows provide depth but require substantial expertise, time, archive access, and manual organization.
- Maps and relationship graphs often look authoritative even when their geography, chronology, or causal edges are unsupported.

### 3.2 Opportunity

Chronicle can occupy the gap between static-but-trustworthy history and flexible-but-unreliable AI. Its differentiator is a durable, navigable investigation model whose claims, relationships, time roles, and geographic representations can be traced to evidence and challenged by the user.

The experience should support both structured research and curiosity-driven rabbit holes. A user should be able to start simply, then progressively inspect where an answer came from, what is disputed, what an actor knew at the time, and what remains unknown.

## 4. Users, Personas, and Jobs to Be Done

### 4.1 Primary: curious history readers

People who want more depth than a summary article without first learning archival research tooling.

Jobs:

- Help me turn a broad historical curiosity into a bounded question.
- Show me the main sequence, actors, places, pressures, and disagreements without losing context.
- Let me follow an interesting connection into a deeper rabbit hole.
- Tell me what is supported, disputed, or missing.

### 4.2 Secondary: students and serious enthusiasts

People who want to interrogate specific claims, compare accounts, reconstruct actor knowledge, and trace evidence.

Jobs:

- Show the sources and passages behind an interpretation.
- Compare how two actors, institutions, or historians describe the same event.
- Distinguish what happened from what was reported, received, discovered, or interpreted later.
- Help me find the next productive question without inventing an answer.

### 4.3 Advanced future audience: historians and trusted editors

Professional historians are an important direction, but the present MVP does not claim to replace professional archival, historiographical, collaborative, citation-management, or publication workflows.

Future jobs:

- Add sources and inspect their possible impact on existing claims.
- Review, revise, dispute, reject, and publish AI-proposed records.
- Preserve immutable revisions and source provenance.
- Maintain a shared evidence network across investigations.

These are primarily Chronicle Studio requirements and are **planned**, not implemented.

### 4.4 Portfolio and engineering audience

Chronicle also needs to demonstrate sound product judgment, frontend craft, full-stack architecture, AI evaluation, and historical-domain rigor. This is not a user persona for the product, but it affects the standard for documentation, testing, disclosure, and visual quality.

## 5. Product Positioning and Principles

### 5.1 Positioning

Chronicle is:

- An investigation generator and inspection environment.
- Map-first, evidence-first, and systems-aware.
- Conversational at entry, but not chat-only.
- AI-assisted, but deterministic and human review gates retain authority.
- Period- and region-agnostic in product identity, while intentionally narrow in initial reliable coverage.

Chronicle is not:

- A generic history chatbot.
- A Wikipedia replacement.
- An autonomous historian.
- A single-prompt research agent.
- An unrestricted web scraper.
- A graph visualization demo.
- A strategy game or alternate-history simulator.
- A professional archival or publication platform in its current form.

### 5.2 Product principles

1. Begin with curiosity and reward depth.
2. Make evidence, disagreement, uncertainty, omissions, and limitations inspectable.
3. Let geography and time clarify an investigation without implying unsupported precision.
4. Keep model work bounded, typed, auditable, resumable, and subordinate to deterministic gates.
5. Treat partial results and abstention as valid outcomes.
6. Use progressive disclosure so a newcomer can begin immediately and a serious reader can keep drilling down.
7. The map is the primary investigation canvas; the assistant is the guide and control surface; Inspector establishes trust.
8. Prefer one coherent interaction system over duplicate maps, graphs, or parallel state models.
9. Do not add an LLM where deterministic software is sufficient.
10. Prefer a narrow, credible, polished product to broad but unsupported historical coverage.

## 6. Product Scope

### 6.1 Current demonstrable slice

The current product can demonstrate:

- An atmospheric Ask landing surface with an authored coastline draw and typed hero sequence.
- Scope/progress presentation and transition into a registered investigation package.
- Two package-backed investigations rendered through the same generic route and contract.
- A map-first desktop workspace with mobile bottom-sheet behavior, timeline, lenses, Ask/Explore/Evidence/Sources tabs, and Inspector mode.
- Synchronized URL-backed focus across selected event, place, timeline, evidence, and map state.
- A real local in-investigation assistant using the current package corpus.
- Cited answers, limitations, tool activity, typed map actions, recovery/resume presentation, and safe abstention.
- Deterministic mock/provider tests that do not require Ollama.

### 6.2 Near-term MVP

The near-term MVP is the smallest credible experience proving the product thesis:

1. A user asks a question within a supported domain or opens a supported investigation.
2. Chronicle proposes and displays a bounded scope.
3. The system retrieves eligible evidence from a traceable corpus.
4. The assistant returns a useful cited answer or an explicit abstention.
5. The user can inspect evidence, move through time and geography, follow a relationship, and understand limitations without losing context.
6. The same generic contracts work across materially different corpora without topic-specific application branches.
7. Evaluation demonstrates that the chosen agent workflow provides a measurable safety/usefulness advantage that justifies its cost and latency.

### 6.3 Full product target

The later target extends the MVP to:

- Bounded source discovery across selected scholarly, archive, library, and institutional providers.
- Rights-respecting acquisition and stable page/passage citations.
- Hybrid retrieval over a growing corpus.
- Historical entity/event/claim/relationship/knowledge-state generation.
- Period-appropriate geography and generated experience plans.
- Human review, source-impact review, immutable revisioning, and publication.
- A new topic proceeding end to end without hand-curated package construction.

### 6.4 Explicit exclusions from the current implementation

- Live internet research or arbitrary browsing.
- JSTOR, Google Books, archive, library, Crossref, OpenAlex, Internet Archive, Europeana, Wikidata, or similar production adapters.
- PDF/HTML/IIIF acquisition, OCR, embeddings, reranking, or vector search.
- PostgreSQL, pgvector, PostGIS, SQLAlchemy, Alembic, or production job queues.
- Authentication, accounts, organizations, billing, or collaboration.
- Chronicle Studio authoring/review UI.
- Public publishing and production hosting.
- Fine-tuning.
- Automatic historical-boundary or map-asset generation.
- Universal reliable generation across all periods, languages, and regions.

## 7. End-to-End User Journeys

### 7.1 Journey A: begin an investigation

**Target flow**

```text
Ask question
→ clarify/interpret request
→ review bounded scope
→ approve or edit scope
→ visible source and generation workflow
→ verified/partial/failed outcome
→ map-first investigation opens
→ original question persists in Ask panel
```

**Current reality:** the landing experience and transition exist, but package selection is deterministic keyword matching against only two registered investigations. It does not create a new investigation or search external sources.

### 7.2 Journey B: ask within an investigation

```text
Ask question with current map/time/lens/selection context
→ Planner selects one eligible typed tool call
→ deterministic tool retrieves bounded package evidence
→ Analyst proposes evidence-grounded statements
→ Critic accepts, downgrades, rejects, requests one bounded retry, or abstains
→ Guide composes only approved material
→ deterministic final validation checks citations and action IDs
→ answer, limitations, citations, and safe UI actions appear
```

This is **implemented locally** for the two package-backed corpora.

### 7.3 Journey C: inspect and challenge an answer

The user opens a cited record, passage, source, event, location, or relationship. The map, timeline, evidence panel, and URL focus should update from the same state. The user can see whether a statement is direct, inferred, disputed, contextual, contradicted, or unsupported.

This is **partially implemented**. Core focus synchronization and evidence views exist; richer answer-to-source deep links and durable conversation state across reloads remain E6 closure work.

### 7.4 Journey D: move through historical time and space

The user scrubs a curated historical sequence. Events at or before the selected position appear, later events disappear, and the active event highlights its documented place. The evidence panel updates from the same focus. The map does not infer routes, boundaries, or precision that are absent from the package.

This is **implemented for the fixture experience plans**, not automatically generated for arbitrary investigations.

### 7.5 Journey E: add a new source

**Planned flow**

```text
Submit URL/file/catalogue record
→ validate type, access, rights, and provenance
→ preserve immutable original and citation map
→ segment/index passages
→ propose claims/entities/relationships
→ human review
→ impact review against existing investigations
→ explicit revision and publication decision
```

No part of this should silently rewrite an existing public investigation. This journey is **not implemented**.

## 8. Functional Requirements

Priority meanings: **P0** is required for a credible MVP; **P1** is required for the next complete product stage; **P2** is valuable but deferrable.

### 8.1 Entry, scope, and investigations

| ID | Priority | Requirement | Current status |
|---|---:|---|---|
| `CHR-ENTRY-001` | P0 | The first page shall provide one clear historical-question input without requiring an account. | Implemented. |
| `CHR-ENTRY-002` | P0 | Chronicle shall preserve the submitted question as the investigation opens and make it available to the contextual assistant. | Implemented for the current package transition. |
| `CHR-ENTRY-003` | P0 | Before unrestricted research begins, Chronicle shall show interpreted dates, geography, actors, themes, inclusions, exclusions, ambiguities, and expected outputs for approval or correction. | UI concept implemented; real general-purpose scope planning remains planned. |
| `CHR-ENTRY-004` | P0 | Broad, ambiguous, unsupported, or weakly sourced requests shall require clarification, narrow scope, produce a partial result, or abstain. | Implemented in assistant safety paths; not implemented for live new-topic generation. |
| `CHR-ENTRY-005` | P1 | A submitted question shall be able to initiate a new investigation rather than only route to a pre-existing package. | Planned for Phases F-K. |
| `CHR-ENTRY-006` | P0 | The UI shall disclose when it is routing to existing curated material rather than generating new research. | Required; current landing behavior must remain honestly presented. |

### 8.2 Explore workspace

| ID | Priority | Requirement | Current status |
|---|---:|---|---|
| `CHR-EXP-001` | P0 | The investigation shall open to a bounded, map-first workspace rather than a whole-world map or article dashboard. | Implemented. |
| `CHR-EXP-002` | P0 | The workspace shall expose Ask, Explore, Evidence, and Sources as coordinated panel modes. | Implemented. |
| `CHR-EXP-003` | P0 | Narrative, timeline, map, relationship/system, source, and evidence views shall use shared focus rather than independent selections. | Implemented in core fixture flows. |
| `CHR-EXP-004` | P0 | The current article/evidence/claim-ledger renderer shall remain available as Inspector mode. | Implemented. |
| `CHR-EXP-005` | P0 | Focus state shall be deep-linkable in the URL where practical. | Implemented for core focus/lens state; assistant-answer deep links remain planned. |
| `CHR-EXP-006` | P0 | Mobile shall use an accessible bottom sheet; desktop shall use a docked research panel. | Implemented. |
| `CHR-EXP-007` | P1 | Users shall be able to resize/collapse the desktop panel and preserve usable focus behavior. | Designed and partly implemented; requires continued usability validation. |
| `CHR-EXP-008` | P1 | The user-facing Systems view shall use readable historical objects and relationship labels, not an unfiltered graph hairball or numbered claims as the main visualization. | Implemented direction; continued scale validation required. |

### 8.3 Assistant and AI workflow

| ID | Priority | Requirement | Current status |
|---|---:|---|---|
| `CHR-AI-001` | P0 | The assistant shall operate only against the active, permitted corpus and supplied workspace context. | Implemented. |
| `CHR-AI-002` | P0 | Model roles shall exchange typed, validated contracts rather than free-form internal state. | Implemented with Pydantic contracts. |
| `CHR-AI-003` | P0 | Tool calls shall be selected from a bounded registry, validate corpus identity and permissions, and record auditable success/failure metadata. | Implemented. |
| `CHR-AI-004` | P0 | Every material answer statement shall resolve to evidence returned by a tool call in that run. | Implemented syntactically/structurally; semantic entailment remains under evaluation. |
| `CHR-AI-005` | P0 | The Critic shall account for every proposed statement and may accept, downgrade, reject, request at most one bounded retrieval retry, or abstain. | Implemented. |
| `CHR-AI-006` | P0 | The Guide shall compose only Critic-approved material and shall not introduce new material claims. | Implemented with deterministic post-validation. |
| `CHR-AI-007` | P0 | Invalid citations, out-of-corpus IDs, unsupported actions, malformed structured output, and budget violations shall be rejected before display. | Implemented. |
| `CHR-AI-008` | P0 | The UI shall expose Scope, Retrieve, Analyze, Verify, and Compose progress without exposing private chain-of-thought. | Implemented. |
| `CHR-AI-009` | P0 | Runs shall support inspection, bounded event replay, safe cancellation boundaries, and resume after a recoverable failure. | Implemented locally through FastAPI and file-backed records. |
| `CHR-AI-010` | P0 | Unsupported questions shall produce a specific limitation or abstention rather than fabricated content. | Implemented, with usefulness still under evaluation. |
| `CHR-AI-011` | P0 | The four-agent workflow shall be retained only if comparative evaluation demonstrates a meaningful advantage over simpler baselines. | Planned Phase E7 gate. |
| `CHR-AI-012` | P1 | Chronicle shall support selected external discovery/acquisition providers through typed adapters without granting the model unrestricted browsing. | Planned Phases F-G. |

### 8.4 Evidence, sources, and review

| ID | Priority | Requirement | Current status |
|---|---:|---|---|
| `CHR-EVID-001` | P0 | Every major claim shall trace through an evidence link to a passage, document, and source. | Enforced by package and assistant contracts for current corpora. |
| `CHR-EVID-002` | P0 | Evidence roles shall distinguish supporting, counterevidence, and context; contextual evidence shall not be promoted to support. | Implemented. |
| `CHR-EVID-003` | P0 | Search metadata and snippets shall be discovery material only and shall never be presented as evidence. | Target rule; external discovery not yet implemented. |
| `CHR-EVID-004` | P0 | The interface shall display relevant source type, locator, visibility, review status, limitations, and citation identity. | Partially implemented; richer source deep-linking remains. |
| `CHR-EVID-005` | P1 | Acquired documents shall preserve original bytes, hashes, page/image boundaries, OCR confidence, and stable passage-to-original mappings. | Planned Phase G. |
| `CHR-EVID-006` | P1 | AI-extracted records shall enter `proposed` status and require the appropriate deterministic and/or human review gate before public use. | Contract/architecture only; Review service not built. |
| `CHR-EVID-007` | P1 | A new source shall create an impact-review proposal rather than silently mutating a published investigation. | Planned Phase K/Studio. |
| `CHR-EVID-008` | P1 | Reviewed/public revisions shall be immutable and retain supersession history. | Planned database/review architecture. |

### 8.5 Typed UI actions

| ID | Priority | Requirement | Current status |
|---|---:|---|---|
| `CHR-ACT-001` | P0 | Assistant actions shall use a closed typed union such as focus event/location, set time/range, activate lens, open evidence/source, show a system path, compare actors, or reset view. | Implemented subset with package validation. |
| `CHR-ACT-002` | P0 | Every referenced action target shall exist in the validated package. | Implemented. |
| `CHR-ACT-003` | P0 | The model shall never emit executable JavaScript or arbitrary map commands. | Implemented architectural boundary. |
| `CHR-ACT-004` | P1 | Every triggered visual action shall be stated textually for non-visual users. | Required; accessibility validation should remain continuous. |

## 9. Historical Integrity and Provenance Requirements

These requirements are non-negotiable because visual polish and fluent prose can otherwise create false authority.

### 9.1 Claims and relationships

- Relationships must be classifiable as directly supported, indirectly supported, contextual, correlational, disputed, speculative, or insufficient evidence.
- Chronological adjacency must never be treated as causation.
- A disputed relationship must preserve disagreement and counterevidence.
- Generated synthesis may use only evidence-backed structured records. It may not introduce new material claims only in prose.
- Model confidence is not evidence and cannot substitute for a validation result.

### 9.2 Provenance

Every AI-originated reviewable record must be able to retain:

- source, document, passage, and evidence-link identities;
- evidence role and source type;
- temporal and geographic scope;
- direct/inferred status where the contract supports it;
- review status and reviewer notes;
- prompt version, provider/model identity, processing timestamp, and stage/run identity;
- immutable revision lineage.

The current assistant persists run/model/tool artifacts to files. The future database/review system is not implemented.

### 9.3 Eligibility and publication

- Proposed, rejected, private, rights-blocked, or metadata-only evidence must not appear as reviewed public fact.
- A partial package must disclose omissions and failed capabilities.
- Publication requires rights/visibility clearance, deterministic verification, appropriate human review, an immutable revision, and a retained limitations report.
- The current packages are development/benchmark fixtures and must not be described as professionally peer-reviewed historical products.

## 10. Spatial and Cartographic Requirements

### 10.1 Map scope

Each investigation requires a validated `MapScope` containing bounds, focus/context regions, initial viewport, represented period, geographic rationale, unavailable historical boundaries, and limitations. The map must show only geography needed to understand the investigation plus enough context for orientation.

### 10.2 Historical geography

- Modern political borders must not masquerade as historical borders.
- Period boundaries may render only when sourced historical geometry exists.
- Otherwise use neutral or border-suppressed orientation geography and disclose the limitation.
- Historical names must resolve from period-valid place records; modern names may appear only as labelled orientation context.
- Routes, territorial highlights, political control, and labels require evidence and period fit.

### 10.3 Precision

Every location must retain `building`, `city`, `region`, or `approximate` precision. The UI must render that precision honestly. Having exact coordinates does not make the underlying evidence exact.

### 10.4 Map assets and provenance

Map layers must retain represented period, coverage, source citation, rights/license, georeferencing method and quality, attribution, projection/scale when known, and limitations. Neutral coastlines, historical scans, political boundaries, routes, labels, and evidence overlays remain distinct layers.

### 10.5 Interaction

- Map, time, selected record, lens, evidence, and accessible list state must synchronize.
- The homepage-to-investigation particle transition may use only validated destination geometry; it must not invent an intermediate map.
- If a suitable historical layer is unavailable, the UI must use a clearly labelled schematic/list fallback.
- Maximum zoom must respect source resolution and georeferencing quality.

## 11. Temporal Requirements

Chronicle must not collapse all historical time into one `date` field. It must preserve distinct roles when available:

- event time;
- source/report time;
- message sent time;
- message received time;
- actor awareness time;
- discovery time;
- interpretation time.

Date values may be exact, ranged, approximate, or otherwise qualified. Temporal filtering uses interval overlap and explicit time roles. Actor knowledge must never be inferred merely because information existed somewhere.

The current time rail operates on curated `EventRecord` order. Moving backward hides later events; advancing restores them; selecting a time step creates first-class event focus. Automatic generation of these plans remains Phase J work.

## 12. AI and LLM Methodology

### 12.1 Chosen architecture

Chronicle uses four bounded roles over one provider and one validated corpus:

| Role | Responsibility | Deterministic boundary |
|---|---|---|
| Investigation Planner | Interpret the question and select a small valid retrieval plan. | Available tools, record IDs, intent compatibility, budgets, and dependency shape are constrained. |
| Evidence Analyst | Form evidence-grounded structured statements from retrieved records. | Identities, citation tuples, temporal/geographic fields, and evidence classifications are constrained to retrieval output. |
| Historical Critic | Challenge support, directness, relationship strength, counterevidence, temporal roles, actor knowledge, and overclaiming. | Every statement receives an explicit disposition; only one bounded retrieval retry is allowed. |
| Investigation Guide | Present only approved material and propose useful workspace actions. | Answer text, citations, and action targets are revalidated against approved records and the active package. |

The roles execute sequentially through one worker. They do not form an autonomous swarm, negotiate freely, browse independently, or execute code.

### 12.2 Why this design was selected

The product needs to separate four different failure domains:

1. Question interpretation and tool choice.
2. Evidence retrieval and structured historical analysis.
3. Adversarial checking for unsupported or overstated conclusions.
4. User-facing explanation and UI navigation.

Splitting these responsibilities makes intermediate artifacts inspectable, resumable, testable, and replaceable. It also lets deterministic validators operate at each boundary. The system records stage, model, tool, timing, retry, error, abstention, and citation metadata without requesting or storing private chain-of-thought.

This architecture is still a hypothesis. Phase E7 must prove it performs better enough than simpler strategies to justify four sequential model calls.

### 12.3 Alternatives and tradeoffs

| Alternative | Benefit | Reason not selected as the default |
|---|---|---|
| One large prompt | Lowest orchestration complexity and latency. | Hard to audit; mixes planning, evidence use, criticism, and writing; makes fabricated citations and silent overclaiming harder to isolate. Retained as E7 baseline. |
| Basic retrieval-augmented generation | Simpler and faster than four roles; grounded context is available. | Retrieval relevance does not guarantee citation entailment, temporal correctness, counterevidence handling, or safe actions. Retained as E7 baseline. |
| Planner + Analyst only | Adds typed tool choice and grounded structure with fewer calls. | No independent historical criticism or approved-material-only presentation gate. Retained as E7 baseline. |
| Autonomous multi-agent swarm | Flexible and potentially broad. | Unbounded cost, state, tool use, and failure surface; weak auditability; conflicts with the product trust model. Explicitly rejected. |
| Paid frontier hosted model | Better likely structured output, reasoning, and latency. | Violates the no-paid-infrastructure default without a separate approved exception; creates cost/key/vendor/privacy concerns. May be reconsidered if evidence shows local quality is inadequate. |
| Deterministic-only system | Predictable and cheap. | Cannot reliably interpret ambiguous natural language, unstructured historical material, or nuanced comparison. Deterministic software remains authoritative where rules are available. |
| Fine-tune an entire assistant now | Potential domain adaptation. | Premature without reviewed traces, a stable task definition, and comparative evaluation. Phase I is limited to one bounded task. |

### 12.4 Why local Qwen through Ollama

The development machine has approximately 13.69 GB RAM, an AMD Ryzen 5 6600H, and no expected practical GPU acceleration for Ollama on its Windows integrated GPU. This makes a quantized 7-8B model the realistic ceiling.

`qwen2.5:7b-instruct` was selected because it offered the strongest expected structured JSON/schema behavior among the locally viable options considered. One model is reused sequentially across all four roles so the hardware does not need to hold multiple models and so E7 can isolate the value of role separation from model-size differences. `qwen2.5:3b-instruct` remains a configurable fallback for faster development or the lower-reasoning Guide role.

The provider layer is structural and provider-agnostic. `DeterministicModelProvider` drives ordinary tests; `OllamaModelProvider` drives opt-in live tests and local use. A future hosted or fine-tuned provider should satisfy the same protocol.

### 12.5 Known model limitations

- CPU-only four-role inference is slow. Recorded broad E6 runs took several minutes, and current E7 planning assumes roughly seven to nine minutes for some full-workflow questions.
- A 7B model can produce schema-valid but semantically wrong text.
- The current grounding check can verify that cited records contain related material without proving that the answer preserves subject/object directionality or full entailment.
- A real E6 run exposed a support-direction reversal. The Critic ultimately abstained, preventing the candidate from being presented as an answer, but this remains a core evaluation risk.
- The model advertises a 32,768-token architectural context, but the project conservatively treats roughly 8K as the practical working assumption on current hardware until measured otherwise.
- Local inference has no provider bill, but it consumes wall-clock time, memory, electricity, and developer attention.
- Safe abstention can become overly conservative and unhelpful. E7 must measure both safety and usefulness.

## 13. UX/UI Requirements and Design System

### 13.1 Experience direction

The approved visual direction is an illuminated Atlantic atlas: ink-deep navy and Prussian blue, warm bone text, oxidized copper highlights, and restrained registration cyan. It draws interaction inspiration from Europa Universalis/Crusader Kings map systems—time, geography, lenses, and information responding together—without importing game mechanics or alternate-history framing.

### 13.2 Landing page

- The coastline begins absent and is visibly drawn as the hero text types; it is not merely highlighted over an already rendered map.
- Cartographic layers behave like a palimpsest, with slow reveals and typing-responsive masks.
- The question field remains the visual and interaction priority over the map atmosphere.
- After approved scope and completed generation, the atlas may dissolve into particles sampled from validated destination geometry and resolve into the local investigation map.
- Reduced-motion users receive complete text/map content immediately or a short crossfade.
- Generated concept art is art direction only and must never become an authoritative production basemap.

### 13.3 Investigation workspace

- The map owns most of the viewport and is not placed inside a generic dashboard card.
- A compact command bar provides product identity, investigation title, lens control, reset when needed, and Inspector access.
- A persistent research rail retains the question and Ask/Explore/Evidence/Sources modes.
- Timeline/provenance controls remain attached to the map context.
- Evidence is discoverable but does not dominate the default surface.
- Loading, empty, partial, abstained, failed, cancelled, and resumable states must be first-class designs.

### 13.4 Typography and color

The implemented design tokens are recorded in `DESIGN.md`. Primary typography uses Barlow Condensed for display/headline roles and system sans-serif for body/UI text. Warm bone provides primary text, copper indicates actions/emphasis, and cyan is limited to registration/evidence cues rather than becoming the dominant palette.

### 13.5 Accessibility

Target WCAG 2.2 AA. Requirements include:

- Full keyboard operation for tabs, timeline controls, markers, evidence, panel controls, and bottom sheet.
- Screen-reader accessible lists equivalent to every map and graph state.
- Semantic narrative and citation text.
- Focus preservation across panel/lens changes.
- Status, uncertainty, relationship strength, and dispute conveyed with text/pattern/icon, never color alone.
- `prefers-reduced-motion` support and no forced animation.
- 200% zoom, long-label, truncation, and responsive review.
- Assistant responses and triggered UI actions announced textually.

Automated axe-core coverage exists in the frontend test tooling; manual keyboard and screen-reader checks remain part of release acceptance.

## 14. Data and Contract Architecture

### 14.1 `GeneratedInvestigation`

`GeneratedInvestigation` is the versioned interchange boundary between generation and rendering. It is not a database dump. Major groups include:

- request, approved scope, generation status, and report;
- presentation/synthesis and finding references;
- entities, events, decisions, communications, and actor knowledge states;
- claims, relationships, perspectives, conflicts, uncertainty, and research gaps;
- sources, documents, passages, evidence links, and claim ledgers;
- timeline entries, historical map assets/scenes, and investigation scenes;
- interaction specification and optional `InvestigationExperiencePlan`.

The frontend validates packages with Zod; the backend uses matching Pydantic contracts. Unknown major schema versions, broken references, ineligible evidence, unsupported precision, and missing claim/evidence links must fail validation rather than render partially by accident.

### 14.2 Package versioning

- `schemaVersion` follows semantic versioning.
- Additive optional fields are minor changes; removals or semantic changes are major.
- `packageRevision` increases monotonically for an investigation.
- Original packages/revisions remain available for audit.
- Migrations must be pure, tested transformations.

### 14.3 Current corpus

`CorpusRegistry` currently exposes two pinned JSON packages. Each registration pins corpus/package identity, hash, schema version, and package revision. Packages are loaded lazily and returned defensively. Record IDs are corpus-local, so identity is `(corpusId, recordId)`.

Search is deterministic lexical retrieval. It is token-aware, returns stable ranking explanations, preserves evidence/source metadata, applies explicit temporal roles, and enforces result and serialized-output limits. There are no embeddings or database queries.

### 14.4 Typed tools

The current registry contains:

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

Every invocation binds the input, execution context, corpus, and manifest to the same corpus ID; validates Pydantic input/output; applies capability, count, and character limits; and emits a `ToolCallRecord` on success or typed failure.

## 15. API Contract

The current local FastAPI surface is deliberately small:

| Method | Path | Purpose | Implemented |
|---|---|---|---|
| `GET` | `/health` | Local service health. | Yes |
| `GET` | `/api/corpora` | List registered package corpora. | Yes |
| `POST` | `/api/investigations/{investigation_id}/questions` | Submit a question with workspace context and optional conversation summary; returns `202` plus run/event URLs. | Yes |
| `GET` | `/api/agent-runs/{run_id}` | Read the persisted agent run. | Yes |
| `GET` | `/api/agent-runs/{run_id}/events` | Poll events or subscribe through SSE; supports cursors/`Last-Event-ID`. | Yes |
| `POST` | `/api/agent-runs/{run_id}/resume` | Resume an eligible interrupted/failed run from durable artifacts. | Yes |
| `POST` | `/api/agent-runs/{run_id}/cancel` | Request cancellation at a safe workflow boundary. | Yes |

The browser client uses SSE plus polling fallback. The Vite dev server proxies `/api` and `/health` to the local backend. CORS currently permits localhost/127.0.0.1 development origins. There is no authentication or production authorization layer, so this API must not be exposed as a production public service in its present form.

## 16. Technology and Infrastructure

### 16.1 Implemented stack

| Area | Current technology |
|---|---|
| Frontend | React 19, TypeScript 6, Vite 8, React Router 7 |
| Styling | Tailwind CSS 4 tooling plus project CSS/design tokens |
| Client data | TanStack Query is installed; investigation packages and assistant state also use project repositories/hooks |
| Validation | Zod 4 frontend; Pydantic 2 backend |
| Mapping | MapLibre GL JS 5 |
| Graph | Cytoscape.js 3 |
| Backend/API | Python 3.11+, FastAPI, Uvicorn, HTTPX |
| AI runtime | Ollama with `qwen2.5:7b-instruct`; deterministic provider for tests |
| Persistence | Validated JSON fixtures and atomic file-backed agent-run records |
| Frontend tests | Vitest, React Testing Library, Playwright, axe-core |
| Backend tests | pytest; opt-in local-Ollama tests excluded from default runs |
| Lint/type/build | oxlint, TypeScript compiler, Vite build |

### 16.2 Target stack, not currently built

| Area | Target/conditional technology | Adoption condition |
|---|---|---|
| Durable domain storage | PostgreSQL, SQLAlchemy, Alembic | Required when normalized investigations, review, and multi-user data replace package/file-only persistence. |
| Vector retrieval | pgvector or another adapter | Only after Phase G proves embeddings improve retrieval beyond deterministic lexical search. |
| Spatial queries | PostGIS | Only if real historical polygon/temporal-spatial queries justify it; points/simple areas do not. |
| Local orchestration | Docker Compose | When a reproducible database/backend/frontend/Ollama stack is implemented. No compose stack exists now. |
| CI/CD | GitHub Actions | Planned for automated frontend/backend/e2e gates and later deployment. Verify repository workflow state before relying on it. |
| Hosting | Free static/preprocessed demo or justified free-tier backend | Production target is undecided; live local Ollama is not a public hosting solution. |
| Editorial UI | Chronicle Studio | After ingestion, review, revision, and publication services exist. |

No paid infrastructure is required or pre-approved. Any paid provider or hosted dependency requires a written justification and explicit approval.

## 17. Non-Functional Requirements

### 17.1 Correctness and safety

- No unsupported major claim, citation, action target, time role, or location precision may reach the user as valid output.
- All boundary schemas reject unknown or malformed values rather than silently coercing them.
- Package and corpus identity must be pinned and cross-checked.
- Partial/abstained outcomes must preserve useful evidence and a specific limitation when possible.

### 17.2 Performance

- Interactive frontend controls should respond immediately and not wait on model inference.
- The API must expose progress throughout long model runs.
- Cancellation and resume occur only at durable safe boundaries.
- E7 must establish latency targets from measured baselines. The present multi-minute CPU latency is a known product blocker for ordinary hosted use.
- Map/animation work must pause when the page is hidden and respect reduced motion.
- The current production build emits an existing MapLibre bundle-size advisory; bundle splitting/performance should be profiled before public deployment.

### 17.3 Reliability and resumability

- Agent stages must persist sufficient typed artifacts to resume without repeating accepted prior work unnecessarily.
- Atomic writes must withstand transient file replacement failures on Windows.
- Event streams must support replay from a sequence cursor.
- Failure messages shown to users must be bounded and not expose internal traces or sensitive data.

### 17.4 Generalization

- Core renderer, corpus, tools, and orchestration code must not branch on known topic/package names.
- Every capability intended to be generic must be exercised across at least two materially different corpora.
- Adding a new valid package should primarily be data/contract work, not React conditional logic.

### 17.5 Maintainability

- Model providers, discovery providers, corpus backends, and future embedding providers remain behind typed protocols/adapters.
- Prompt versions and schema versions change deliberately, with evaluation before production promotion.
- Tests use deterministic providers by default and never depend on live inference or internet availability.
- Architecture decisions that are expensive to reverse require an ADR.

## 18. Security, Privacy, and Rights

### 18.1 Current security boundary

The current API is a localhost development service with no authentication. It should not be exposed directly to the internet. Ollama is expected at a local loopback URL and requires no API key. Run files may contain user questions and retrieved evidence; they should be treated as local potentially sensitive artifacts.

### 18.2 Required future controls

- Server-side authentication and authorization for private workspaces and Studio.
- Query-layer enforcement of review status and visibility; never trust client role flags.
- Parameterized database access through the chosen ORM/Core layer.
- Input type/size validation and sanitization for files, URLs, OCR text, and extracted content.
- Uploaded/source content treated as untrusted data and never executed as code or prompt instructions.
- Rate limits, quotas, cancellation, and bounded provider/tool budgets before public AI access.
- Audit logs for ingestion, review, revision, publication, and access-sensitive actions.
- Secret loading through ignored environment files or deployment secret managers; no committed keys.
- Rights/access checks kept separate from visibility and processing status.

### 18.3 Privacy posture

The local-first model reduces third-party prompt disclosure, but it does not remove privacy obligations. A hosted version must define retention, deletion, export, telemetry, and model-provider data handling before accepting private sources or personal accounts.

## 19. Success Metrics and Evaluation Gates

### 19.1 Product success metrics

For the MVP, success is not total question volume. It is whether a user can complete a trustworthy investigation loop:

- Begin a question and understand the proposed scope.
- Identify the main supported finding.
- Open the supporting passage/source.
- Use time and geography to understand sequence/context.
- Identify at least one disagreement, uncertainty, or limitation.
- Ask a follow-up without losing investigation context.
- Recognize when Chronicle has insufficient evidence.

Usability gates should measure task completion, time-on-task, navigation errors, comprehension of uncertainty, and whether users confuse a generated draft with reviewed truth.

### 19.2 Phase E7 comparative AI gate

E7 compares four strategies under the same model/corpus/settings:

1. Single prompt.
2. Basic deterministic retrieval plus one answer call.
3. Planner + tools + Analyst.
4. Full Planner + Analyst + Critic + Guide workflow.

The approved benchmark expands the existing 24 cases across both corpora. It measures:

- citation existence, eligibility, and role correctness;
- semantic entailment and subject/relation/object directionality;
- actor-knowledge discipline;
- temporal ordering and time-role preservation;
- counterevidence and disputed-interpretation handling;
- invalid-premise handling;
- abstention recall and false abstention;
- action relevance and target validity;
- usefulness;
- latency, attempts, tokens where reported, provider-billed cost, stability, and failure rate.

Directionality-critical and counterevidence cases require blinded human review and, where specified, a second reviewer/adjudication. The four-agent architecture should be simplified if it does not demonstrate enough safety/usefulness improvement to justify its additional calls and latency.

### 19.3 Release gates

A phase/slice is not done until:

1. Approved scope/assumptions are met.
2. Relevant automated tests pass.
3. A representative manual user flow is completed.
4. Loading, empty, partial, failure, and recovery states exist where applicable.
5. Historical-integrity and cartographic requirements pass.
6. Accessibility equivalents and reduced-motion behavior are verified.
7. Delivery/current-phase documentation is updated.
8. No capability is presented as implemented when it remains target architecture.

## 20. Constraints and Dependencies

### 20.1 Constraints

- Development and demonstration must remain possible with free/open-source infrastructure.
- Current hardware limits local models to roughly 7-8B Q4 and makes sequential inference slow.
- The reliable initial historical domain is intentionally narrower than the universal product identity: European diplomatic/political history, approximately 1814-1914, with selected English-language accessible corpora.
- Historical data validation and source rights are ongoing content work, not one-time engineering tasks.
- The current working tree contains extensive uncommitted changes and tracked deletions; contributors must inspect before editing and must not assume remote GitHub matches the local implementation.
- Commits and pushes require explicit owner approval per repository policy.

### 20.2 Dependencies

- Node/npm for the frontend.
- Python 3.11+ and the backend virtual environment/dependencies.
- Ollama plus the configured Qwen model for live local inference.
- Valid fixture packages for the current corpus.
- MapLibre-compatible geometry/assets and legally usable historical map sources.
- Human historical review for benchmark rubrics, period fit, and eventual publication.

## 21. Risks and Tradeoffs

| Risk | Why it matters | Current mitigation / required decision |
|---|---|---|
| Semantically wrong but lexically grounded answers | A related citation can hide a reversed or overstated claim. | E7 proposition/directionality review; add deterministic/model-assisted entailment gates only if validated. |
| Excessive local latency | Seven-to-nine-minute answers are not viable for ordinary users. | Measure per-stage latency; compare simpler strategies; consider smaller role-specific model, fewer calls, caching, hardware, or approved hosted provider based on evidence. |
| Over-abstention | Safe but consistently unhelpful output fails the product goal. | Score false abstention and usefulness separately from citation safety. |
| Underpowered local model | All strategies may be uniformly weak, making orchestration evaluation inconclusive. | Maintain provider abstraction; compare 3B/7B only where useful; require explicit decision before hosted provider. |
| Hand-curated fixture bias | Success on two packages may not generalize. | E8 formal generalization checks and later domain gates; add corpora as evaluation fixtures, not app branches. |
| Source availability and rights | Full text may be inaccessible or not displayable. | Discovery metadata never becomes evidence; rights and full-text availability are deterministic gates. |
| False geographic authority | Maps create immediate legitimacy concerns when labels, coastlines, boundaries, or scale are wrong. | Cartographic quality gate, period-valid names, sourced geometry, honest precision, omission over invention. |
| Complex UI overwhelms readers | Map, timeline, lenses, evidence, and chat can become a dashboard. | Progressive disclosure, one persistent canvas, one research rail, Inspector for depth, usability testing. |
| File persistence does not scale | Local run files are not sufficient for concurrency, accounts, review, or hosted durability. | Keep it as a local Phase E implementation; design normalized database migration when the next capability requires it. |
| Target/current documentation drift | Existing docs and README may describe older phases. | Treat code plus current phase reports/ADRs as evidence; update docs at every completed slice. |
| Prompt injection from future sources | Historical documents or web pages may contain adversarial instructions. | Treat source text only as untrusted evidence data; models receive bounded typed content; never execute document instructions. |
| Review workload | Historical integrity can bottleneck scaling. | Prioritize high-impact claims, source diversity, and risk-based review; do not imply universal coverage. |
| Scope expansion into professional tooling | Premature Studio/collaboration work can stall the core product. | Finish and evaluate the investigation-generation/assistant loop first. |

## 22. Development Strategy and Phase Hierarchy

The strategy deliberately proves contracts and deterministic behavior before adding live data sources or larger infrastructure.

```text
A. Freeze/audit/salvage
→ B. Versioned package contract + generic renderer
→ C. Deterministic Python generation CLI
→ D. Map-first investigation workspace
→ E. Real local LLM assistant core
   E0 documentation/architecture reconciliation
   E1 model-provider foundation
   E2 package corpus + typed tools
   E3 Planner + Analyst
   E4 Critic + Guide
   E5 FastAPI + streaming/persistence
   E6 live Ask-panel integration
   E7 comparative evaluation
   E8 formal cross-domain/generalization gate
   E9 AI learning documentation
→ F. Bounded source discovery
→ G. Acquisition + RAG corpus
→ H. Historical model generation
→ I. One bounded Chronicle task-model experiment
→ J. AI geographic/experience composer
→ K. End-to-end autonomous investigation + review/publication path
```

### 22.1 Phase status

| Phase | Scope | Status |
|---|---|---|
| A | Freeze manual expansion; audit reusable prototype. | Complete. |
| B | `GeneratedInvestigation` contract, golden fixture, generic package renderer. | Complete. |
| C | Deterministic Python/Pydantic generation pipeline and CLI. | Implemented historically; current working tree includes deleted legacy provider/run-store files, so full legacy verification needs reconciliation. |
| D | Map-first workspace, experience plan, Ask entry prototype, Inspector preservation. | Implemented local product slice. |
| E0-E5 | AI architecture through FastAPI/streaming runtime. | Implemented locally. |
| E6 | Real in-investigation Ask integration. | Working vertical slice; closure items remain. |
| E7 | Comparative evaluation harness. | Approved plan; implementation not started. |
| E8 | Formal generalization/no-topic-branching evaluation. | Planned. Two corpora already exist, but the formal phase gate is not complete. |
| E9 | Consolidated AI learning documentation. | Planned; partial learning logs already exist. |
| F | Selected live discovery providers and candidate assessment. | Planned; no adapters implemented. |
| G | Rights-respecting acquisition, OCR/passage mapping, lexical/hybrid retrieval. | Planned. |
| H | Generate historical model records from the acquired corpus. | Planned. |
| I | Fine-tune/evaluate one bounded task model. | Planned and optional based on evidence. |
| J | Generate map scope, lenses, routes, sequences, and experience plan. | Planned. |
| K | New topic from discovery through reviewed investigation/publication. | Planned long-term target. |

## 23. Pivots and Why They Happened

### 23.1 Explore-first to generation-first

Chronicle began as a manually curated July Crisis exploration experience. That work proved valuable map/timeline/graph/evidence patterns, but scaling it manually would have produced a historical viewer rather than the intended AI systems product. The Blank Cheque slice was therefore converted into a golden fixture, and the versioned generation contract became the core.

### 23.2 Article-first to map-first

The original renderer centered narrative with map/graph tabs. The product direction shifted to a persistent bounded map, synchronized time/lenses, and a docked assistant, while preserving the article/evidence renderer as Inspector. This better communicates systems, geography, and historical depth and supports the desired strategic-map interaction language.

### 23.3 Source-pipeline-first to LLM-core-first

The roadmap initially placed discovery/acquisition before the real assistant. It was reordered so the four-agent system could be built and evaluated against controlled corpora first. Discovery and acquisition moved to Phases F-G. This reduces the number of simultaneous unknowns: agent quality can be measured before adding web noise, rights failures, OCR, embeddings, and broad corpus variability.

### 23.4 Hosted frontier model to local open-weight default

A hosted frontier model would likely improve output quality and latency, but the project adopted local Ollama/Qwen to preserve the no-paid-infrastructure constraint. The provider boundary keeps future reconsideration possible. E7 is the evidence gate for whether this tradeoff remains acceptable.

## 24. Open Decisions

1. Does the four-agent workflow outperform simpler strategies enough to retain it?
2. What semantic-entailment mechanism catches directionality and qualification errors without introducing another unreliable opaque judge?
3. What latency is acceptable for research-quality results, and which stages can be simplified, cached, parallelized safely, or moved to a different model?
4. Should a hosted model provider be added if the local model cannot meet quality/latency gates, and under what cost/privacy limits?
5. Which two or three discovery providers should Phase F implement first based on access, rights, historical usefulness, and stable APIs?
6. When do embeddings materially improve retrieval enough to justify pgvector and added infrastructure?
7. What is the first production persistence boundary: agent runs only, normalized investigations, source corpus, or the complete review model?
8. What authentication/workspace model is the smallest safe foundation for private sources and Studio?
9. What hosting architecture can offer a compelling public demo without exposing an unauthenticated local-style AI endpoint or incurring uncontrolled cost?
10. Which additional corpus best tests geographic, linguistic, and historiographical generalization beyond European diplomacy?
11. What level of professional historical review is required before any package can be labelled reviewed/published rather than prototype-curated?
12. Should Phase K absorb private source enrichment and Studio impact review, or should a narrower source-enrichment slice be scheduled earlier?

## 25. Acceptance and Definition of Done

### 25.1 Near-term MVP acceptance

The MVP is acceptable when all of the following are true:

- The entry experience clearly distinguishes existing-package routing from new investigation generation.
- At least two materially different corpora render through the same generic package/workspace contracts.
- A user can ask each supported question class and receive a useful, cited, verified answer or a specific evidence-based abstention.
- Citation clicks resolve to the exact eligible record/passage/source used.
- Directionality, actor knowledge, temporal roles, counterevidence, and invalid premises pass the approved evaluation gates.
- Map actions reference valid package objects and never invent geography.
- Map, timeline, evidence, lens, and selection state remain synchronized and accessible.
- Long-running inference exposes stage progress, cancellation, resume, and bounded errors.
- Deterministic tests pass without Ollama; live tests are opt-in and produce reproducible audit records.
- A manual desktop/mobile/reduced-motion/keyboard flow passes.
- Performance is acceptable for the declared use case, or a deliberate architectural change is approved.
- Product copy accurately labels draft, partial, abstained, schematic, approximate, and unreviewed states.

### 25.2 Full autonomous product acceptance

The Phase K target is done only when a new supported topic can proceed from scoped request through source discovery, rights-respecting acquisition, citation-stable corpus construction, historical model generation, geographic/experience composition, assistant interaction, human review, immutable revision, and publication without hand-authoring application code or silently bypassing integrity gates.

## 26. Onboarding and Engineering Reading Order

For a technical collaborator joining the project:

1. `README.md` — repository entry point, noting that its status section may lag the current working tree.
2. `AGENTS.md` — canonical product, architecture, historical-integrity, security, cost, testing, and git rules.
3. `PRODUCT.md` and `DESIGN.md` — compact current product/design contracts.
4. This PRD — consolidated product and technical context.
5. `docs/product/product-vision.md`, `product-principles.md`, `ai-first-product-definition.md`, and `generation-first-user-experience.md`.
6. `docs/decisions/ADR-ai-generation-is-the-product-core.md`, `ADR-002-map-first-workspace.md`, and `ADR-003-llm-agent-system-is-product-core.md`.
7. `docs/architecture/generated-investigation-contract.md`, `system-overview.md`, `provenance-and-review.md`, `verification-and-abstention.md`, and `spatial-architecture.md`.
8. `docs/ai/model-provider-decisions.md`, `agent-architecture.md`, and `tool-registry.md`.
9. `docs/delivery/revised-development-phases.md`, `phase-e6-live-assistant-implementation-report.md`, `phase-e7-evaluation-harness-plan.md`, and `plans/current-phase.md`.
10. Frontend entry points: `src/app/routes.tsx`, `src/features/investigation/InvestigationPage.tsx`, `workspace/InvestigationWorkspace.tsx`, `workspace/panel/AskTab.tsx`, and `assistant/useInvestigationAssistant.ts`.
11. Backend entry points: `backend/src/chronicle/api/app.py`, `ai/orchestration/sequential.py`, `ai/orchestration/finalization.py`, `ai/agents/`, `ai/tools/`, `corpus/manifest.py`, and `storage/agent_run_store.py`.
12. Tests beside each module plus `backend/tests/ai/integration/` and `tests/e2e/` for end-to-end evidence.

Before making changes, inspect `git status`, because the local branch currently contains substantial uncommitted work and tracked deletions. Do not restore, overwrite, commit, or push another contributor's changes without coordination and explicit owner approval.

## 27. Suggested First Contributions for a Senior CS/SWE Collaborator

The highest-leverage work is not another visual feature. It is to help establish whether the product core is technically justified and safe:

1. Review and implement the Phase E7 evaluation harness without changing production prompts first.
2. Audit the semantic grounding boundary for entailment, directionality, temporal-role, and actor-knowledge failure modes.
3. Profile end-to-end and per-stage Qwen latency/memory; produce evidence-based simplification options.
4. Review the dirty working tree and reconcile the deleted Phase C corpus/provider/run-store files without discarding newer E2-E6 work.
5. Verify that remote GitHub contains the changes required for collaborative work before branching.
6. After E7, help choose the smallest Phase F discovery adapter set and design its rights/provenance threat model.
7. Review the transition from file persistence to a normalized database only when a concrete Phase F/G/Studio requirement demands it.

This order protects the project from investing in broad ingestion, databases, or additional UI before proving that the central assistant architecture produces reliable historical value.
