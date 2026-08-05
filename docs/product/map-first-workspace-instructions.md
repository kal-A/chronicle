# Chronicle — Map-First Investigation Workspace and Updated Next-Phase Instructions

> Source document supplied by Kamal on 2026-08-04 (`chronicle_map_first_workspace_next_phase_instructions.md`), preserved here verbatim as the durable reference for Phase D. Summarized/actioned by `docs/decisions/ADR-002-map-first-workspace.md` and `plans/current-phase.md`; other product/architecture docs reference this file rather than duplicating its content.

## Purpose

This document is an **additive update** to the existing Chronicle instructions and roadmap.

It does not replace:

- the AI-first product definition;
- the generated-investigation contract;
- the deterministic generation pipeline;
- the source-discovery and assessment plan;
- the historical-integrity requirements;
- the map-rights and precision constraints;
- the assistant-grounding rules; or
- the later retrieval, extraction, relationship, geographic, and publishing phases.

It adds a major product and UX correction:

> Chronicle should begin as a conversational historical inquiry and then transform into a map-first investigation workspace. The map is the main interaction canvas. The assistant panel begins as the initial input surface and remains beside the map as the guide, control surface, evidence inspector, and source navigator.

The current article-first renderer should remain available as an Inspector and accessibility fallback, but it should no longer define the main Chronicle experience.

---

# 1. Updated Product Framing

Chronicle is:

> **A conversational historical investigation environment. A user asks a question, Chronicle builds an evidence-backed geographic investigation, and the user explores it through a focused historical map, time controls, contextual AI assistance, inspectable relationships, and traceable sources.**

The major product surfaces are:

## 1.1 Ask

The initial conversational interface.

The user enters:

- a historical event;
- a person;
- a period;
- a comparison;
- a connection;
- a source;
- or a natural-language historical question.

Examples:

- `How did the Concert of Europe respond to revolutionary movements?`
- `What did the French mainland authorities know during the Haitian Revolution?`
- `How did the German blank cheque affect Austria-Hungary's decisions?`
- `Where did British and Austrian positions on intervention differ?`
- `How did Caesar's intervention in Egypt affect later Roman power struggles?`

## 1.2 Investigate

The map-first historical workspace.

Chronicle opens only the geographic area relevant to the investigation and displays:

- events;
- places;
- routes;
- communications;
- actor positions;
- knowledge states;
- systems relationships;
- source coverage;
- uncertainty;
- and temporal change.

## 1.3 Ask Chronicle

The contextual investigation assistant.

It remains available beside the map and can:

- answer grounded questions;
- change the selected time;
- focus a place;
- activate a lens;
- trace a relationship;
- compare actors;
- open evidence;
- explain uncertainty;
- and suggest productive next questions.

## 1.4 Inspector

The detailed evidence and provenance environment.

It contains:

- full claims;
- supporting passages;
- counterevidence;
- source metadata;
- rights;
- known limitations;
- relationship classifications;
- generation reports;
- rejected or deferred source candidates;
- and audit history.

The current article/evidence-heavy experience should be preserved here rather than discarded.

---

# 2. Core User Journey

The intended flow is:

```text
User asks about a historical event or question
→ Chronicle interprets the request
→ Chronicle proposes a bounded scope
→ user approves or adjusts the scope
→ Chronicle generates the investigation
→ a focused historical map opens
→ the original interaction panel remains beside the map
→ the user explores through time, map lenses, questions, relationships, and evidence
```

The initial panel and later assistant panel are the **same persistent product surface** in different states.

```text
Initial Ask panel
→ Scope panel
→ Generation-progress panel
→ Investigation assistant
→ Evidence/source inspector
```

The user should not feel redirected from one disconnected product into another.

---

# 3. Map Scope

The map is the primary workspace after generation.

It must not default to the whole world.

Every investigation should generate a bounded `MapScope`.

```ts
type MapScope = {
  bounds: GeographicBounds;
  focusRegions: HistoricalRegionReference[];
  contextRegions: HistoricalRegionReference[];

  initialViewport: Viewport;
  minimumZoom: number;
  maximumZoom: number;

  geographicRationale: string;
  representedPeriod: TimeRange;

  unavailableHistoricalBoundaries: string[];
  geographicLimitations: string[];
};
```

