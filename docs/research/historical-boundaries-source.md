# Historical-boundaries dataset — source, licence, and honesty notes

The generated map's **territory** layer (ADR-004 + its addendum) needs period
boundary polygons. Per the honesty rules, geometry is only ever taken from a
**sourced dataset**, never drawn by the LLM. This documents the dataset the
deterministic geometry resolver (Slice T3) reads.

## Source

- **historical-basemaps** — Andrei Ourednik, <https://github.com/aourednik/historical-basemaps>.
- **Licence:** GPL-3.0 (as reported by the repository). Attribution is expected;
  we ship this note and the upstream licence with any distribution.
- **Contents:** 54 `world_<year>.geojson` snapshots (~69 MB), covering
  **8000 BCE → 2010 CE** — antiquity through the modern era — with polity names
  and boundary polygons. Antiquity is sparser (e.g. `bc323`, `bc300`, `bc200`,
  `bc100`), the 19th–20th century denser (`1815`, `1878`, `1914`, `1938`, `1945`, …).

## How it is stored (not shipped to the browser)

This is a **backend resolver input**, not a client asset. The resolver (Slice T3)
reads these files during acquisition and bakes only *each investigation's*
resolved polygons into its `TerritoryGeometry` records; the browser never loads
the dataset. Because it is large it is **gitignored** (`backend/data/boundaries/`)
and fetched on demand:

```
python backend/scripts/fetch_boundaries.py
```

The resolver's unit tests run against a tiny committed fixture, not this download,
so the suite never depends on it.

## Honesty when resolving

- The resolver matches a `ControlState`'s polity name to a dataset polity and takes
  the **nearest snapshot that names it** (preferring at-or-before on ties, searching
  outward when the closest snapshot doesn't name it), recording that year as
  `TerritoryGeometry.attestedYear` so the map can say "as of ~Y". Antiquity's sparse
  snapshots mean a match may be decades stale — shown as such, never presented as
  exact — and an optional distance cap rejects matches too far to stand in.
- **No match ⇒ no geometry.** A `ControlState` with no resolvable polygon stays a
  non-rendered claim rather than a fabricated frontier.
- 1:coarse world polygons are approximate at this scale; they orient, they do not
  survey. OpenHistoricalMap (date-filtered, networked) remains the optional
  higher-fidelity layer deferred by ADR-004.
