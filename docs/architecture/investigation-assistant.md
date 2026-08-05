# Investigation Assistant Architecture

## Boundary

The assistant operates only over an approved generated package and its permitted corpus. It has no unrestricted database or web access.

## Initial Typed Tools

- `search_passages`
- `get_source_metadata`
- `get_claim_evidence`
- `compare_sources`
- `compare_perspectives`
- `get_timeline_context`
- `get_actor_knowledge_state`
- `trace_reviewed_relationships`
- `get_map_context`
- `find_conflicts`
- `find_research_gaps`
- `focus_timeline`
- `focus_map`
- `highlight_relationship_path`
- `open_evidence`

Read tools enforce package/workspace/visibility boundaries. UI tools return typed actions that the frontend validates; the model never emits arbitrary JavaScript.

**Phase D update:** the four UI tools above (`focus_timeline`, `focus_map`, `highlight_relationship_path`, `open_evidence`) are the assistant-facing subset of the broader typed `AssistantAction` union the map-first workspace dispatches (`docs/product/map-first-workspace-instructions.md` §15) — `SET_TIME`/`SET_TIME_RANGE`, `ACTIVATE_LENS`, `HIGHLIGHT_EVENTS`, `SHOW_SYSTEM_PATH`, `COMPARE_ACTORS`, `OPEN_SOURCE`, and `RESET_VIEW` are new siblings, all executing by calling the same frontend selection/focus state the existing four tools already target — not a second, parallel action system. See `docs/decisions/ADR-002-map-first-workspace.md`.

**Phase E update:** the single "assistant" pipeline described in this document is now formalized as four bounded agents — Investigation Planner, Evidence Analyst, Historical Critic, Investigation Guide — each with a typed Pydantic input/output contract, per `docs/ai-core-instructions/02_AGENT_ARCHITECTURE.md` and `docs/decisions/ADR-003-llm-agent-system-is-product-core.md`. This is a naming/typing concretization of the same bounded-pipeline shape already described here (query planning → tool calls → answer composition → verification), not a conflicting redesign: "the answer verifier" below is the Historical Critic; "answer composition" is the Evidence Analyst plus Investigation Guide split into evidence-gathering and user-facing-answer responsibilities. The tool list above is Phase E's actual E2 tool registry, reused as specified, not reinvented. `search_passages`/`get_claim_evidence`/`get_timeline_context` are explicitly the three tools document `06`'s recommended first vertical slice wires up first.

## First Question Classes

1. Explain an event or connection.
2. Compare sources, accounts, actors, or institutions.
3. What was known by this date?
4. What is disputed, uncertain, or missing?

## Verification

Every material statement maps to claim IDs returned by tools in that run. Every citation maps to permitted Passages. The answer verifier checks classification wording, dispute preservation, knowledge-state support, and action references. Failure yields retry within a cap or abstention. Unreviewed material is labelled and cannot be presented as published fact.

