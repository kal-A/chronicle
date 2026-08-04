# Source Hierarchy

Sources feeding any Chronicle investigation are classified by type and evidentiary weight. This classification is stored per-source (`source_type` on the domain model) and drives how the assistant may cite it and how confidently the UI may present claims derived from it.

## Source Types (highest to lowest evidentiary weight for direct claims)

1. **Primary — official/diplomatic record.** Telegrams, cables, cabinet minutes, treaties, ultimatums, official correspondence between named actors. Strongest basis for "what was said/decided/known by whom, when."
2. **Primary — personal record.** Diaries, private letters, memoirs written close to the events (with the caveat that memoirs written years later carry hindsight risk and should be flagged as such).
3. **Primary — press record of the period.** Contemporary newspaper reporting. Useful for what was publicly known/reported, weaker for establishing private intent or actual decision-making.
4. **Secondary — specialist historiography.** Peer-reviewed or widely-recognized academic historical works analyzing primary sources. Best source for causal interpretation and for identifying genuine scholarly disagreement.
5. **Secondary — general historiography.** Reputable general histories, encyclopedic treatments. Useful for context and scope-setting, weaker for disputed-claim resolution — defer to specialist historiography when they conflict.
6. **Tertiary — reference material.** Encyclopedias, textbooks, structured datasets (e.g., historical gazetteers for place records). Used for supporting metadata, not as sole support for a contested claim.

## Rules

- A claim's `direct_or_inferred` status and `relationship_type` (see `historical-methodology.md`) must be set based on what the *cited sources* actually establish, not on source type alone — a primary source can still only indirectly support a claim, and a secondary source can directly state one.
- Where sources at different levels conflict, the conflict itself is recorded (as a `disputed` relationship or as parallel claims), never silently resolved by picking the "higher" source.
- AI-assisted extraction must record which source(s) and passage(s) a proposed claim came from before it can enter the human review queue; a claim with no traceable source is rejected automatically, not queued.
- Modern secondary works about historical geography are evidence for period *place records*, not license to reuse modern political borders as historical fact (`historical-methodology.md`).

## Review Bar

The operational bar for `reviewed` and `disputed` content is defined in `review-standard.md`. It is claim-specific rather than a universal source count: a primary document can directly establish that its author made a statement without proving the statement true or causally decisive, while causal, motivational, and actor-knowledge claims require broader checks. No content becomes reviewed merely because it cites one primary source or two secondary sources.