## 3.1 Scope principles

The map should:

- include the locations required to understand the investigation;
- include enough surrounding geography for orientation;
- exclude irrelevant global space;
- change focus when the active historical sequence expands geographically;
- use historically appropriate place labels where supported;
- distinguish period labels from modern clarification;
- avoid displaying unsupported historical boundaries;
- disclose when only a modern basemap or schematic view is available.

## 3.2 Examples

### July Crisis

Initial scope:

- Sarajevo;
- Vienna;
- Berlin;
- Belgrade;
- Saint Petersburg;
- Paris;
- London;
- relevant communication routes.

Do not display the entire world.

### Haitian Revolution

Possible scope:

- Saint-Domingue;
- nearby Caribbean routes;
- relevant French Atlantic ports;
- Paris or other mainland authorities only when the investigation requires them.

### Caesar in Egypt

Possible scope:

- Alexandria;
- the Nile Delta;
- relevant eastern Mediterranean routes;
- selected Roman locations when the narrative expands.

### Concert of Europe

Possible scope:

- Vienna;
- Aachen;
- Troppau;
- Laibach;
- Verona;
- Naples;
- Spain;
- Britain;
- other capitals only when relevant to a selected lens.

---

# 4. Initial Interaction Surface

The initial interface should be conversational, focused, and minimal.

## 4.1 Default initial state

Suggested structure:

```text
Chronicle

What would you like to investigate?

[ Ask a historical question... ]

Suggested starting points:
- Explain how an event unfolded
- Compare historical perspectives
- Reconstruct what was known at a particular time
- Trace the connection between two events
- Explore a source
```

Optional controls may include:

- investigation depth;
- date range;
- actor or institution focus;
- geographic focus;
- primary-source emphasis.

Do not expose advanced provider, model, or retrieval configuration to ordinary users.

## 4.2 Clarification behaviour

Chronicle should ask only the minimum useful clarification.

Example:

> I can focus this investigation on the initial Concert of Europe from 1814–1822, emphasizing intervention doctrine, Austria's actions in Naples, and British opposition. I will prioritize primary diplomatic documents where available. Proceed with this scope?

Actions:

- Generate this investigation
- Edit scope
- Expand timeframe
- Focus on selected actors
- Prioritize primary sources

Avoid turning the initial experience into a long research questionnaire.

---

# 5. Scope Review

The assistant should propose:

- interpreted question;
- date range;
- geographic area;
- primary actors;
- institutions;
- themes;
- relevant source categories;
- included scope;
- excluded scope;
- important ambiguities;
- likely investigation lenses.

Example:

```text
Question:
How did the Concert of Europe respond to revolutionary movements?

Proposed scope:
1814–1822

Focus:
- intervention doctrine;
- Troppau;
- Laibach;
- Naples;
- British opposition;
- Verona and Spain.

Excluded:
- later nineteenth-century balance-of-power politics;
- the Crimean War;
- all events through 1848.

Likely lenses:
- Sequence;
- Diplomatic positions;
- Systems relationships;
- Evidence gaps.
```

The approved scope should become a first-class persisted record.

---

# 6. Generation Transition

After approval, the initial assistant panel should move into a docked position while the map workspace opens.

This transition should preserve:

- the original user question;
- scope decisions;
- conversation history;
- generation progress;
- source-discovery status;
- and assistant context.

Do not build a separate disconnected generation page unless implementation constraints require it.

## 6.1 Progress display

Show structured workflow state, not private model reasoning.

Example:

```text
✔ Scope defined
✔ Discovery queries prepared
✔ 24 source candidates found
✔ 11 sources accepted
… Extracting events and positions
… Building the timeline
… Preparing map lenses
… Checking claims and citations
```

The user may inspect:

- accepted sources;
- rejected sources;
- missing coverage;
- provider failures;
- current limitations.

Do not reveal speculative historical content before it passes verification.

---

# 7. Main Desktop Workspace

Recommended structure:

