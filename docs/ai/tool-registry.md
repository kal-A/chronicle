# Tool Registry (Phase E2)

Phase E2 provides deterministic, typed retrieval over one validated
`GeneratedInvestigation` package at a time. It contains no agent, model call,
embedding, database, web request, source download, or live discovery path.

## Corpus identity and isolation

`CorpusRegistry` loads packages lazily. Each built-in `CorpusSource` pins the
expected package ID, stable JSON hash, schema version, and package revision;
loading fails if any pin disagrees with the file. Public corpus reads and the
index escape hatch return defensive copies.

Every invocation binds four independently obtained identifiers: the typed tool
input, `ToolExecutionContext`, actual `PackageBackedCorpus`, and loaded
manifest. All four must match before execution. Record IDs are only
corpus-local: tests use two synthetic valid packages with deliberately
overlapping source, document, passage, and claim IDs to prove that lookup and
search are isolated by `(corpusId, recordId)`.

The built-in Concert of Europe and Blank Cheque packages are benchmark data,
not runtime branches. An AST-aware guard scans `chronicle.corpus`,
`chronicle.ai.tools`, and `chronicle.ai.orchestration` for literal corpus/package
ID comparisons and scans source text for known benchmark names. The explicit
data-only manifest is the sole exception.

## Discovery and invocation contracts

`ToolRegistry.list_specs()` returns sorted, JSON-serializable `ToolSpec`
objects: name/version, purpose, complete Pydantic input schema, output summary,
required capabilities, effective result limit, use/avoid guidance, and the
deterministic/current-corpus-only flags. With a context and corpus, unavailable
or unauthorized tools are omitted and advertised limits reflect the context.

`ToolExecutionContext.maximumResults` defaults to 8 and has a hard maximum of
20. `maximumOutputCharacters` defaults to 16,000 and has a hard maximum of
64,000; post-execution overflow is a failed `MalformedToolOutputError`, never
an oversized payload passed to a model. Tool-specific limits may be lower. List
outputs expose truthful totals/returned counts and truncation at their relevant
level. Relationship traversal additionally caps depth at 5, paths at 20,
prevents node revisits, and uses a sentinel candidate so `truncated` means that
another path really exists.

Successful and unsuccessful calls are auditable. A successful invocation
returns `(typed_output, ToolCallRecord)`. Typed exceptions raised for rejected,
unsupported, malformed, or failed calls carry their completed `callRecord`,
including input hash, status, timing, and sanitized error metadata. Unexpected
exceptions do not leak raw internal details.
Corpus-layer lookup failures are wrapped as audited `CorpusRetrievalError`s at
the tool boundary; direct corpus APIs retain their own error taxonomy.

## Retrieval semantics

`search_passages` is deterministic lexical retrieval. Ranking is token-aware,
stable, and explained by named `scoreFactors`; annotation density does not
inflate relevance. Every hit keeps each canonical `EvidenceLinkProjection`
attached to its target and role, together with passage/document/source IDs,
visibility, curation, locator, and limitations.

Date filtering requires explicit roles and uses interval overlap, not only an
interval's earliest bound. The represented roles are passage sent time,
passage received time, source date, linked event time, and linked actor-awareness
time. `get_timeline_context` returns those roles separately and explicitly says
that report, discovery, and interpretation times are absent unless separately
represented in a future contract.

All evidence-facing tools use one canonical projection containing evidence
link ID, typed target ID, role, review status/note, visibility, passage,
document, and source. Only role `supporting` counts as support.
`counterevidence` and `context` remain separate; contextual or qualifying
material is never silently promoted into support. The current schema's
canonical third role is `context`; prose that calls material “qualifying” is a
description, not a fourth stored evidence role.

`get_actor_knowledge_state` returns only stored `KnownAtTime` records. It
distinguishes records available from insufficient data, preserves awareness and
review fields, and marks `directOrInferred` as not recorded because the current
contract has no such field. Information existing somewhere never implies that
an actor knew it.

`get_map_context` preserves exact stored coordinates, place-period names and
controlling-polity records, marker precision, map-asset georeferencing
precision/note, source citation, attribution, license, bounds/default view, the
full represented `HistoricalDate`, geographic limitations, and unavailable
historical boundaries. It does not invent coordinates, routes, borders,
control, or finer precision.

`trace_relationships` is intentionally not named
`trace_reviewed_relationships`: it traverses stored relationships regardless of
review status and preserves both `reviewStatus` and
`evidenceClassification`. Path existence is not a causal or certainty verdict.

## Registered tools

The ten E2 tools are `search_passages`, `get_source_metadata`,
`compare_sources`, `get_claim_evidence`, `find_counterevidence`,
`get_relationship_evidence`, `trace_relationships`, `get_timeline_context`,
`get_actor_knowledge_state`, and `get_map_context`.

`compare_perspectives`, `find_conflicts`, and `get_research_gaps` remain
deferred because their package collections are untyped `ExtensionRecord`
placeholders and empty in both built-in fixtures. Planner and Analyst
orchestration begins in E3; it is not part of this phase.
