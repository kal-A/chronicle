# Chronicle — Claude Code Bootstrap Instructions

You are the primary development partner for a product called **Chronicle**.

Your first responsibility is to establish a durable product, architecture, research, and development foundation inside the repository. Do not immediately build the entire application.

Read this complete instruction before taking action.

## 1. Product Vision

Chronicle is an **interactive historical systems atlas powered by a shared evidence network**.

It helps people understand complex historical developments by exploring:

- What happened
- Where it happened
- When it happened
- Who made important decisions
- What different actors knew at the time
- What institutional, ideological, geographic, technological, and political pressures shaped those decisions
- How earlier events influenced later developments
- Where historical accounts agree or conflict
- What primary and secondary evidence supports each interpretation

Chronicle should feel like:

> An interactive historical documentary, atlas, timeline, systems map, evidence explorer, and investigation assistant combined.

It should not feel like:

- A generic history chatbot
- A Wikipedia clone
- A conventional academic project manager
- A graph visualization looking for a purpose
- An autonomous historian
- A source summarizer with no durable knowledge model
- A thin AI wrapper
- A barely functional technical prototype

## 2. Primary Product Experience

Chronicle has two long-term product surfaces.

### Chronicle Explore

The public-facing experience and the first product to build.

Users open a polished historical investigation and explore it immediately.

An investigation may include:

- A guided historical narrative
- Chapters or scenes
- A synchronized timeline
- A contextual geographic map
- A focused systems graph
- People, institutions, ideas, decisions, and events
- Primary and secondary sources
- Conflicting interpretations
- “Known at the Time” views
- An evidence-grounded investigation assistant

The first flagship investigation should likely be the **July Crisis of 1914**, but the architecture must not hard-code the application exclusively around this event.

### Chronicle Studio

The later authoring and editorial environment.

It will eventually allow trusted users to:

- Upload research documents
- Process sources using LLM workflows
- Review extracted events, actors, dates, places, and claims
- Connect evidence to historical entities
- Create timeline entries, map scenes, and systems relationships
- Compare new evidence with existing knowledge
- Route sources across several relevant investigations
- Review proposed changes before publication
- Publish or update Chronicle Explore investigations

Studio is not the first user-facing priority, but the early data architecture must not make it impossible.

## 3. Core User Value

Chronicle should help users do things that static articles, generic chatbots, and ordinary timelines do not do well.

A user should be able to:

1. Follow a complex event through a guided experience.
2. Move between narrative, timeline, map, graph, and evidence without losing context.
3. Select an event, decision, actor, institution, or place and see how it fits into the wider system.
4. Compare different perspectives and accounts.
5. Ask what specific actors or institutions knew by a given date.
6. Trace a historical connection through evidence.
7. Inspect supporting, opposing, or incomplete evidence.
8. See where an interpretation is debated.
9. Ask an assistant questions grounded in the current investigation.
10. Add a source privately and see where it may connect to the investigation or wider historical database.

## 4. Shared Historical Evidence Network

Chronicle should not store every investigation as a completely isolated project.

The long-term system should have shared entities such as:

- People
- Institutions
- Places
- Events
- Decisions
- Ideas
- Technologies
- Conditions
- Documents
- Claims
- Historical relationships

A single source may be relevant to several investigations.

For example, a source concerning Caesar in Egypt may be relevant to investigations about:

- Caesar’s Civil War
- The Alexandrian War
- Cleopatra and Roman power
- The fall of the Ptolemaic Kingdom
- The final wars of the Roman Republic
- The rise of Octavian

However, newly uploaded sources must never automatically rewrite public investigations.

The correct future workflow is:

```text
Source uploaded
→ passages extracted
→ historical entities and claims proposed
→ existing knowledge compared
→ potentially affected investigations identified
→ impact review created
→ human editor accepts, revises, disputes, or rejects each proposed update
```

Preserve:

- Provenance
- Source permissions
- Public/private state
- Editorial status
- Conflicting accounts
- Historical uncertainty
- Version history

## 5. Investigation Assistant

Chronicle should include an LLM-powered investigation assistant as a central feature, but it must be narrowly grounded in the investigation.

Useful question types include:

