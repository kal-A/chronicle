# Source Register Template

Per-investigation tracking format for sources, used during content curation (Phase 0/1 for July Crisis) and later by Studio's ingestion workflow (Phase 6+). One row per source. This is the human-curation precursor to the `Source` entity in `docs/architecture/domain-model.md` — fields map directly.

| Field | Description |
|---|---|
| `id` | Stable short identifier, e.g. `jc-src-014` |
| `title` | Source title/description |
| `source_type` | One of the types in `source-hierarchy.md` |
| `author_or_origin` | Author, or issuing body for official records |
| `date_of_source` | When the source itself was produced (not the event it describes) |
| `date_type` | exact / approximate / range — see `historical-methodology.md` |
| `language` | Original language |
| `rights_status` | public-domain / licensed / needs-permission / unknown |
| `processing_needs` | none / needs-translation / needs-transcription / needs-acquisition |
| `visibility` | public / private-workspace |
| `link_or_location` | Where the full text/scan can be found |
| `covers_events` | Which in-scope decisions/events (from `july-crisis-scope.md`) this source bears on |
| `covers_actors` | Which actors this source gives direct insight into |
| `evidentiary_notes` | What this source directly establishes vs. what it only supports indirectly |
| `known_limitations` | Translation issues, later-hindsight risk (memoirs), partisan origin, etc. |
| `curation_status` | identified / acquired / passages-extracted / curated / reviewed |

## Usage Notes

- A source only becomes eligible to back a `directly supported` relationship once its `evidentiary_notes` field explicitly states what it establishes — this is a manual discipline during Phase 0/1 curation, enforced structurally once Studio's review workflow exists (Phase 6).
- Keep this register in plain markdown/CSV during Phase 0/1; it becomes seed data for the `Source` table in Phase 2 (`docs/architecture/domain-model.md`), so keep field names aligned to avoid a lossy migration.
- One register per investigation, stored alongside that investigation's content once a content directory convention is established in Phase 1.
