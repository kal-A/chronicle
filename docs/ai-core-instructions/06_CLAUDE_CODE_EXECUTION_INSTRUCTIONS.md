<!--
See 00_START_HERE.md for the encoding-fix note that applies to this whole
instruction set. This file's file-tree diagrams were reconstructed with
standard box-drawing characters (the exact glyphs were lost to the same
copy-paste corruption) — directory/file names and nesting are unchanged.
-->

# Claude Code — Execution Instructions for Chronicle AI Core

[← Phase E plan](./05_PHASE_E_AI_CORE_IMPLEMENTATION_PLAN.md) · [Return to start](./00_START_HERE.md)

## Mission

Reorient Chronicle so its main product and engineering story is a real domain-specialized LLM and multi-agent system.

The historical domain remains central, but it must serve as the data, evaluation, and interaction context for the AI system rather than becoming one event-specific research website.

## Read before doing anything

Read:

1. `AGENTS.md`;
2. `CLAUDE.md`;
3. current-phase and revised-development-phase documents;
4. AI-first product documents;
5. map-first workspace instructions;
6. generated-investigation contract;
7. experience-plan contract;
8. workflow-engine architecture;
9. provenance and review architecture;
10. every document in this instruction set, starting with `00_START_HERE.md`.

## First response required before editing

Return an audit and proposed plan containing:

1. actual Git status and whether current phase claims are stale;
2. current Python/backend structure;
3. current frontend Ask-panel integration points;
4. current workflow-engine extension points;
5. current corpus and retrieval interfaces;
6. current model-provider abstractions, if any;
7. reusable files and components;
8. blockers to real model calls;
9. proposed agent-run data model;
10. proposed model-provider interface;
11. proposed tool registry;
12. proposed four-agent orchestration;
13. FastAPI integration plan;
14. frontend streaming plan;
15. evaluation architecture;
16. cross-domain benchmark plan;
17. exact smallest first vertical slice;
18. files to create or modify;
19. commands and tests;
20. decisions requiring Kamal's approval.

Do not start implementation until this audit is approved.

## Required architectural decisions

### Agents

Begin with exactly:

1. Investigation Planner;
2. Evidence Analyst;
3. Historical Critic;
4. Investigation Guide.

Do not add more agents until evaluation proves a need.

### Tools

Retrieval and database operations are deterministic typed tools. Do not turn every operation into an agent.

### Model

Support a deterministic test provider, one real provider, and a future open-weight or fine-tuned provider. Do not integrate several providers at once.

### Corpus

Use existing Chronicle corpora for the first real AI slice. Do not add unrestricted web search before the in-corpus workflow works.

### Generalization

All generic agent code must work across multiple corpora. Do not add topic-specific branches.

## Recommended first vertical slice

Implement:

```text
Question inside existing investigation
→ real Planner
→ search_passages / get_claim_evidence / get_timeline_context
→ real Evidence Analyst
→ deterministic citation validation
→ cited answer in Ask panel
```

Use one real provider in development and deterministic fixtures in tests.

Then add the Critic, Guide actions, additional tools, FastAPI streaming, and evaluation as separately approved slices.

## Suggested backend structure

```text
backend/src/chronicle/
├── ai/
│   ├── models/
│   │   ├── protocol.py
│   │   ├── deterministic.py
│   │   └── real_provider.py
│   ├── prompts/
│   │   ├── planner.py
│   │   ├── analyst.py
│   │   ├── critic.py
│   │   └── guide.py
│   ├── agents/
│   │   ├── planner.py
│   │   ├── analyst.py
│   │   ├── critic.py
│   │   └── guide.py
│   ├── tools/
│   │   ├── registry.py
│   │   ├── passages.py
│   │   ├── evidence.py
│   │   ├── timeline.py
│   │   ├── relationships.py
│   │   ├── knowledge.py
│   │   └── map_context.py
│   ├── orchestration/
│   │   ├── runner.py
│   │   ├── policies.py
│   │   └── validation.py
│   ├── contracts/
│   │   ├── plan.py
│   │   ├── analysis.py
│   │   ├── critique.py
│   │   ├── answer.py
│   │   └── actions.py
│   └── evals/
│       ├── cases.py
│       ├── runner.py
│       ├── metrics.py
│       └── reports.py
├── corpus/
│   ├── protocol.py
│   ├── fixture_corpus.py
│   ├── search.py
│   └── traversal.py
└── api/
    ├── app.py
    ├── questions.py
    ├── runs.py
    └── events.py
```

Simplify if appropriate, but preserve clear boundaries.

## Required implementation properties

- structured outputs;
- typed tools;
- bounded loops;
- replayability;
- prompt and model versioning;
- citation validation;
- action validation;
- abstention;
- timeout and retry policies;
- agent-run persistence;
- no chain-of-thought storage;
- deterministic test provider;
- cross-domain tests;
- cost and latency recording.

## Required user-visible behavior

The in-workspace Ask panel must eventually show:

- user question;
- stage status;
- concise tool-use summary;
- answer;
- citations;
- limitations;
- verification outcome;
- suggested follow-ups;
- optional map actions.

Do not show hidden chain-of-thought.

## Required tests

- Planner structured output;
- tool selection;
- invalid tool rejection;
- retrieval correctness;
- Analyst evidence references;
- Critic downgrade/reject/abstain;
- citation validity;
- action validity;
- provider failure;
- timeout;
- retry;
- run resume;
- cross-corpus parameterization;
- unsupported question;
- baseline comparison;
- frontend assistant journey;
- accessibility.

## Documentation updates

Add or update:

```text
docs/
├── ai/
│   ├── agent-architecture.md
│   ├── tool-registry.md
│   ├── model-provider-decisions.md
│   ├── evaluation-methodology.md
│   └── learning-log.md
├── decisions/
│   └── ADR-chronicle-llm-agent-system-is-product-core.md
└── delivery/
    ├── revised-development-phases.md
    ├── phase-e-ai-core-plan.md
    └── phase-e-validation-plan.md
```

## Codex handoff

After each approved slice, prepare a read-only Codex review covering:

- whether the slice genuinely adds AI capability;
- whether deterministic code and agents are separated properly;
- whether outputs are grounded;
- whether tool permissions are bounded;
- whether topic-specific logic was introduced;
- whether evaluation supports the design;
- whether private reasoning is stored;
- whether failures and abstention are honest.

Classify findings as blocking, important, or optional.

## Final instruction

Do not continue growing the historical UI around placeholder AI.

Build the actual LLM-agent system now, one evaluated vertical slice at a time.
