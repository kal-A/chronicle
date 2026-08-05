<!-- See 00_START_HERE.md for the encoding-fix note that applies to this whole instruction set. -->

# Chronicle — Product and Roadmap Reset

[← Start here](./00_START_HERE.md) · [Next: Agent architecture →](./02_AGENT_ARCHITECTURE.md)

## 1. Revised product definition

Chronicle is:

> **A domain-specialized LLM and multi-agent system that investigates historical questions, retrieves evidence, constructs and critiques historical claims, and controls an interactive map workspace through validated actions.**

Chronicle should demonstrate:

- LLM orchestration;
- typed tool use;
- retrieval-augmented generation;
- agent specialization;
- evidence-grounded reasoning;
- source comparison;
- temporal reasoning;
- relationship analysis;
- critic and verifier loops;
- abstention;
- map and timeline control;
- evaluation;
- later task-specific fine-tuning.

The historical domain is selected because it is interesting, difficult, source-rich, temporally complex, and suited to testing grounded reasoning.

## 2. What Chronicle is not

Chronicle is not primarily:

- a Concert of Europe article;
- a historical website with an AI chat box;
- a manually authored map viewer;
- a collection of static case studies;
- a source-card dashboard;
- a generic chatbot;
- an LLM that scrapes arbitrary pages without controls;
- a claim that a foundation model was trained from scratch.

## 3. Meaning of "a Chronicle LLM"

### Current target

Build a **domain-specialized LLM system** using:

- a base model;
- Chronicle prompts;
- Chronicle tools;
- Chronicle retrieval;
- Chronicle agent roles;
- Chronicle validators;
- Chronicle evaluation;
- Chronicle historical datasets.

### Later expansion

Fine-tune a smaller open-weight model for one bounded Chronicle task such as:

1. claim–evidence classification;
2. unsupported-claim detection;
3. relationship classification;
4. source-role classification;
5. contradiction or counterevidence detection.

Do not begin by fine-tuning the entire assistant.

## 4. Existing work reinterpreted

| Existing capability | New AI-core role |
|---|---|
| Workflow engine | Agent orchestration and run persistence |
| Stage records | Agent and tool audit trail |
| Pydantic/Zod parity | Structured model output enforcement |
| GeneratedInvestigation | Historical model and output contract |
| ExperiencePlan | AI-generated interaction contract |
| Ask panel | Live LLM interface |
| Map workspace | Agent-controlled exploration canvas |
| Inspector | Evidence, provenance, and agent audit surface |
| Curated corpora | Retrieval and evaluation datasets |
| Mock providers | Deterministic test doubles |
| Relationship validation | Critic and verifier safeguards |

## 5. Revised roadmap

### Phase E — Real LLM Agent Core

Build a real, evaluated, tool-using multi-agent workflow over existing curated corpora.

### Phase F — Autonomous Source Discovery

Add live scholarly, archive, library, and controlled web discovery.

### Phase G — Document Acquisition and RAG Corpus

Add permitted downloading, HTML/PDF/OCR processing, stable passages, embeddings, hybrid search, and reranking.

### Phase H — Historical Model Generation

Generate actors, events, dates, decisions, communications, claims, knowledge states, timelines, and relationship proposals.

### Phase I — Chronicle Task Model Experiment

Create a reviewed dataset and fine-tune a small model for one bounded historical-reasoning task.

### Phase J — AI Geographic and Experience Composer

Generate map scope, lenses, routes, story sequences, system paths, and experience plans.

### Phase K — Full Autonomous Investigation

A new topic proceeds from search through corpus construction, historical modelling, map generation, assistant interaction, review, and publication.

## 6. Frontend freeze

Until the Phase E AI core works, avoid:

- new static investigations;
- extensive UI polish;
- new map lenses without an AI consumer;
- additional hand-authored provider sets;
- more deterministic "generation" simulations;
- unrelated schema expansion.

Only make frontend changes required to:

- connect the live assistant;
- display agent stages;
- show tool activity summaries;
- show citations and verification;
- execute validated actions;
- surface abstention and errors.

## 7. Updated phase gate

Phase E does not pass because one Concert of Europe question works.

It passes only when:

- the real agent workflow operates across at least two materially different corpora;
- unsupported questions abstain;
- citation validity is measured;
- map actions validate;
- no topic-specific application branching is introduced;
- the agent workflow is compared with a single-prompt and basic-RAG baseline.
