# Generated Investigation Contract

## Boundary

`GeneratedInvestigation` is the versioned interchange contract between the generation pipeline and renderer. It is a self-describing package, not a database dump and not a replacement for normalized persistence. The backend persists normalized workflow/domain records and exports a validated package; the frontend accepts only supported package versions.

## Top-Level Shape

```ts
type GeneratedInvestigation = {
  schemaVersion: string;
  packageId: string;
  packageRevision: number;
  generatedAt: string;
  request: InvestigationRequest;
  scope: InvestigationScope;
  status: "draft" | "partial" | "verified" | "reviewed" | "published";

  presentation: {
    title: string;
    synthesis: NarrativeBlock[];
    findings: FindingReference[];
    sceneIds: string[];
    perspectiveIds: string[];
  };

  entities: Entity[];
  events: EventRecord[];
  decisions: Decision[];
  communications: Communication[];
  knowledgeStates: KnownAtTime[];
  claims: Claim[];
  relationships: Relationship[];
  perspectives: Perspective[];
  conflicts: SourceConflict[];
  uncertainties: Uncertainty[];
  researchGaps: ResearchGap[];

  sources: Source[];
  documents: Document[];
  passages: Passage[];
  evidenceLinks: EvidenceLink[];
  claimLedgers: ClaimEvidenceLedger[];

  timeline: TimelineEntry[];
  mapAssets: HistoricalMapAsset[];
  mapScenes: MapScene[];
  scenes: InvestigationScene[];
  interactionSpec: InteractionSpecification;

  generationReport: GenerationReport;
};
```

Existing domain concepts from `domain-model.md` remain canonical. Actors, institutions, and locations are typed Entities rather than duplicate top-level types. Decisions may extend Event records but have explicit decision fields. Timeline entries reference events; they do not duplicate event truth. Presentation blocks reference claims; they cannot introduce material claims only in prose.

## Request and Scope

`InvestigationRequest` stores the raw user input, request class, requested depth/focus, optional constraints, and creation metadata. `InvestigationScope` stores interpreted question, date/geographic bounds, themes, core candidate entities, inclusions, exclusions, ambiguity decisions, expected outputs, approval state, and revision history.

## Provenance

Every AI-proposed record carries `stageRunId`, `promptVersion`, `modelProvider`, `modelVersion`, and `processingTimestamp`. Every stage run belongs to a workflow run and records typed input/output hashes. Claim ledgers resolve evidence through `EvidenceLink → Passage → Document → Source` and distinguish supporting, contradicting, qualifying, and contextual roles.

## Package Validation

A package is invalid when any of the following holds:

- IDs are not unique or references do not resolve.
- A material NarrativeBlock lacks claim/relationship/knowledge-state references.
- A major synthesis claim lacks a claim ledger and supporting Passage.
- Proposed/rejected/private evidence is used in a public package.
- Relationship classification lacks the evidence required by its class.
- A disputed relationship lacks disagreement/counterevidence representation.
- Date bounds are invalid or time roles are collapsed.
- Location or map precision exceeds its evidence/georeference support.
- Displayed map assets lack rights and period-fit decisions.
- Required verification checks did not pass or abstain.

Partial packages may intentionally omit capabilities, but omissions and failed stages must appear in `GenerationReport` and cannot masquerade as complete.

## Versioning

- `schemaVersion` uses semantic versioning for the interchange schema.
- Additive optional fields are minor changes; removals or semantic changes are major.
- `packageRevision` is immutable and monotonically increases per investigation.
- The renderer supports an explicit version range and rejects unknown major versions.
- Migrations are pure, tested transformations that preserve provenance; original packages remain stored.

## Golden Fixture

The existing Scene 2 data becomes `fixtures/blank-cheque.golden-investigation.json`. It must be produced from or validated against the same schema used by backend output. Tests load the JSON rather than importing July Crisis TypeScript content directly. The package remains `prototype-curated`, not historically peer-reviewed.

## Phase B Implementation Mapping

The frontend contract is implemented in `src/features/investigation/model/generatedInvestigation.ts`. Canonical package evidence links live at the top level and records reference them by ID. `normalizeInvestigationScene` rehydrates the embedded evidence arrays required by the preserved Phase 1 facets; that `Scene` is a derived view, not a second source of truth. The package repository validates registered fixtures before returning them and the page route is `/investigations/:packageId/scenes/:sceneId`.

Adding a Source alone cannot silently rewrite synthesis. A source must resolve through `Source → Document → Passage → EvidenceLink → Claim/Relationship/KnownAtTime`; a material synthesis block must then reference the supported record. Phase L adds the human impact-review and immutable narrative-revision workflow for source enrichment. The Phase B golden package is a migrated human-curated draft, so AI stage/model/prompt provenance is not fabricated; typed AI record provenance and Python contract parity are Phase C work.
