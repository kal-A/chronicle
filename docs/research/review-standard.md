# Historical Content Review Standard

This document defines the minimum operational bar for moving Chronicle content from `proposed` to `reviewed` or `disputed`. It replaces source-count shortcuts with a claim-specific review process. Review status records editorial completion, not historical certainty.

## Roles

- **Curator:** identifies sources, extracts passages, drafts claims, and records limitations.
- **Reviewer:** checks the proposed record against its cited passages and the rules below. The reviewer must be a different review action from the proposal action; during solo development, Kamal may perform the reviewer role and record that the check was owner review rather than independent expert review.
- **Domain-expert review:** required before Chronicle presents the public investigation as historically validated. Until then, the limitations report must say that review is internal and not expert peer review.

The software must store reviewer identity, review timestamp, notes, and the exact revision reviewed. A later revision requires a new review.

## Required Checks

A Claim, Relationship, or KnownAtTime proposal can move to `reviewed` only when the reviewer confirms:

1. Every material assertion resolves to at least one exact Passage and then to its Document and Source.
2. The Passage says what the proposal says it says; editorial interpretation is not presented as document text.
3. Source type, edition/translation, rights status, and known limitations are recorded.
4. Event, report, sent, received, awareness, discovery, and interpretation times are separated wherever relevant.
5. Temporal and geographic scope are explicit, including uncertainty and location precision.
6. `direct_or_inferred` and any `evidence_classification` match the cited passages.
7. Plausible counterevidence or materially different specialist interpretations were actively checked and linked or noted as a gap.
8. No source is treated as independent corroboration of itself through a derivative edition, translation, quotation, or wartime compilation.
9. The wording does not imply causation, actor knowledge, consensus, or precision beyond the evidence.
10. Visibility and rights permit the intended public citation/passage representation.

## Evidence Bar by Record Type

- **Direct documentary statement:** One authenticated primary passage may directly support the narrow fact that its author/issuer made or received the recorded statement. It does not automatically prove the statement's truth, sincerity, reception, representativeness, or causal consequence.
- **Event metadata:** Prefer a primary record plus independent corroboration when timing, location, or identity is load-bearing. A single source may suffice for uncontested display metadata only when its limitations are recorded.
- **Actor knowledge:** Requires evidence of receipt, acknowledgment, contemporaneous discussion, or a decision that specifically presupposes the information. Mere availability elsewhere is insufficient.
- **Causal or motivational relationship:** Requires explicit support from a suitable source or a transparent inference from multiple genuinely independent sources. Significant causal claims must be checked against specialist historiography and counterevidence.
- **Disputed interpretation:** Requires at least two traceable, credible positions or a specialist source that documents the dispute. Publish the positions and their evidence; do not manufacture symmetry where the literature does not support it.
- **Insufficient evidence:** May be reviewed as an honest assessment when the search scope and missing evidence are recorded.

No numeric source count overrides these rules.

## Outcomes

- `reviewed`: the record passes the checks and its wording reflects the evidence.
- `disputed`: the record passes traceability/review checks but credible disagreement is material to its interpretation; reviewer notes are required.
- `rejected`: the record is unsupported, duplicative, misleading, outside scope, or otherwise unsuitable; reviewer notes are required.
- Remain `proposed`: review is incomplete or a resolvable evidence/metadata gap remains.

## Phase 1 Prototype Label

Phase 1 may use curated draft content to validate interaction design, but the interface and project documentation must label it as prototype content. It may not be described as publicly reviewed historical content until the checks above have been completed and logged.

