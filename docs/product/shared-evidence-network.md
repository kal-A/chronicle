# Shared Evidence Network

Chronicle should not store every investigation as a fully isolated project. Long-term, the system has shared entities — people, institutions, places, events, decisions, ideas, technologies, conditions, documents, claims, historical relationships — that a single source can inform across multiple investigations.

A source may also enter the shared library before any relevant investigation exists. Temporal/geographic coverage and entity/event links allow it to become useful later without migrating or duplicating the source.

**Example:** a source concerning Caesar in Egypt may be relevant to investigations about Caesar's Civil War, the Alexandrian War, Cleopatra and Roman power, the fall of the Ptolemaic Kingdom, the final wars of the Roman Republic, and the rise of Octavian.

## The Rule That Protects This

Newly uploaded sources must never automatically rewrite public investigations. The workflow is always:

```text
Source uploaded
  → passages extracted
  → historical entities and claims proposed
  → existing knowledge compared
  → potentially affected investigations identified
  → impact review created
  → human editor accepts, revises, disputes, or rejects each proposed impact
  → evidence-linked narrative revision proposed where warranted
  → human editor reviews and explicitly publishes a new presentation version
```

This is a hard architectural constraint, not a policy note — see `docs/architecture/provenance-and-review.md` for how it is enforced through immutable proposed revisions that remain non-public until a human accepts them into `reviewed` status and explicitly publishes them.

See `docs/architecture/source-to-narrative-enrichment.md` for how new evidence adds context, competing accounts, corrections, or qualifications to narrative text while preserving the previous public version.

## What Must Be Preserved

- Provenance (which source, which passage, which extraction run)
- Source permissions (public/private)
- Public/private state of both sources and derived entities
- Editorial review status (proposed/reviewed/disputed/rejected), kept separate from revision and publication state
- Conflicting accounts (multiple claims about the same relationship can coexist)
- Historical uncertainty (explicit, not implied by omission)
- Version history

## Sequencing

The shared evidence network is a Phase 7+ concern. Phases 1–6 build and validate a single investigation (July Crisis) deeply. Phase 7 demonstrates cross-investigation sharing with **two** connected investigations, not an attempt to model all of history — see `docs/product/product-principles.md` item 10 and `docs/delivery/development-phases.md` Phase 7. The Phase 2 domain model must use entity types (not investigation-scoped tables) from the start so this doesn't require a rewrite later — see `docs/architecture/domain-model.md`.