```text
┌──────────────────────────────────────────────────────────────┐
│ Chronicle  Investigation title      Coverage  Sources  ⋯      │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│                    HISTORICAL MAP                             │
│                                                                │
│  events · regions · movements · communications                │
│  knowledge · positions · relationships · uncertainty          │
│                                                                │
│                                    ┌──────────────────────┐   │
│                                    │ Ask                  │   │
│                                    │ Explore               │   │
│                                    │ Evidence               │   │
│                                    │ Sources                │   │
│                                    │                        │   │
│                                    │ Contextual content     │   │
│                                    └──────────────────────┘   │
│                                                                │
├──────────────────────────────────────────────────────────────┤
│ 1814 ─────────────────────────────── 1822   │  ▶  Play  Filters │
└──────────────────────────────────────────────────────────────┘
```

The map remains visible while the user:

- asks a question;
- inspects a source;
- reads an explanation;
- compares actors;
- selects a relationship;
- or moves through time.

The map should not be a tab beside Relationships.

---

# 8. Docked Interaction Panel

The panel should be docked and resizable.

A fully free-floating window should be deferred because it introduces:

- map obstruction;
- keyboard and focus complexity;
- responsive-layout problems;
- discoverability problems;
- accidental loss;
- and desktop-software behaviour that may not help the product.

## 8.1 Desktop behaviour

Default:

- docked to the right;
- approximately 360–420 pixels wide;
- map automatically resizes.

Controls:

- drag divider to resize;
- minimum width around 320 pixels;
- maximum width around half the workspace;
- collapse to an icon rail;
- reopen without losing state;
- optional dock-left control;
- double-click divider to restore the default width;
- keyboard buttons to increase, decrease, reset, collapse, and reopen.

Persist the user's width preference locally where appropriate.

## 8.2 Panel tabs

### Ask

Grounded LLM interaction.

### Explore

Generated investigation structure:

- direct answer;
- key findings;
- story beats;
- actors;
- institutions;
- locations;
- perspectives;
- tensions;
- uncertainties;
- suggested paths.

### Evidence

Current selected claim or relationship:

- explanation;
- classification;
- supporting passages;
- counterevidence;
- source links;
- limitations.

### Sources

Investigation corpus:

- accepted sources;
- source types;
- rights;
- perspectives;
- coverage;
- rejected or deferred candidates;
- known gaps.

Optional later tabs:

- Notes;
- Compare;
- Generation report.

Do not create too many first-level tabs during the first implementation.

---

# 9. Mobile and Tablet Behaviour

## 9.1 Mobile

Use:

- full-screen map;
- bottom sheet instead of side panel;
- drag handle;
- collapsed, half-height, and expanded states;
- Assistant, Explore, Evidence, and Sources tabs;
- timeline above the bottom sheet;
- horizontally scrollable lens selector only when necessary;
- selected-location card above the sheet.

Do not use free-floating windows.

## 9.2 Tablet

- docked panel in landscape where space permits;
- bottom sheet in portrait;
- preserve the same investigation state across orientation changes.

---

# 10. Historical Investigation Lenses

Use the term **lens**, not game-like "map mode."

Each lens answers a historical question.

Not every investigation requires every lens.

The Experience Composer should choose only useful lenses.

## 10.1 Sequence

Question:

> What happened, where, and in what order?

Shows:

- event markers;
- dates;
- story steps;
- routes;
- communications;
- movements;
- turning points.

## 10.2 Positions

Question:

> How did relevant actors or institutions differ on the selected issue?

Shows evidence-backed classifications such as:

- supported;
- opposed;
- supported with qualifications;
- position changed;
- unresolved in the current corpus.

Every position must trace to evidence.

## 10.3 Knowledge

Question:

> What could a selected actor plausibly have known at this point?

Distinguish:

- event occurred;
- report created;
- report sent;
- report received;
- evidence of awareness;
- acted upon;
- unknown;
- uncertain.

Do not infer knowledge merely because information existed.

## 10.4 Systems

Question:

> What mechanisms and relationships connected the selected events?

Shows a focused historical path.

Visible nodes should usually be:

- people;
- institutions;
- events;
- decisions;
- ideas;
- documents;
- conditions;
- places.

Do not expose numbered claim records as the primary visual language.

