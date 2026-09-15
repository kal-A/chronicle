# ADR-005: Era-capable HistoricalDate (BC/BCE support)

**Status:** Accepted

**Date:** 2026-09-14

## Context

`HistoricalDate` is the single time type behind every dated record in the contract:
events (`eventTime`), the timeline, source dates, passage sent/received times,
`KnownAtTime.asOfDate`, scope `dateRange`, and — since ADR-004 step 3 — control-state
intervals (`validFrom`/`validTo`).

Its bounds were stored as calendar dates: `datetime.date` on the backend and
`z.iso.date()` (an ISO `YYYY-MM-DD` string) on the frontend. Both representations are
**CE-only**: Python's `date` has `MINYEAR == 1`, and ISO date strings as validated here
cannot express a year before 1 CE. Every ordering, interval-overlap, and `.year`
computation in the system (`timeline.py`, `corpus/indexing.py`, `corpus/search.py`,
`ai/agents/validation.py`, the frontend timeline/lens sorts) relied on comparing those
dates.

This made the whole time system CE-only. BC subjects could not be represented honestly:
the territory prototype's Punic data (`src/devTerritoryDemo.json`, throwaway) faked
218 BC / 201 BC as the padded CE strings `"0218-01-01"` / `"0201-01-01"`, and the
frontend `historicalYear` helper recovered a signed year by **parsing the display
`label`** ("…BC") because no field carried it. ADR-004's flagship example is the Punic
Wars, so BC support is a prerequisite, not a nicety.

## Decision

Give `HistoricalDate` a **signed astronomical year** as its canonical, always-derivable
ordering key, while keeping the existing calendar dates as *optional, CE-only* day/month
precision.

New optional fields on `HistoricalDate` (backend Pydantic and frontend Zod, field-for-field):

- `earliestYear: int | None` — signed **astronomical** year: `1` = 1 CE, `0` = 1 BC,
  `-1` = 2 BC, …, `-43` = 44 BC. The lower bound of the record's time.
- `latestYear: int | None` — signed astronomical upper bound.

Existing fields are unchanged except that the calendar dates become optional:

- `earliest: date | None`, `latest: date | None` — retained for CE day/month precision
  (e.g. `1914-07-05`); **must be omitted for BC**.
- `precision`, `label` — unchanged.

### Invariants (enforced on both sides)

1. **A lower and an upper bound must each be derivable.** For each bound at least one of
   the year field or the calendar date must be present. (Existing CE records supply the
   date; BC records supply the year.)
2. **Agreement when both present.** If `earliest` and `earliestYear` are both set,
   `earliest.year == earliestYear` (same for `latest`). Calendar dates are therefore
   CE-only (`year >= 1`), so an accompanying year field is necessarily positive.
3. **Ordering is total across eras.** The canonical key is the signed year, refined by
   day-of-year when a calendar date is present: `(year, day_of_year)`, with day-of-year
   defaulting to the first day for a lower bound and the last for an upper bound. This is
   exposed as helper accessors (`lower_key`/`upper_key` on the backend; `dateKeys` on the
   frontend) so no consumer re-derives it.
4. `earliest`/`latest` bounds still satisfy earliest ≤ latest, and `exact` still requires
   equal bounds — now checked on the canonical key so it holds for BC too.

### Numbering convention

**Astronomical** (year 0 = 1 BC), matching ISO 8601's own model, is chosen over historical
numbering (no year 0) so the key is a gap-free signed integer and interval arithmetic is
total and simple. Human-facing "44 BC" is a *display* concern, produced from the signed
year by `formatHistoricalDate`; it is never the stored or compared form.

## Consequences

- **BC works end to end.** Extraction/assembly emit signed years (`_event_time(year)`
  sets `earliestYear = latestYear = year`, and sets the calendar dates only for `year >= 1`);
  control-state intervals, events, and the timeline order correctly across the BC/CE
  boundary; the frontend reads `earliestYear`/`latestYear` directly and the
  `historicalYear` **label-parsing hack is removed**.
- **No CE fixture migration.** Every committed fixture is CE and keeps its calendar dates;
  the year key is derived from them. Only BC records (and the throwaway Punic demo) carry
  explicit signed years.
- **Consumers order by the canonical key, not raw dates**, so BC records (which have no
  calendar date) sort correctly. Coarse date-range *filters* (`DateRangeFilter`, still
  `date`-typed and CE-only) compare against the key at day granularity for CE and at year
  granularity for BC records.
- Honesty (AGENTS.md §3/§12) is preserved: precision is unchanged, `label` still carries
  the authored display string, and a BC record no longer masquerades as a CE date.

## Alternatives considered

- **Year-only (drop calendar dates).** Simpler, but curated CE data (July Crisis
  `1914-07-05`, Great Fire `1666-09-02`) genuinely needs day precision for ordering and
  display. Rejected.
- **Mandatory signed-year fields.** Cleaner single source of truth, but forces a rewrite
  of every CE fixture and constructor. The optional-with-fallback form is backward
  compatible for the same end guarantee (a signed year is always derivable). Chosen.
- **Historical numbering (no year 0).** Matches citation habits but leaves a gap at the
  boundary and complicates interval math; display can render it anyway. Rejected.
