# Phase E2 Implementation Report — Corpus Service and Typed Tools

Phase E2 implements a deterministic corpus and tool boundary over existing,
validated `GeneratedInvestigation` packages. The implementation is still
uncommitted and unpushed. It does not start Phase E3.

## Delivered

- `backend/src/chronicle/corpus/`: strict request/result contracts, validated
  package loading, immutable public reads, derived indexes, deterministic
  lexical search, and lazy manifest registration with expected package
  ID/hash/schema/revision pins.
- `backend/src/chronicle/ai/tools/`: ten typed retrieval tools, serializable
  Planner-facing `ToolSpec`s, four-way corpus binding, capability and result
  limits, canonical EvidenceLink projections, and success/failure audit
  records.
- `backend/src/chronicle/cli/`: `corpus list/inspect/search` and
  `tools list/invoke`; malformed JSON and every non-object JSON value are clean
  exit-code-2 input errors rather than crashes.
- Tests across both real benchmark corpora plus synthetic valid corpora whose
  record IDs deliberately overlap while their content differs.

The registered tools are `search_passages`, `get_source_metadata`,
`compare_sources`, `get_claim_evidence`, `find_counterevidence`,
`get_relationship_evidence`, `trace_relationships`, `get_timeline_context`,
`get_actor_knowledge_state`, and `get_map_context`.

## Corrected guarantees

- Input/context/corpus/manifest identities must all agree. Built-in package
  contents are pinned, and record IDs are treated as corpus-local.
- Search is token-aware, deterministically ranked, and role-preserving. Each
  evidence role stays attached to its typed target.
- Date filtering is role-explicit and interval-aware. Timeline output keeps
  sent, received, source, linked-event, and actor-awareness times distinct.
- Only supporting EvidenceLinks count as support in source comparison;
  counterevidence and context remain separate. “Qualifying” prose is not
  promoted to support or modeled as an invented fourth role.
- Relationship traversal is honestly named `trace_relationships`, preserves
  raw review/evidence fields, is cycle-safe, and reports real truncation.
- Knowledge lookup reports records-available versus insufficient-data and does
  not infer actor awareness or an unavailable direct/inferred classification.
- Map output preserves marker/place precision, georeferencing notes, the full
  represented period, boundary gaps, and geographic limitations.
- Result-producing tools obey the execution context's conservative default cap
  of 8 (hard maximum 20), with truthful total/returned/truncation metadata.
- Serialized tool output is also capped at 16,000 characters by default
  (64,000 hard maximum); an implementation that exceeds it fails audibly
  instead of overflowing a local-model prompt.
- Failed, rejected, and unsupported calls raise typed errors carrying complete
  `ToolCallRecord`s; corpus failures are wrapped at the tool boundary and
  unexpected failures expose sanitized messages without chained tracebacks.

## Verification evidence

The authoritative closeout commands are:

```powershell
$env:PYTHONPATH='<temporary-dependencies>;D:\Full time Grind\projects\Chronicle\backend\src'
C:\Python314\python.exe -m pytest -q
C:\Python314\python.exe -m pytest tests\corpus tests\ai\tools tests\cli -q
```

Fresh post-integration verification passed: **514 passed, 4 skipped, 1
deselected** in the full backend suite. The explicitly excluded test is the
local-Ollama integration smoke test. The E2-facing corpus/tool/CLI slice passed
**397 tests with 4 skips**; the expanded E2 slice including contract-invalid
fixture regressions passed **407 tests with 4 skips**. These are collected
test-case totals (including
parametrized cases), replacing the false pre-correction “230 new tests” count.

The unchanged frontend also passed typecheck, lint, production build, all
**103 unit tests**, and all **14 Playwright journeys** after the shared
Python/TypeScript package-validation correction.

Manual CLI coverage includes list and inspect for corpora, lexical search,
Planner-safe tool listing, valid JSON tool invocation, unknown corpus/tool,
schema-invalid input, malformed JSON, and non-object JSON (`[]`, `null`,
string, number, boolean).

## Explicitly absent and deferred

There are no Planner, Analyst, Critic, Guide, FastAPI endpoint, frontend
assistant changes, embeddings, network calls, live retrieval, downloads,
database infrastructure, or paid runtime provider in E2. The Concert of Europe
package is one benchmark alongside Blank Cheque, never a product-specific code
path. `compare_perspectives`, `find_conflicts`, and `get_research_gaps` remain
deferred until their data contracts and real records exist.

Known infrastructure limitation: the repository's backend `.venv` is damaged
in this checkout, so verification uses the system Python plus an isolated
temporary dependency directory. This does not change project files or runtime
behavior.