Claims and evidence support the edges and explanations.

## 10.5 Sources

Question:

> Where does the investigation's evidence come from, and where is coverage weak?

Shows:

- source origin;
- archive or institution;
- geographic coverage;
- source density;
- missing areas;
- public/private or accepted/deferred status.

## 10.6 Uncertainty

Question:

> Which parts of the investigation remain weak, approximate, disputed, or unsupported?

Shows:

- disputed relationships;
- indirect support;
- approximate locations;
- missing primary evidence;
- unresolved boundaries;
- weak geographic coverage;
- absent perspectives.

## 10.7 Political or Territorial Context

Use only when historically sourced and necessary.

Do not present modern borders as historical borders.

---

# 11. Timeline Interaction

The timeline should be integrated with the map.

## 11.1 Controls

Support:

- scrub;
- event markers;
- play and pause;
- step forward and backward;
- adjustable playback speed;
- date-range selection;
- reset;
- "Known at this time" toggle;
- reduced-motion mode.

## 11.2 Map synchronization

Changing time may:

- add or remove markers;
- reveal communication routes;
- update positions;
- show movement;
- change labels;
- change known information;
- activate relevant story beats;
- alter system paths;
- update assistant suggestions.

The timeline should not be a row of large cards occupying the top of the page.

---

# 12. Map Interaction Behaviour

## 12.1 Select a place

Selecting a place should:

- focus the location;
- open a compact context card;
- show what occurred there;
- highlight related events;
- update the timeline;
- show connected actors and institutions;
- update suggested questions;
- expose evidence.

## 12.2 Select an event

Selecting an event should:

- focus relevant location(s);
- highlight the date or range;
- show linked actors;
- show associated claims and decisions;
- show evidence and uncertainty;
- suggest relevant follow-ups.

## 12.3 Select a route or communication

Show:

- origin;
- destination;
- date;
- movement or communication type;
- what moved or was transmitted;
- documented versus inferred status;
- supporting evidence;
- uncertainty.

## 12.4 Select a relationship

Show:

- source element;
- target element;
- relationship verb;
- mechanism;
- support classification;
- supporting evidence;
- counterevidence;
- alternative explanations;
- review status.

## 12.5 Select a region

Show, where supported:

- period political context;
- institutions;
- active events;
- relevant actors;
- current source coverage;
- applicable historical labels;
- boundary uncertainty.

---

# 13. Systems Visualization Redesign

The current numbered-node graph is not an acceptable long-term user-facing systems view.

## 13.1 Required changes

Do not use:

- numbered-only nodes;
- claim IDs as the main historical objects;
- an empty black debugging canvas;
- a separate numbered legend required to interpret the graph;
- duplicate relationship cards below the graph.

Use:

- directly labelled historical nodes;
- readable edge verbs;
- focused paths;
- progressive expansion;
- contextual evidence on selection;
- evidence-strength encoding;
- text fallback.

## 13.2 Example

```text
Troppau Protocol
        │ established
        ▼
Intervention doctrine
        │ invoked at
        ▼
Congress of Laibach
        │ authorized
        ▼
Austrian intervention in Naples
```

Opposition path:

```text
Castlereagh / Britain
        │ rejected
        ▼
General intervention doctrine
```

Weak extension:

```text
Troppau doctrine
        │ later extended?
        ▼
Verona authorization
        │ weaker direct evidence
        ▼
French intervention in Spain
```

## 13.3 Evidence states

Possible stable visual encodings:

- solid line: directly supported;
- dashed line: indirectly supported;
- parallel/opposing treatment: disputed;
- faded/incomplete line: insufficient;
- contextual line: background or enabling condition.

Do not rely on colour alone.

---

# 14. Map Sequence Example: Concert of Europe

## Default finding

> The intervention principle moved from declaration at Troppau to practical application at Laibach and Naples, while Britain rejected its use as a general licence to police revolutions. Its later extension through Verona is less directly supported in Chronicle's current corpus.

## Sequence

1. **Troppau**
   - doctrine articulated;
   - November 1820.

2. **Laibach**
   - intervention authorized;
   - early 1821.

3. **Naples**
   - Austrian intervention carried out;
   - March 1821.