- Explain this event or connection.
- What evidence supports this interpretation?
- Where do these sources or actors disagree?
- What did this actor or institution know by this date?
- How did Event A influence Event B?
- Which claims remain disputed?
- What evidence is missing?
- Show this event from another actor’s perspective.
- Which locations were active during this period?
- How does this uploaded source affect the current investigation?

The assistant should turn answers into navigable actions.

An answer may:

- Focus the timeline
- Move the map to relevant locations
- Highlight graph nodes and relationships
- Open source passages
- Compare interpretations
- Suggest a guided path through the investigation

The assistant must not:

- Behave like an unrestricted general history chatbot
- Use unsourced model knowledge as investigation evidence
- Invent citations
- Claim that an actor knew something merely because information existed somewhere
- Flatten disputed interpretations
- Present unreviewed user uploads as public fact
- Hide insufficient evidence behind polished language
- Make public editorial changes without review

## 6. LLM and Agent Architecture

LLMs should handle ambiguous language and unstructured historical material.

Deterministic software should handle:

- Permissions
- Authentication
- Project and investigation boundaries
- Persistence
- Review status
- Date filtering
- Timeline ordering
- Map coordinates
- Graph traversal
- Citation existence
- Source visibility
- Publication rules
- State transitions

Likely bounded AI components include:

### Source Processing

- Source classification
- Passage segmentation assistance
- Metadata extraction
- Event and actor extraction
- Date and place extraction
- Claim extraction

### Historical Understanding

- Entity resolution
- Temporal interpretation
- Relationship proposal
- Supporting-evidence retrieval
- Counterevidence retrieval
- Conflicting-account detection
- Research-gap detection
- Investigation-impact analysis

### User Assistance

- Query planning
- Evidence retrieval
- Source comparison
- Actor-knowledge reconstruction
- Reviewed relationship tracing
- Answer verification
- Answer composition

Do not create a swarm of loosely controlled autonomous agents.

Prefer:

- Explicit state machines
- Typed inputs and outputs
- Small bounded tools
- Deterministic validations
- Human review
- Auditable execution

## 7. Historical Integrity Rules

Chronological sequence does not prove causation.

Historical relationships must be capable of being classified as:

- Directly supported
- Indirectly supported
- Contextual
- Correlational
- Disputed
- Speculative
- Insufficient evidence

Every important claim or relationship should be capable of retaining:

- Supporting passages
- Counterevidence
- Source identifiers
- Source type
- Temporal scope
- Geographic scope
- Direct or inferred status
- Review status
- Reviewer notes
- Prompt version
- Model version
- Processing timestamp
- Revision history

Distinguish:

- When an event occurred
- When it was reported
- When a message was sent
- When it was received
- When an actor became aware of it
- What later investigators discovered
- What later historians interpreted

Do not represent city-level evidence as an exact building location.

Do not use modern borders as though they represent historical political geography.

Period boundaries, place names, political control, and disputed geography require sourced historical data.

## 8. Quality Standard

This project is intended to become a polished portfolio product, not a rushed MVP.

“MVP” should mean:

> The smallest coherent and credible product experience that demonstrates real value.

It should not mean:

> The fastest collection of partially working screens.

Every phase should produce something usable and testable.

Prioritize:

- Coherent UX
- Historical traceability
- Clear interactions
- Reliable state
- Strong loading, empty, and failure states
- Accessibility
- Responsive design
- Consistent visual hierarchy
- Evaluation
- Honest limitations
- Maintainable architecture

Push back on ideas that:

- Add complexity without user value
- Turn chat into the entire product
- Make the graph unreadable
- Create redundant map views
- Introduce unnecessary services
- Require paid infrastructure
- Overstate historical certainty
- Depend on unreviewed AI outputs
- Attempt to map all of history immediately
- Sacrifice polish for feature count

## 9. Cost Constraint

The project must be developable and demonstrable without additional paid infrastructure.

Preferred free or open-source technologies include:

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- TanStack Query
- Cytoscape.js for systems graphs
- MapLibre GL JS for maps
- PDF.js where needed
- Vitest
- React Testing Library
- Playwright

### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL
- pgvector
- PostGIS when spatial queries justify it
- pytest

### AI Runtime

- Ollama for local inference
- Open-weight models
- Local embedding models
- Mock providers for tests

### Infrastructure

- Docker Compose
- GitHub Actions
- Free hosting only for a seeded public demonstration
- Static or preprocessed public investigation content where live inference would be unreliable or costly

