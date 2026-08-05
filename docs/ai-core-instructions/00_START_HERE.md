<!--
Source document supplied by Kamal, preserved with only mechanical
encoding-corruption fixes (em dashes, arrows, and list bullets that were
mangled by a copy-paste re-encoding) — no wording was added, removed, or
reworded. See docs/decisions/ADR-003-llm-agent-system-is-product-core.md
for how Chronicle responded to this instruction set (Phase E0).
-->

# Chronicle AI Core — Start Here

## Purpose

This instruction set re-centres Chronicle around its actual product and portfolio objective:

> **Chronicle is a domain-specialized LLM and multi-agent historical investigation system. Historical research is the domain in which the AI system is developed, evaluated, demonstrated, and improved.**

The map-first workspace, evidence model, workflow engine, package contract, Inspector, and deterministic providers remain valuable. They are infrastructure serving the AI system rather than separate product goals.

Claude Code must read this document first, then follow the linked documents in order.

## Required reading order

1. [Product and roadmap reset](./01_PRODUCT_AND_ROADMAP_RESET.md)
2. [Agent architecture](./02_AGENT_ARCHITECTURE.md)
3. [Retrieval, source, API, and MCP infrastructure](./03_RETRIEVAL_SOURCE_AND_MCP_INFRASTRUCTURE.md)
4. [Domain generalization and evaluation](./04_DOMAIN_GENERALIZATION_AND_EVALUATION.md)
5. [Phase E implementation plan](./05_PHASE_E_AI_CORE_IMPLEMENTATION_PLAN.md)
6. [Claude Code execution instructions](./06_CLAUDE_CODE_EXECUTION_INSTRUCTIONS.md)

## Existing foundations to preserve

Do not discard or bypass:

- the Python workflow engine;
- resumable stage persistence;
- Pydantic/Zod contract parity;
- `GeneratedInvestigation`;
- `InvestigationExperiencePlan`;
- source → document → passage → evidence-link provenance;
- claim and relationship validation;
- map-first workspace;
- persistent assistant panel;
- Inspector;
- existing curated corpora;
- deterministic providers and tests;
- accessibility and Playwright coverage.

These foundations should now support:

- real model calls;
- agent planning;
- tool use;
- retrieval;
- critic and verification loops;
- cited answers;
- typed map actions;
- evaluation;
- future task-specific fine-tuning.

## Immediate product correction

Chronicle is currently AI-ready but not yet an AI product.

The next phase must introduce a real LLM-backed agent workflow over the existing corpora before broad autonomous web research.

The first real user outcome is:

> A user asks a historical question inside an existing investigation. A planner chooses tools, an evidence analyst builds a structured answer, a critic challenges it, a response composer returns verified citations, and the workspace executes validated map actions.

## Non-negotiable principle

> **The LLM-agent system is the product. The historical domain is the proving ground. The map is the interaction surface. The Inspector is the trust surface.**

## Scope discipline

Do not implement every future agent, source provider, ingestion format, model, and map generator in one phase.

Build the smallest complete real-AI vertical slice first:

```text
Question
→ planner
→ deterministic retrieval tools over an existing corpus
→ evidence analyst
→ historical critic
→ response composer
→ citation verification
→ typed map actions
→ assistant UI
→ evaluation
```

After that works across more than one corpus, add autonomous source discovery and document ingestion.