4. **Britain**
   - general doctrine rejected;
   - position shown as an opposing diplomatic path.

5. **Verona and Spain**
   - doctrine treated as extended;
   - weaker direct source support;
   - uncertainty visible.

The current static package should be used to implement this deterministic experience plan before the Experience Composer becomes live.

---

# 15. Contextual Assistant

The assistant is not merely a chat window.

It must operate the workspace through typed actions.

## 15.1 Assistant action contract

```ts
type AssistantAction =
  | { type: "FOCUS_LOCATION"; locationId: string }
  | { type: "FOCUS_EVENT"; eventId: string }
  | { type: "SET_TIME"; date: HistoricalDate }
  | { type: "SET_TIME_RANGE"; range: TimeRange }
  | { type: "ACTIVATE_LENS"; lensId: string }
  | { type: "HIGHLIGHT_EVENTS"; eventIds: string[] }
  | { type: "HIGHLIGHT_RELATIONSHIP"; relationshipId: string }
  | { type: "SHOW_SYSTEM_PATH"; pathId: string }
  | { type: "COMPARE_ACTORS"; actorIds: string[] }
  | { type: "OPEN_EVIDENCE"; recordId: string }
  | { type: "OPEN_SOURCE"; sourceId: string }
  | { type: "RESET_VIEW" };
```

All referenced IDs must exist in the validated package.

The LLM must not generate arbitrary JavaScript or map commands.

## 15.2 Example

User:

> How did Troppau lead to intervention in Naples?

Assistant response:

> The current corpus supports a three-step path. The Troppau Protocol articulated a general intervention principle; the powers invoked that principle at Laibach; Austrian forces then intervened against the constitutional government in Naples. Chronicle's present evidence for the later Verona extension is weaker.

Suggested actions:

- Show the sequence
- Open Troppau evidence
- Compare Britain's objection
- Move to January 1821

Selecting `Show the sequence` should activate the Sequence lens and focus the relevant events, locations, and time range.

## 15.3 Contextual prompts

Prompts should respond to selection state.

### No selection

- What is the main conclusion?
- Where do the powers disagree?
- Show the intervention sequence.
- What evidence is missing?

### Troppau selected

- What was agreed here?
- Who rejected this doctrine?
- How was the doctrine applied?
- Show the strongest primary evidence.

### Britain selected

- Why did Britain object?
- Compare Castlereagh and Metternich.
- Did Britain reject every form of intervention?
- Which evidence supports this position?

---

# 16. Evidence and Inspector Behaviour

Evidence should support the experience without dominating the default workspace.

## 16.1 Default evidence depth

Show:

- concise claim;
- classification;
- one or two key evidence references;
- uncertainty;
- open-full-evidence action.

## 16.2 Inspector

The Inspector may contain:

- complete narrative;
- all claims;
- relationship ledger;
- source passages;
- counterevidence;
- source limitations;
- rights;
- map-source details;
- generation report;
- source-assessment decisions.

The current article/evidence renderer should be adapted into this mode.

## 16.3 Deep-linking

Every:

- place;
- event;
- relationship;
- source;
- passage;
- date;
- lens;
- assistant answer;

should support a durable URL or equivalent state representation where practical.

---

# 17. Accessibility Requirements

The map cannot be the only way to use Chronicle.

## 17.1 Equivalent structured views

Every map lens must have a text representation.

Example:

```text
Current visible sequence

1. Troppau — Protocol signed, 19 November 1820
2. Laibach — Intervention authorized, early 1821
3. Naples — Austrian intervention carried out, March 1821
4. Verona — French intervention in Spain authorized, late 1822
```

## 17.2 Required accessibility

- keyboard-accessible markers;
- accessible timeline controls;
- screen-reader selection announcements;
- relationship paths as ordered text;
- colour-independent classification;
- panel resizing through keyboard buttons;
- focus preservation during panel changes;
- reduced-motion support;
- no forced map animation;
- readable alternatives for historical boundaries and routes;
- accessible bottom-sheet behaviour on mobile.

Existing accessibility tests must remain passing and be extended.

---

# 18. Investigation Experience Plan Contract

