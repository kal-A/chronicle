/**
 * The real 8-stage pipeline sequence, hand-mirrored from
 * backend/src/chronicle/workflow/stages.py's StageName/STAGE_ORDER — no
 * cross-language codegen exists in this project. Presentation copy for the
 * generation-progress checklist (map-first-workspace-instructions.md §6.1),
 * not a contract: it must stay in sync with stages.py by inspection, the
 * same way this fixture content stays in sync with other hand-authored
 * presentation data in src/content/investigationFixtures.ts.
 */
export interface GenerationStage {
  id: string
  label: string
}

export const GENERATION_STAGES: GenerationStage[] = [
  { id: 'SCOPE_PROPOSED', label: 'Scope defined' },
  { id: 'DISCOVERY_QUERIES_PREPARED', label: 'Discovery queries prepared' },
  { id: 'SOURCE_CANDIDATES_DISCOVERED', label: 'Source candidates found' },
  { id: 'SOURCES_ASSESSED', label: 'Sources assessed' },
  { id: 'CORPUS_PREPARED', label: 'Corpus prepared' },
  { id: 'HISTORICAL_MODEL_ASSEMBLED', label: 'Events, positions, and timeline assembled' },
  { id: 'INVESTIGATION_COMPOSED', label: 'Map lenses and narrative composed' },
  { id: 'VERIFIED', label: 'Claims and citations checked' },
]