Do not introduce a paid dependency without explicitly identifying it and explaining why a free option is insufficient.

Claude Code and Codex are development tools only. They must not become runtime dependencies.

## 10. Development Model

Work in bounded vertical slices.

A vertical slice should connect the smallest useful path through:

```text
Data model
→ backend service
→ API contract
→ frontend state
→ interface
→ tests
→ documentation
```

Do not build the complete backend before producing a visible product.

Do not build the entire AI pipeline before validating the exploration experience.

The recommended high-level sequence is:

```text
Product foundation
→ static investigation prototype
→ seeded full-stack Explore experience
→ synchronized story, timeline, map, graph, and evidence
→ investigation assistant using seeded reviewed data
→ source upload and private source analysis
→ Studio review workflows
→ shared evidence network
→ cross-investigation source routing
→ editorial publishing
```

## 11. Your Immediate Task

Do not implement the complete application yet.

First inspect the repository.

If the repository is empty, treat it as a new project.

If code already exists:

- Inspect it thoroughly.
- Explain what is reusable.
- Identify conflicts with this product direction.
- Do not delete or rewrite it until presenting a migration plan.

Then create or update the following source-of-truth files:

```text
AGENTS.md
CLAUDE.md
README.md

docs/
├── product/
│   ├── product-vision.md
│   ├── product-principles.md
│   ├── target-users.md
│   ├── core-user-experience.md
│   ├── explore-and-studio.md
│   ├── investigation-assistant.md
│   └── shared-evidence-network.md
│
├── research/
│   ├── historical-methodology.md
│   ├── source-hierarchy.md
│   ├── july-crisis-scope.md
│   ├── source-register-template.md
│   └── validation-status.md
│
├── architecture/
│   ├── system-overview.md
│   ├── domain-model.md
│   ├── frontend-architecture.md
│   ├── backend-architecture.md
│   ├── ai-agent-architecture.md
│   ├── spatial-architecture.md
│   ├── provenance-and-review.md
│   └── deployment.md
│
├── design/
│   ├── information-architecture.md
│   ├── investigation-layout.md
│   ├── interaction-principles.md
│   ├── map-timeline-graph-sync.md
│   └── accessibility.md
│
├── delivery/
│   ├── development-phases.md
│   ├── phase-0-product-foundation.md
│   ├── phase-1-static-prototype.md
│   ├── definition-of-done.md
│   └── risks-and-open-questions.md
│
└── decisions/
    ├── README.md
    └── ADR-001-explore-first.md

plans/
├── current-phase.md
├── backlog.md
└── completed/
```

Do not generate shallow filler documents merely to satisfy the file list.

Where two documents can responsibly be combined, explain why before combining them.

## 12. Shared Agent Instructions

Create `AGENTS.md` as the canonical instruction file for both Claude Code and Codex.

It must include:

- Product purpose
- Explore-first priority
- Historical-integrity rules
- Architecture boundaries
- Cost constraints
- Testing requirements
- Security requirements
- Development workflow
- Git restrictions
- Definition of done
- Rules for LLM outputs
- Rules for map and graph accuracy
- Rules protecting human-reviewed data

Create `CLAUDE.md` that imports or references `AGENTS.md` and adds Claude-specific workflow instructions.

Claude-specific requirements should include:

- Enter planning mode before substantial multi-file changes.
- Read the relevant product and architecture documents.
- Inspect current code before editing.
- State assumptions.
- Identify affected files.
- Propose the smallest complete vertical slice.
- Do not commit or push without explicit permission.
- Update delivery documentation after implementation.
- Provide an end-of-session handoff.
- Do not make broad architectural changes silently.

## 13. Revised Development Phases

Create a detailed `docs/delivery/development-phases.md`.

Each phase must include:

- Purpose
- Product assumption being tested
- User-facing capabilities
- Technical work
- Historical or content work
- Output at the end
- Manual test flow
- Automated test requirements
- Completion criteria
- Explicitly deferred scope
- Risks
- Claude Code responsibilities
- Codex review responsibilities

Use this phase structure as a starting point, but critically refine it.

### Phase 0: Product and Historical Foundation

Output:

- Durable product documentation
- Historical methodology
- July Crisis investigation boundary
- Initial source register
- Information architecture
- Low-fidelity interaction flows
- Prioritized assumptions
- Clearly defined first test