Add a first-class generated experience layer.

```ts
type InvestigationExperiencePlan = {
  opening: {
    question: string;
    scopeSummary: string;
    leadAnswer: string;
    evidenceCoverageSummary: string;
  };

  workspace: {
    initialMapScope: MapScope;
    initialLensId: string;
    initialTimeRange: TimeRange;
    initialPanelTab: PanelTab;
    defaultPanelWidth: number;
  };

  lenses: InvestigationLens[];
  timeline: InvestigationTimelinePlan;

  storySequences: StorySequence[];
  systemPaths: SystemPath[];
  perspectiveComparisons: PerspectiveComparison[];

  contextualPrompts: ContextualPromptSet[];
  recommendedSelections: SelectionTarget[];
  limitations: InvestigationLimitation[];

  inspector: {
    defaultEvidenceDepth: EvidenceDepth;
    exposeGenerationReport: boolean;
    exposeRejectedSources: boolean;
  };
};
```

## 18.1 Investigation lens

```ts
type InvestigationLens = {
  id: string;
  label: string;
  purpose: string;
  historicalQuestion: string;

  applicableTimeRange: TimeRange;

  visibleLocations: string[];
  visibleEvents: string[];
  visibleRelationships: string[];
  visibleRegions: string[];

  markerRules: MarkerRule[];
  routeRules: RouteRule[];
  regionRules: RegionRule[];
  labelRules: LabelRule[];

  legend: LegendItem[];

  evidenceReferences: string[];
  limitations: string[];
};
```

## 18.2 Story sequence

```ts
type StorySequence = {
  id: string;
  title: string;
  summary: string;
  stepIds: string[];
  defaultLensId: string;
  defaultTimeRange: TimeRange;
};
```

## 18.3 System path

```ts
type SystemPath = {
  id: string;
  title: string;
  nodeIds: string[];
  relationshipIds: string[];
  summary: string;
  limitations: string[];
};
```

## 18.4 Cross-reference validation

Validate:

- all lens record IDs;
- all map-scope references;
- all story steps;
- all system paths;
- all assistant actions;
- all evidence references;
- all timeline references;
- all default selections;
- all contextual prompt targets.

Add Zod and Pydantic parity.

---

# 19. Experience Composer

The long-term AI pipeline must generate the experience plan after the historical model is verified.

```text
Verified historical model
→ Experience Composer
→ deterministic cross-reference validation
→ InvestigationExperiencePlan
→ map-first frontend
```

## 19.1 Experience Composer responsibilities

Determine:

- opening question;
- lead answer;
- initial geographic scope;
- most useful default lens;
- timeline framing;
- important story sequences;
- focused system paths;
- perspectives worth comparing;
- meaningful uncertainty;
- contextual prompts;
- evidence presentation depth.

## 19.2 The Experience Composer must not

- invent historical records;
- change claim status;
- introduce unsupported relationships;
- create map routes without geographic evidence;
- conceal uncertainty;
- alter source rights;
- generate arbitrary frontend code;
- include IDs that do not exist.

Initially, use deterministic experience-plan fixtures.

A live LLM Experience Composer comes after the contract and UI are proven.

---

# 20. Updated Phase Sequence

Insert a focused phase before live source-discovery work.

## Phase D0 — Map-First Investigation Experience

### D0.1 Interaction architecture

Define and document:

- entry-to-workspace transition;
- scope interaction;
- panel states;
- resizing;
- map selection;
- timeline synchronization;
- lenses;
- Inspector;
- assistant actions;
- responsive behaviour;
- accessibility equivalents.

### D0.2 Experience-plan contract

Implement:

- `InvestigationExperiencePlan`;
- `MapScope`;
- `InvestigationLens`;
- `StorySequence`;
- `SystemPath`;
- contextual prompts;
- assistant actions;
- cross-reference validation;
- Zod/Pydantic parity;
- shared valid/invalid fixtures.

### D0.3 Workspace shell

Build:

- map-first desktop layout;
- docked resizable assistant panel;
- panel tabs;
- timeline scrubber;
- lens selector;
- selected-item context card;
- evidence drawer;
- Inspector mode;
- mobile bottom sheet.

