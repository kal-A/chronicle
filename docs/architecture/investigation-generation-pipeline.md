# Investigation Generation Pipeline

## Persisted Workflow

The pipeline is a resumable state machine, not a prompt chain hidden in request memory.

```text
requested → scope_proposed → awaiting_scope_approval
→ discovery → assessment → acquisition → extraction → entity_resolution
→ timeline → relationship_proposal → criticism → geography → composition
→ verification → completed | partial | failed | cancelled
```

Each stage run records status (`pending/running/succeeded/failed/skipped`), attempt, typed input/output references, start/end timestamps, error category, retryability, prompt/model versions where applicable, and concise decision summaries. Private chain-of-thought is never stored or shown.

## Stage Contracts

1. **Scope planner:** request → bounded scope proposal and discovery plan.
2. **Query decomposition:** approved scope → versioned discovery queries.
3. **Discovery:** queries/provider adapters → SourceCandidates.
4. **Assessment:** candidates/rubric → accepted, deferred, rejected decisions.
5. **Acquisition:** permitted candidates → Documents or metadata-only records.
6. **Passage processing:** Documents → stable, location-preserving Passages.
7. **Extraction:** Passages → proposed entities, events, communications, claims, dates, places, uncertainties.
8. **Entity resolution:** proposals/shared entities → matches, new candidates, unresolved queue.
9. **Timeline:** accepted records → selective evidence-linked TimelineEntries.
10. **Relationship proposal:** claims/events → mechanisms, alternatives, evidence-ledger proposals.
11. **Critic:** proposed relationships/conclusions → accept, downgrade, dispute, reject, abstain.
12. **Geographic intelligence/map discovery:** scoped records → verified place records, map candidates, MapScenes.
13. **Composition:** verified claim set → bounded synthesis/presentation/interaction specification.
14. **Verification:** package → pass/partial/block report.

## Retry and Resume

Retries are stage-specific and capped. Transient provider/network failures may retry with backoff; validation, rights, or unsupported-scope failures do not retry blindly. Successful stage outputs are immutable and reused unless their input hash or stage version changes. Resuming starts at the first invalidated/failed stage.

## Provider Boundaries

Discovery, acquisition, model generation, embeddings, and background execution use adapters. No stage imports a vendor SDK into domain code. Deterministic mocks and recorded fixtures implement the same protocols and are the only providers used in tests.

## First CLI Skeleton

```text
chronicle generate "The Concert of Europe and revolutionary intervention"
  --provider mock
  --output ./artifacts/concert-of-europe/
```

The first CLI uses deterministic fixtures to create a scope proposal, query plan, candidates, draft package, and verification report. It does not search, download, embed, or call a live model.

## Suggested Backend Package Structure

```text
backend/chronicle/
  domain/          # Pydantic domain/package schemas
  workflows/       # state machine and stage orchestration
  stages/          # bounded implementations
  providers/       # discovery/acquisition/model/embedding protocols + mocks
  repositories/    # persistence interfaces
  verification/    # deterministic rules and reports
  cli/             # generate/resume/inspect commands
  api/             # later FastAPI transport
```

