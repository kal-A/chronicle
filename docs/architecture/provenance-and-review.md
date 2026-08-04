# Provenance and Review

This is the enforcement mechanism behind `AGENTS.md` §3 and §13, and the mechanism that makes `docs/product/shared-evidence-network.md`'s "no silent public updates" rule real rather than aspirational.

## Review Status State Machine

Applies to Claim, Relationship, KnownAtTime, and any AI-extracted candidate Entity/Event/Decision:

```text
proposed → reviewed
proposed → disputed   (kept visible in Explore as a disputed item, with rationale)
proposed → rejected   (never surfaces in Explore)
reviewed → disputed   (a previously-settled item is newly contested by evidence)
disputed → reviewed   (the contest is resolved by a later reviewed revision)
```

Only `reviewed` and `disputed` states are eligible for public Explore surfaces (`disputed` is shown *as* disputed — this is a feature, not a gap, per `AGENTS.md` §3). `proposed` and `rejected` are never visible to unauthenticated/public callers, enforced at the query layer (`backend-architecture.md`).

`revised` is not a review status. Revision is an operation that creates a new immutable revision in `proposed` status, linked to the superseded revision. The previously published revision remains the public version until the new revision is reviewed or disputed and explicitly published. `accepted` is likewise an editorial action, not an additional status: accepting a proposal transitions it to `reviewed`.

## Required Fields on Reviewable Records

- `review_status` (enum above)
- `reviewer_notes` (free text, required when status is `disputed` or `rejected`, explaining why)
- `prompt_version`, `model_version`, `processing_timestamp` — set whenever the record originated from or was modified by an AI step; null for purely human-authored records
- immutable revision ID plus `supersedes_revision_id`; revision history is reconstructed from append-only revision rows

## Provenance Chain

Every Claim traces through at least one supporting EvidenceLink to a Passage; every Passage traces through a Document to a Source with recorded `source_type` and access/permission metadata (`docs/research/source-hierarchy.md`). A Claim with no traceable supporting Passage is not just unreviewed — it is structurally invalid and rejected at write time, not merely flagged for review. EvidenceLinks explicitly distinguish supporting evidence, counterevidence, and context.

## Impact Review (Phase 6+, activates the Shared Evidence Network in Phase 7–8)

When a new/changed reviewed record could affect an Investigation, the system creates an **ImpactReview** record rather than touching narrative or presentation data. Candidate discovery considers shared entities/events, temporal and geographic overlap, and existing evidence links. Impact classification is supporting/contradicting/contextual/qualifying/duplicate/unrelated and always requires human confirmation.

Accepting an ImpactReview may create NarrativeRevisionProposals, but it still does not change the active public presentation. Accepted narrative proposals create immutable block revisions in a draft InvestigationPresentation version. Only a separate explicit publish action atomically promotes that version. Full behavior and safety invariants are in `source-to-narrative-enrichment.md`.

## Permissions

`Source.rights_status` (public-domain/licensed/needs-permission), `Document.processing_needs` (for example, needs-translation), and `visibility` (public/private-workspace) are separate concerns. Visibility is carried by Documents and every derived reviewable record. A derived record may never be more public than any Passage needed to support it; promotion to public visibility is an explicit Review-service operation after permissions checks, never automatic inheritance. Public Explore endpoints require all of: `review_status IN (reviewed, disputed)`, `visibility = public`, a published InvestigationPresentation, and publicly accessible supporting evidence or an explicitly permitted public citation representation.

## Testing Requirements

- A contract test suite that specifically tries to fetch `proposed`/`rejected`/`private` content through every public endpoint and asserts it's never returned — run on every PR touching the Evidence or Review service, not just at phase boundaries.
- A test asserting that creating or publishing a revision never deletes or mutates the prior revision.