### D0.4 Concert of Europe experience plan

Create a deterministic plan containing:

- bounded map scope;
- opening intervention sequence;
- Troppau→Laibach→Naples path;
- British opposition;
- Verona uncertainty;
- contextual prompts;
- accessible text sequence;
- evidence links.

The plan must be package/provider output, not hard-coded React branching.

### D0.5 Initial interaction prototype

Add:

- question input state;
- mock scope proposal;
- approve/edit actions;
- mock generation progress;
- smooth transition into the workspace;
- persistent conversation context.

### D0.6 Usability gate

Test whether users can:

- begin an investigation;
- understand the scope;
- identify the main finding;
- navigate the map;
- resize/collapse the panel;
- move through time;
- change lenses;
- ask a contextual question;
- inspect evidence;
- identify a limitation;
- return to the overview.

## Phase D1 — Live scope-planning agent

After D0:

- introduce a bounded LLM scope planner;
- store prompt/model versions;
- validate output;
- preserve deterministic fallback.

## Phase D2–D5 — Live source discovery and assessment

Continue the existing plan:

- provider adapters;
- candidate registry;
- deduplication;
- assessment;
- coverage;
- diversity;
- abstention;
- Source Discovery Report.

## Phase E — Acquisition and corpus retrieval

- full-text acquisition;
- PDF/OCR;
- passage extraction;
- lexical retrieval;
- embeddings;
- metadata filters.

## Phase F — Historical extraction

- actors;
- institutions;
- events;
- dates;
- locations;
- decisions;
- communications;
- claims;
- uncertainty.

## Phase G — Relationship and critic workflows

- relationship proposals;
- mechanisms;
- counterevidence;
- alternatives;
- causal downgrading;
- abstention.

## Phase H — Geographic and map generation

- historical place resolution;
- map discovery;
- rights checks;
- georeferencing;
- map scenes;
- generated lenses;
- map interaction plans.

## Phase I — Full live generation UX and assistant

- complete live request-to-map workflow;
- contextual assistant;
- streaming progress;
- source inspection;
- generated experience plans.