No production backend is required.

### Phase 1: Static Explore Prototype

Output:

- A polished frontend-only investigation prototype
- Seeded July Crisis content
- Guided story chapters
- Basic timeline
- Basic geographic scenes
- Focused relationship view
- Evidence panel
- Mock investigation assistant
- Responsive design

Use realistic curated mock data.

The prototype should test whether users understand and value the exploration experience before backend complexity is added.

### Phase 2: Seeded Full-Stack Investigation

Output:

- React frontend
- FastAPI backend
- PostgreSQL
- Typed API contracts
- Seeded investigation data
- Persistent events, actors, places, sources, claims, and relationships
- Working source-to-evidence navigation
- Docker-based local setup
- Automated tests

No live extraction agent is required.

### Phase 3: Synchronized Historical Exploration

Output:

- Story, timeline, map, graph, and evidence synchronization
- Scene-based map navigation
- Focused local graph expansion
- Actor and institution perspectives
- Known-at-the-Time prototype
- Historical naming support
- Strong state and URL persistence

### Phase 4: Evidence-Grounded Investigation Assistant

Output:

- Assistant grounded only in seeded reviewed investigation data
- Controlled tools for:
  - source search;
  - source comparison;
  - reviewed relationship tracing;
  - timeline context;
  - map context;
  - actor-knowledge reconstruction;
  - evidence-gap detection.
- Citations and interface navigation
- Verification pass
- Honest insufficient-evidence behaviour

Start with four polished question types:

1. Explain this event or connection.
2. Compare these accounts or actors.
3. What was known by this date?
4. What is disputed or missing?

### Phase 5: Private Source Upload and Analysis

Output:

- User-created private workspace
- Document upload
- Source metadata
- Text extraction
- Passage storage
- Private assistant comparison against an investigation
- Suggested relevant entities and events
- No public database changes

### Phase 6: Chronicle Studio Review Workflow

Output:

- Structured extraction
- Event, actor, place, date, and claim proposals
- Approve, revise, reject, merge, and dispute actions
- Entity resolution
- Human correction persistence
- Reprocessing safety
- Audit history

### Phase 7: Shared Evidence Network

Output:

- Canonical historical entities
- Reusable sources and passages
- Cross-investigation relationships
- Investigation-specific presentation layers
- Public/private permissions
- Versioned evidence associations

Demonstrate this with two connected investigations rather than trying to model all history.

### Phase 8: Cross-Investigation Source Routing

Output:

- Investigation-impact analysis
- Proposed source relevance across investigations
- Supporting, contradicting, contextual, or duplicate classification
- Human editorial approval
- No silent public updates

### Phase 9: Publishing and Contribution

Output:

- Investigation authoring
- Scene creation
- Timeline and map editing
- Evidence review
- Editorial workflow
- Published Explore experience
- Version history and rollback

### Phase 10: Evaluation and Portfolio Release

Output:

- Stable seeded public demo
- Full local version
- Evaluated assistant
- Historical limitations report
- Architecture documentation
- User testing
- Performance and security checks
- Demo video
- Portfolio case study

For each phase, ensure the user has a runnable product or testable artifact.

## 14. First Build Recommendation

After producing the documentation and roadmap, recommend the smallest strong first implementation.

The preferred starting point is likely:

> A frontend-only July Crisis Explore prototype with three to five guided scenes, a synchronized narrative/timeline/map interaction, a focused relationship panel, visible evidence, and a mocked investigation assistant.

Do not begin with:

- Authentication
- User accounts
- General source uploads
- A production vector database
- Full autonomous agents
- Cross-investigation routing
- A graph database
- Every July Crisis event
- Every European border
- Complex historical polygon data
- A general-purpose chat interface

The first prototype must answer:

> Is exploring history in this combined format actually understandable, useful, and compelling?

## 15. Codex Integration

Codex does not have access to the prior product conversations.

You must create durable instructions that Codex can use independently.

Create:

```text
docs/delivery/codex-review-process.md
.codex/
├── README.md
├── review-template.md
└── phase-review-prompts.md
```

If a `.codex` directory is not appropriate for the repository, use `docs/codex/` and explain the choice.

Codex should be treated primarily as an independent reviewer, not a simultaneous co-author of the same feature.

The preferred workflow is:

