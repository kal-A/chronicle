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

## First Question Classes

1. Explain an event or connection.
2. Compare sources, accounts, actors, or institutions.
3. What was known by this date?
4. What is disputed, uncertain, or missing?

## Verification

Every material statement maps to claim IDs returned by tools in that run. Every citation maps to permitted Passages. The answer verifier checks classification wording, dispute preservation, knowledge-state support, and action references. Failure yields retry within a cap or abstention. Unreviewed material is labelled and cannot be presented as published fact.

