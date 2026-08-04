# Source-to-Narrative Enrichment

## Goal

Chronicle must accept sources about any historical period or event without requiring an existing investigation, and must let reviewed evidence improve investigation text without silently rewriting published history.

The system separates four concerns:

```text
Source acquisition
  → evidence extraction and review
  → investigation-impact review
  → narrative revision and publication
```

A source entering the library does not itself change a historical claim or a published narrative. It creates evidence and proposals that can be inspected, accepted, revised, disputed, or rejected.

## Period-Agnostic Source Intake

A Source is global and may be created without an `investigation_id`. It records bibliographic identity, rights, language, and broad proposed coverage:

- temporal coverage using bounded `HistoricalDate` ranges, including approximate/disputed bounds;
- geographic coverage using Place/PlacePeriodRecord references and precision;
- mentioned or relevant entities/events when known;
- source type, limitations, and acquisition/processing state.

Coverage metadata may be human-entered or AI-proposed. Proposed coverage is never treated as reviewed evidence. If the source concerns a period or entity Chronicle has never modeled, the ingestion workflow may propose new Entities, Events, Places, and PlacePeriodRecords without requiring a schema change or forcing them into an existing investigation.

## Evidence Before Narrative

Documents and Passages are acquired representations of a Source. Claims, Relationships, KnownAtTime records, and entity/event proposals are extracted from Passages and pass through the review workflow first. Narrative text never cites a Source only by title when a passage-level route is available.

New evidence can have one or more effects:

- `supporting`: strengthens or adds evidence for an existing reviewed claim;
- `contradicting`: supplies counterevidence or a competing claim;
- `contextual`: adds relevant background without asserting causation;
- `qualifying`: narrows time, place, actor, certainty, or scope;
- `duplicate`: adds no material proposition but may improve provenance;
- `unrelated`: retained in the source library without affecting an investigation.

These are impact classifications, not automatic conclusions. A human reviewer confirms them.

## Evidence-Linked Narrative Model

Investigation narrative is stored as ordered **NarrativeBlock** records rather than one mutable text field. A block carries:

- stable block identity and scene placement;
- immutable revision identity;
- authored prose;
- referenced Claim/Relationship/KnownAtTime IDs;
- optional perspective/actor attribution;
- temporal and geographic scope;
- editorial status and author/reviewer metadata.

Every material historical statement in a NarrativeBlock must be backed by one or more referenced reviewed records. Transitional or purely presentational prose may remain uncited, but it cannot introduce a new historical assertion.

Multiple accounts are represented as parallel attributed Claims or NarrativeBlocks when appropriate. New evidence must not be blended into a false single consensus.

## Impact and Revision Workflow

When a new or revised reviewed record may affect an investigation, deterministic candidate selection uses shared entity, event, time, place, and existing-claim links. An optional bounded AI step may rank or explain candidates, but cannot update text.

For every material candidate, the system creates an **ImpactReview** with:

- triggering reviewed record and evidence links;
- candidate investigations, scenes, and narrative blocks;
- proposed impact classification;
- rationale and confidence/provenance for any AI contribution;
- human decision and notes.

An accepted ImpactReview can create one or more **NarrativeRevisionProposal** records. Each proposal contains:

- target NarrativeBlock or proposed new-block location;
- change kind: add context, add account, correct, qualify, dispute, replace, or no text change;
- before text and proposed after text/diff;
- exact triggering Claims/Relationships and their supporting/counterevidence;
- explanation of why the change is warranted;
- author/AI provenance and review state.

Accepting a proposal creates a new immutable NarrativeBlock revision inside a draft InvestigationPresentation version. It does not mutate the currently published version. A separate human publication action makes the new presentation version public atomically. Rejection leaves the public narrative unchanged and retains the audit record.

## Reader Transparency

Published text can expose a concise “updated with new evidence” history. A reader must be able to trace a material sentence to its reviewed records and passages, see competing accounts, and inspect earlier published narrative revisions where the product exposes version history.

The UI must distinguish:

- added context from a correction;
- a new source supporting an existing account from a genuinely new account;
- a disputed interpretation from a factual metadata correction;
- evidence availability from actor awareness at the historical time.

## Deterministic Safety Invariants

1. A Source can exist with zero investigation links.
2. Ingestion never writes into published NarrativeBlocks.
3. Only reviewed/disputed records with permitted visibility can support public narrative text.
4. Every material narrative revision identifies its triggering reviewed records.
5. Publishing is an explicit human action and atomically changes the active presentation version.
6. Superseded narrative revisions and rejected proposals are retained.
7. Removing or privatizing required evidence blocks publication of a dependent draft and flags already-published dependencies for review; it does not silently erase public text.
8. AI-generated wording is always a proposal with prompt/model/timestamp provenance.

## Required Tests When Implemented

- Add a source for a period with no existing investigation and retain it without failure or forced linkage.
- Add supporting, contradicting, contextual, qualifying, duplicate, and unrelated evidence and verify distinct ImpactReviews.
- Prove that source ingestion and proposal acceptance cannot change the active public presentation.
- Publish a reviewed narrative revision and verify the old presentation remains recoverable.
- Verify every material sentence fixture resolves to reviewed evidence.
- Verify private/rejected/proposed evidence cannot support a public narrative revision.
- Verify two conflicting accounts can coexist without either being overwritten.

