<!-- See 00_START_HERE.md for the encoding-fix note that applies to this whole instruction set. -->

# Chronicle — Phase E Real LLM Agent Core

[← Domain generalization and evaluation](./04_DOMAIN_GENERALIZATION_AND_EVALUATION.md) · [Next: Claude Code execution instructions →](./06_CLAUDE_CODE_EXECUTION_INSTRUCTIONS.md)

## Phase objective

> A real LLM-powered, tool-using, evaluated agent workflow answers questions over existing Chronicle corpora, verifies its claims, returns citations, and controls the map workspace through validated actions.

This phase must introduce real model calls.

## E0 — Reconcile repository state and reorient documentation

Before implementation:

1. inspect actual Git status, branches, remotes, and pushed state;
2. update stale phase documents;
3. add this instruction set to the repository;
4. update the roadmap so Phase E is AI Core;
5. record an ADR that the LLM-agent system is the product focal point;
6. move broad live source discovery to Phase F;
7. freeze unrelated UI expansion.

## E1 — Model provider and structured generation

Build:

- provider protocol;
- deterministic provider;
- one real provider;
- structured generation;
- timeouts;
- retries;
- error mapping;
- prompt/model version metadata;
- token, latency, and cost recording;
- secret/config handling.

Required tests:

- valid structured output;
- malformed output recovery;
- timeout;
- rate limit;
- provider error;
- deterministic test provider;
- model metadata persistence.

Do not hard-code business logic into provider classes.

## E2 — Corpus service and agent tools

Build deterministic tools over existing corpora:

- `search_passages`;
- `get_source_metadata`;
- `get_claim_evidence`;
- `get_relationship_evidence`;
- `get_timeline_context`;
- `get_actor_knowledge_state`;
- `compare_sources`;
- `find_counterevidence`;
- `trace_reviewed_relationships`;
- `get_map_context`.

Add tool registry, schemas, authorization, logging, result limits, corpus boundaries, and deterministic tests.

## E3 — Planner and analyst

Build the Investigation Planner and Evidence Analyst.

Requirements:

- typed inputs and outputs;
- bounded tool budget;
- model/provider metadata;
- replayable fixtures;
- no final prose from Planner;
- no uncited statements from Analyst;
- retry invalid structured output;
- abstain on unsupported requests;
- tests across at least two corpora.

## E4 — Critic and guide

Build:

- Historical Critic;
- bounded critique/retrieval loop;
- Investigation Guide;
- deterministic citation validator;
- action validator;
- final answer contract.

The Guide receives only critic-approved material.

## E5 — FastAPI and streaming agent runs

Add a narrow HTTP boundary.

Initial endpoints:

```text
POST /api/investigations/{investigation_id}/questions
GET  /api/agent-runs/{run_id}
GET  /api/agent-runs/{run_id}/events
POST /api/agent-runs/{run_id}/resume
```

Use server-sent events or polling fallback. Do not add a large REST surface.

## E6 — Real assistant integration

Replace the in-workspace Ask placeholder.

Required behavior:

- question submission;
- context snapshot;
- streaming stage updates;
- cited answer;
- limitations;
- tool-activity summary;
- optional map actions;
- conversation history;
- retry;
- abstention;
- error recovery.

The existing keyword-match entry page may remain a disclosed prototype until full new-topic generation exists, but the in-investigation assistant must become real.

## E7 — Evaluation harness

Build:

- benchmark registry;
- evaluation-case schema;
- baseline runner;
- RAG runner;
- multi-agent runner;
- metric computation;
- saved reports;
- regression thresholds.

Compare:

1. single prompt;
2. basic retrieval answer;
3. planner–analyst;
4. planner–analyst–critic–guide.

## E8 — Domain-generalization foundation

Before Phase E closes:

- move Concert-specific test content under benchmark/fixture structure;
- add at least one small non-Concert corpus;
- add a second materially different corpus or define a holdout;
- parameterize agent tests;
- add no-topic-branching checks;
- diversify prompt examples.

## E9 — Learning documentation

Create:

```text
docs/ai/
  agent-architecture.md
  tool-registry.md
  model-provider-decisions.md
  evaluation-methodology.md
  learning-log.md
```

Record model selection, structured-output failures, tool-description effects, critic effectiveness, latency, cost, and whether multiple agents were justified.

## Completion gate

Phase E is complete when:

- a real model is used;
- all four bounded agents exist;
- agent tools retrieve from existing corpora;
- answers contain valid citations;
- unsupported questions abstain;
- the Critic rejects or downgrades unsupported claims;
- map actions validate and execute;
- the assistant panel is live;
- agent runs are inspectable;
- tests use at least two corpora;
- no topic-specific application branching exists;
- evaluation compares the multi-agent workflow with simpler baselines;
- results and lessons are documented.

## Explicit exclusions

Do not include unless required for the core slice:

- unrestricted live web research;
- broad scraping;
- OCR;
- production vector database;
- full autonomous new-topic generation;
- map asset discovery;
- fine-tuning;
- public publishing;
- collaboration;
- user accounts.
