# AI-First Product Definition

## Product

Chronicle is an AI-powered historical investigation generator and interactive systems atlas. A user supplies a topic, event, person, period, comparison, source, or historical question. Chronicle proposes a bounded scope, builds a traceable source corpus, constructs a claim-centered historical model, and returns a draft interactive investigation that users can inspect, challenge, navigate, and extend.

> The investigation-generation pipeline is Chronicle. The frontend is the environment in which users inspect, challenge, navigate, and extend what that pipeline produces.

## Core Output

A generated investigation contains a scoped synthesis, major actors and institutions, events and decisions, communications, a selective timeline, evidence-backed geographic scenes, proposed and criticized relationships, perspectives and conflicts, actor knowledge states, uncertainties, research gaps, sources and passages, interaction actions, and a generation report.

The output is a draft, not autonomous historical truth. It must distinguish reviewed evidence, generated proposals, disputed interpretations, unsupported questions, and missing coverage.

## Trust Model

```text
User request
→ bounded scope proposal
→ auditable discovery and acquisition
→ claim-centered extraction
→ relationship proposal and criticism
→ deterministic verification
→ generated draft + coverage/limitations report
→ optional human correction/review
→ reusable or publishable version
```

Deterministic software owns permissions, workflow state, persistence, citation resolution, source visibility, rights gates, date validation, geographic precision, package validation, and publication. Models handle ambiguous language and bounded proposals. No model output bypasses validation.

## Current Prototype

The Blank Cheque experience is retained as:

- a renderer and evidence-inspection prototype;
- a golden valid investigation fixture;
- a regression test for package validation and cross-facet interactions;
- a historical-integrity reference case.

It is not the product's manually authored content template. No additional hand-authored scenes should be added before the generic package contract and deterministic mock generation pipeline exist.

## Initial Supported Domain

The initial domain is European diplomatic and political history, 1814–1914, beginning with bounded, well-documented crises and congresses. This limits retrieval, evaluation, geography, and historiography to a tractable testbed without encoding the period into the schema. See `supported-domain-strategy.md`.

## Non-Goals

- Universal reliable generation for all history at launch.
- A general history chatbot.
- One-prompt investigation generation.
- Unrestricted autonomous web browsing or scraping.
- Metadata or search snippets presented as evidence.
- Automatic publication or silent narrative mutation.
- Decorative graphs or period-map images without evidence, rights, and georeferencing discipline.