> **Note on lettering (added by Claude during D0.1, 2026-08-04):** this section's own "Phase D0/D1/D2-D5/E-I" numbering is the source document's original proposal. Chronicle's actual roadmap (`docs/delivery/revised-development-phases.md`) instead inserted this work as the new **Phase D** in full (not a "D0" sub-phase of an existing Phase D), shifting the previously-lettered D-K to E-L — see `docs/decisions/ADR-002-map-first-workspace.md` for the reasoning. Treat this section as the original proposal's internal sequencing (D0.1-D0.6 as Phase D's own sub-plans), not the authoritative letter-to-phase mapping.

---

# 21. Changes Required to Existing Instructions and Documents

Update the existing documentation rather than silently contradicting it.

## 21.1 Product documents

Update:

- AI-first product definition;
- generation-first user experience;
- core user experience;
- Explore and Studio separation;
- investigation assistant.

Add:

- map-first workspace;
- persistent assistant panel;
- Inspector mode;
- experience-plan generation.

## 21.2 Architecture documents

Update:

- generated-investigation contract;
- frontend architecture;
- AI-agent architecture;
- spatial architecture;
- map/timeline/graph synchronization;
- investigation assistant.

Add:

- experience-plan contract;
- Experience Composer;
- assistant action contract;
- panel and workspace state;
- lens architecture.

## 21.3 Delivery documents

Update:

- development phases;
- current phase;
- backlog;
- risks and open questions;
- definition of done.

Insert Phase D0 before live discovery.

## 21.4 Decision records

Create an ADR such as:

```text
ADR — Chronicle uses a map-first investigation workspace
```

Record:

- map as persistent canvas;
- assistant panel as persistent control surface;
- article renderer moved to Inspector;
- Experience Plan is generated data;
- free-floating panels deferred;
- full-world map is not the default;
- claims do not become numbered visual nodes.

---

# 22. Phase D0 Completion Criteria

Phase D0 is complete when:

- an initial user question can transition into a map-first workspace;
- the assistant panel persists across the transition;
- the panel is resizable and collapsible;
- mobile uses an accessible bottom sheet;
- the map is bounded to the investigation;
- timeline and map state synchronize;
- at least three useful lenses render;
- systems view uses labelled historical objects;
- evidence opens from map or relationship selections;
- the current article renderer is available through Inspector;
- an `InvestigationExperiencePlan` is validated in TypeScript and Python;
- the Concert package receives a deterministic experience plan through the pipeline;
- no Concert-specific React branching exists;
- text alternatives exist for map and systems states;
- accessibility tests pass;
- existing Phase B/C tests remain passing or are intentionally extended;
- a five-person usability test plan is documented;
- a Codex handoff is prepared.

---

# 23. Explicit Deferrals

Phase D0 should not require:

- live search;
- live LLM calls;
- source downloads;
- embeddings;
- PostgreSQL;
- authentication;
- production job queues;
- automatic map discovery;
- historical boundary generation;
- autonomous Experience Composer output;
- arbitrary free-floating windows;
- complete Studio authoring.

Use existing packages and deterministic plans.

---

# 24. Immediate Claude Code Instruction

Use the following to begin:

> Add this map-first workspace update on top of the existing Chronicle AI-first and Phase D source-discovery instructions.
>
> Phase C is complete and pushed. Before beginning live source discovery, insert Phase D0: Map-First Investigation Experience.
>
> Read `AGENTS.md`, `CLAUDE.md`, the generated-investigation contract, the AI-first product documents, the Phase C implementation report, the existing Phase D plan, and this document.
>
> Before editing, return:
>
> 1. an audit of the current page and component hierarchy;
> 2. which current components move into Inspector;
> 3. proposed map-first workspace component structure;
> 4. persistent assistant-panel state model;
> 5. panel resize/collapse behaviour;
> 6. responsive and mobile approach;
> 7. timeline synchronization design;
> 8. lens architecture;
> 9. systems-view redesign;
> 10. `InvestigationExperiencePlan` schema;
> 11. Zod/Pydantic parity plan;
> 12. deterministic Concert experience plan;
> 13. migration steps;
> 14. tests;
> 15. files to create or modify;
> 16. decisions requiring Kamal's approval.
>
> Do not begin live search, live model calls, downloads, embeddings, PostgreSQL, authentication, or automatic map discovery in Phase D0.
>
> Preserve the current article/evidence renderer as Inspector rather than deleting it.
>
> Do not hard-code Concert-specific display logic in React.
>
> The map must be the primary workspace, not a tab beside Relationships.
>
> The assistant panel must begin as the initial input surface and remain available after generation.
>
> Use a docked, resizable panel on desktop and an accessible bottom sheet on mobile.
>
> Do not use numbered claim nodes as the primary systems visualization.
>
> Do not commit, push, or merge until explicitly instructed.

---

# 25. Codex Review Requirements

Codex should independently review:

## Product alignment

- Is the map genuinely primary?
- Does the assistant persist from input through investigation?
- Is evidence available without dominating the experience?
- Does Inspector preserve provenance?
- Are lenses useful rather than decorative?

## Architecture

- Is Experience Plan data-driven?
- Are package IDs validated?
- Is React free from investigation-specific branching?
- Is assistant action execution deterministic?
- Is state serializable?
- Can live Experience Composer output replace the fixture later?

## Historical integrity

- Does map scope overstate geography?
- Are routes and regions evidence-backed?
- Is uncertainty visible?
- Are modern borders presented honestly?
- Are relationships qualified?
- Are knowledge states handled safely?

## UX and accessibility

- Can the panel be resized by keyboard?
- Can the map be used without pointer input?
- Are equivalent lists available?
- Does mobile remain usable?
- Does reduced-motion work?
- Does focus survive panel changes?
- Is selection clear?

Classify findings as:

1. blocking;
2. important;
3. optional.

Codex should review first without editing.

---

# 26. Product Principle

The updated product principle is:

> **The investigation-generation pipeline creates the historical model. The Experience Composer creates a map-led interaction plan. The map is the persistent investigation canvas. The assistant is the guide and control surface. The timeline changes the visible historical state. The lenses answer different questions. The Inspector establishes trust.**