```text
Claude plans
→ Kamal approves
→ Claude implements
→ Claude runs tests
→ Codex independently reviews
→ Kamal evaluates findings
→ Claude applies accepted fixes
```

Claude and Codex must not edit the same working tree simultaneously.

## 16. Instructions You Must Generate for Codex

Create exact reusable Codex prompts for the following situations.

### A. Phase Plan Review

Codex should review:

- Product coherence
- Scope
- Missing outputs
- Whether each phase is testable
- Whether AI is being added before product value is established
- Whether the roadmap is overengineered
- Whether the historical-validation process is credible

### B. Architecture Review

Codex should review:

- Frontend/backend separation
- Domain boundaries
- Data-model consistency
- Provenance
- State transitions
- Permissions
- Local deployment
- Unnecessary dependencies
- Scaling assumptions
- Failure recovery

### C. Feature Diff Review

Codex should receive:

- `AGENTS.md`
- Feature brief
- Acceptance criteria
- Approved implementation plan
- Current diff
- Test results

It should identify:

1. Blocking issues
2. Important improvements
3. Optional refinements

It should check:

- Missing acceptance criteria
- Frontend/backend mismatch
- Provenance loss
- Human-review bypass
- Unreviewed claims leaking into published data
- Broken timeline or map semantics
- Incorrect historical certainty
- Accessibility
- Security
- Missing tests
- Unnecessary complexity
- Unrelated changes

Codex should not edit the code during the first review pass.

### D. Historical Feature Review

Codex should check software behaviour, not independently declare historical truth.

It should check whether:

- Claims are cited
- Uncertainty is represented
- Date types are distinguished
- Location precision is honest
- Disagreement can be represented
- Modern geographic assumptions leak into historical views
- Historical evidence can be traced
- Unsupported claims are blocked

Historical factual validation must still use reviewed sources.

### E. Pre-Release Review

Codex should:

- Follow setup instructions from a clean environment
- Run tests
- Inspect security-sensitive flows
- Test primary user journeys
- Identify stale documentation
- Identify fragile demo behaviour
- Check whether the project can be explained credibly in an interview

## 17. Codex Handoff Output

At the end of every completed Claude implementation phase, generate a Codex handoff containing:

```text
Feature or phase:
User problem:
Expected user outcome:
Relevant product documents:
Relevant architecture documents:
Files changed:
Database changes:
API changes:
Tests added:
Commands run:
Known limitations:
Risks:
Acceptance criteria:
Specific areas requiring independent review:
```

The handoff must be factual and based on the implemented code.

Do not give Codex Claude’s internal reasoning or ask it merely to agree with the implementation.

## 18. Critical Review Behaviour

You must be constructively critical throughout this project.

Do not automatically accept a requested feature.

When evaluating a feature, assess:

- What user problem it solves
- Whether an existing feature already solves it
- Whether it makes the product clearer or more confusing
- Whether it should exist in Explore, Studio, or neither
- Whether it needs an LLM
- Whether deterministic software is better
- Whether it expands historical-validation requirements
- Whether it adds disproportionate complexity
- Whether it threatens the free-development constraint
- Whether it improves the FluidAI-relevant portfolio story
- Whether it can be built and polished properly

When an idea is weak, say so clearly and propose a stronger alternative.

## 19. Your Required Output Before Coding

Before editing production code, provide:

1. Repository assessment
2. Product understanding
3. Major assumptions
4. Proposed document structure
5. Revised phased roadmap summary
6. Proposed domain-model outline
7. Proposed first prototype scope
8. Risks and open questions
9. Files you intend to create or modify
10. Exact commands or setup choices you expect to use
11. Whether any decision needs Kamal’s approval before implementation

Do not ask broad questions that can be resolved through a sensible documented assumption.

When an assumption is necessary:

- State it
- Record it
- Design it so it can be revised later

After the assessment, create the documentation foundation.

Do not scaffold the production application until the documentation foundation and first prototype scope are coherent.

## 20. End-of-Task Report

After creating the documentation foundation, report:

- Files created
- Files modified
- Key product decisions captured
- Revised development phases
- First implementation recommendation
- Open product risks
- Open historical-research risks
- Open technical risks
- Proposed first feature brief
- Codex review instructions created
- What should be reviewed manually before coding begins

Do not commit or push unless explicitly instructed.
