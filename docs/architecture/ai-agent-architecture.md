# AI Agent Architecture

> **AI-first extension:** This document's safety principles remain binding. The complete generation workflow and stage boundaries are now defined in `investigation-generation-pipeline.md`; assistant-specific tools are in `investigation-assistant.md`.

## Governing Principle

No autonomous agent swarms. Prefer explicit state machines, typed inputs/outputs, small bounded tools, deterministic validation, human review, and auditable execution (`AGENTS.md` §4). Every AI component below is a *bounded* step with a defined input/output contract, not an open-ended agent given broad goals and free rein.

## Two Distinct AI Subsystems

### 1. Source Processing (Studio-side, Phase 5+)

Bounded, mostly single-purpose steps, run in sequence with human checkpoints, not a single "process this document" agent:

- **Source classification** — typed output: source_type guess + confidence.
- **Passage segmentation assistance** — proposes passage boundaries; human confirms.
- **Metadata extraction** — author/date/origin fields, typed Pydantic output.
- **Event/actor/date/place extraction** — proposes candidate Event/Person/Place records with source passage references. Every proposal is untraceable-source-rejected automatically (`docs/research/source-hierarchy.md`).
- **Claim extraction** — proposes Claims linked to Passages.

All outputs land in `proposed` state (Review service, `provenance-and-review.md`) and require human action to progress.

### 2. Historical Understanding (supports both Studio and the Assistant)

- **Entity resolution** — proposes "this extracted mention is likely the same as existing canonical Entity X," never auto-merges.
- **Temporal interpretation** — proposes date_type/date fields from ambiguous text ("early July" → range).
- **Relationship proposal** — proposes a Relationship + its `evidence_classification` (`historical-methodology.md`), always as a proposal.
- **Supporting/counterevidence retrieval** — pgvector similarity + structured filtering over reviewed Documents/Passages.
- **Conflicting-account detection** — flags where two reviewed Claims about the same Relationship disagree; surfaces for human/editorial attention, does not resolve.
- **Research-gap detection** — flags Relationships/Decisions with `insufficient evidence` or missing KnownAtTime coverage.
- **Investigation-impact analysis** (Phase 8) — given a new/changed Claim, proposes which Investigations' InvestigationPresentation records might need review.

### 3. User Assistance (the Investigation Assistant, Phase 4)

A bounded pipeline, not a free agent loop:

```text
User question
  → query planner (classifies question into one of the supported question types,
     docs/product/investigation-assistant.md)
  → bounded tool calls against stored, status-labelled corpus data:
       source_search, source_compare, relationship_trace,
       timeline_context, map_context, actor_knowledge_reconstruction,
       evidence_gap_detection
  → answer composition (must cite the specific Claims/Passages/Relationships used)
  → verification pass (checks every citation in the draft answer actually
     resolves to data returned by a tool call in this run and is eligible for
     the intended use under its review status and visibility — reject/retry
     if not)
  → answer + UI actions (focus timeline/map/graph, open evidence)
```

The query planner and verification pass are the two places most likely to need iteration; both are deterministic checks wrapping the LLM call, not additional LLM calls trusted blindly.

Phase E2 retrieval deliberately preserves proposed, disputed, rejected, and
private records instead of silently erasing the evidence ledger. Tool outputs
surface review and visibility metadata; the E3/E4 orchestration and validation
layers must deterministically prevent ineligible records from being cited or
published as reviewed fact.

**Phase D update:** the assistant's UI-action output is now the typed `AssistantAction` union (`docs/product/map-first-workspace-instructions.md` §15, `docs/decisions/ADR-002-map-first-workspace.md`) — `FOCUS_LOCATION`, `FOCUS_EVENT`, `SET_TIME`, `SET_TIME_RANGE`, `ACTIVATE_LENS`, `HIGHLIGHT_EVENTS`, `HIGHLIGHT_RELATIONSHIP`, `SHOW_SYSTEM_PATH`, `COMPARE_ACTORS`, `OPEN_EVIDENCE`, `OPEN_SOURCE`, `RESET_VIEW`, superseding this section's looser "focus timeline/map/graph, open evidence" phrasing with a concrete, package-ID-validated action set. The assistant panel is also the initial (pre-generation) Ask entry surface, not only a post-generation feature — the query planner's first classification step now includes "this is a new investigation request," not just in-investigation question types.

**Phase E update:** the AI-agent system is now the product core, not one of several application features (`docs/decisions/ADR-003-llm-agent-system-is-product-core.md`, `docs/ai-core-instructions/`). The "query planner" and bounded-tool-call pipeline described in subsystem 3 above are now the four named, separately-typed agents — Investigation Planner, Evidence Analyst, Historical Critic, Investigation Guide (`docs/ai-core-instructions/02_AGENT_ARCHITECTURE.md`) — this document's "Governing Principle" (no autonomous agent swarms, bounded steps, typed contracts) already anticipated exactly this shape and needs no revision. The real model provider is local and open-weight via Ollama, per `AGENTS.md` §5's existing no-paid-infrastructure constraint (not a new exception) — every AI-orchestration path still requires the deterministic mock/test provider this document's "Testing" section already calls for; Ollama being free rather than paid does not relax that requirement.

## Tool Contracts

Each bounded tool above has a typed Pydantic input/output schema, defined and versioned in the backend's AI orchestration layer (`backend-architecture.md`). Tool schemas are documented alongside their implementation, not duplicated here — this file defines the *shape* of the system, not the current field-level schemas.

## Prompt/Model Versioning

Every AI-generated field records `prompt_version` and `model_version` (`domain-model.md`). Prompt changes are versioned deliberately (not silently edited in place) so that reviewers and auditors can tell which extraction run produced a given proposal.

## Testing

Every AI-orchestration path has a deterministic mock provider (`AGENTS.md` §6) so pipeline logic (routing, validation, state transitions) is tested without live inference; live-inference quality is evaluated separately via a small hand-curated eval set per question type, not via unit tests asserting exact model output.
