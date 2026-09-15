"""Deterministic historical-boundary geometry resolver (ADR-004 addendum, T3).

Maps a polity name + a target year to a boundary polygon taken from a SOURCED
dataset (historical-basemaps ``world_<year>.geojson`` snapshots) — never drawn by
the LLM. It steps to the nearest attested snapshot at or before the target year
and records that year, so rendering can honestly say "as of ~Y". No name match
=> no geometry: the caller omits the territory rather than fabricating a frontier.

Subject-agnostic: matching is generic string normalisation over the dataset's
``NAME`` field. No event or polity names appear in this module — the polity to
resolve is always supplied by the caller (ultimately the extractor's grounded
ControlState), never branched on here.

The dataset is a backend resolver input, not shipped to the browser; populate it
with ``python backend/scripts/fetch_boundaries.py`` (see
docs/research/historical-boundaries-source.md).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

# backend/data/boundaries — this file is backend/src/chronicle/acquisition/boundaries.py
_DEFAULT_DIR = Path(__file__).resolve().parents[3] / "data" / "boundaries"
_SOURCE_DATASET = "historical-basemaps"
_LICENSE = "GPL-3.0"

# Era guard for the pipeline: a naming snapshot farther than this from the claim
# year is too anachronistic to stand in, so the caller omits the territory rather
# than draw a wildly-wrong-era shape. Sized against the dataset: in the historical
# era (~1000 BC onward) adjacent snapshots are at most ~300 years apart, so 400
# admits every legitimate nearest-snapshot reach (e.g. Numidia 209 BC -> 100 BC,
# ~109y) while rejecting name/era collisions such as ancient "Sicily"/"Sardinia"
# matching a medieval snapshot ~1200-1500 years away. The resolver itself stays
# unbounded by default; this is the pipeline's policy, applied in assembly.
DEFAULT_MAX_DISTANCE_YEARS = 400
_FILENAME = re.compile(r"^world_(bc)?(\d+)\.geojson$", re.IGNORECASE)
_AREA_GEOMETRIES = ("Polygon", "MultiPolygon")


@dataclass(frozen=True)
class ResolvedBoundary:
    """A boundary polygon resolved from the dataset, ready to become a
    TerritoryGeometry. ``attested_year`` is the snapshot the polygon actually came
    from (BC negative), which the map surfaces as "as of ~Y"."""

    geometry_type: str  # "Polygon" | "MultiPolygon"
    coordinates: list
    attested_year: int
    matched_name: str
    source_dataset: str = _SOURCE_DATASET
    license: str = _LICENSE


def _normalise(name: str) -> str:
    """Casefold and strip to alphanumerics so matching ignores spacing, case and
    punctuation without any per-polity special-casing."""
    return re.sub(r"[^a-z0-9]+", "", name.casefold())


def _snapshot_year(filename: str) -> int | None:
    match = _FILENAME.match(filename)
    if not match:
        return None
    year = int(match.group(2))
    return -year if match.group(1) else year


class BoundaryResolver:
    """Reads ``world_<year>.geojson`` snapshots from a directory (defaulting to the
    fetched dataset) and resolves polity name + year to a polygon. Snapshots are
    parsed lazily and cached, so repeat lookups are cheap."""

    def __init__(self, directory: Path | str | None = None) -> None:
        self._dir = Path(directory) if directory is not None else _DEFAULT_DIR
        self._years: list[int] | None = None
        self._index_cache: dict[int, dict[str, list[tuple[str, str, list]]]] = {}

    def available_years(self) -> list[int]:
        if self._years is None:
            years: list[int] = []
            if self._dir.is_dir():
                for path in self._dir.glob("world_*.geojson"):
                    year = _snapshot_year(path.name)
                    if year is not None:
                        years.append(year)
            self._years = sorted(years)
        return self._years

    def _years_by_proximity(self, target_year: int) -> list[int]:
        """Snapshot years ordered nearest-first, tie-broken toward the earlier
        (at-or-before) snapshot. Antiquity's snapshots are sparse and a polity is
        not named in every one, so the resolver searches outward from the target
        rather than only stepping back — and always discloses the year it landed on
        (``attested_year``), so a stale match reads as "as of ~Y", never as exact."""
        return sorted(self.available_years(), key=lambda year: (abs(year - target_year), year > target_year))

    def _filename_for(self, year: int) -> str:
        return f"world_bc{-year}.geojson" if year < 0 else f"world_{year}.geojson"

    def _index(self, year: int) -> dict[str, list[tuple[str, str, list]]]:
        if year not in self._index_cache:
            data = json.loads((self._dir / self._filename_for(year)).read_text(encoding="utf-8"))
            index: dict[str, list[tuple[str, str, list]]] = {}
            for feature in data.get("features", []):
                name = (feature.get("properties") or {}).get("NAME")
                geometry = feature.get("geometry") or {}
                if not name or geometry.get("type") not in _AREA_GEOMETRIES:
                    continue
                index.setdefault(_normalise(name), []).append(
                    (name, geometry["type"], geometry["coordinates"])
                )
            self._index_cache[year] = index
        return self._index_cache[year]

    def resolve(
        self,
        polity: str,
        year: int,
        max_distance_years: int | None = None,
    ) -> ResolvedBoundary | None:
        """Resolve ``polity`` as of ``year`` to a boundary: the nearest snapshot
        (preferring at-or-before on ties) that names the polity. Returns None if no
        snapshot names it, or ``max_distance_years`` is given and even the nearest
        naming snapshot is further than that from ``year`` (too anachronistic to
        stand in). ``max_distance_years=None`` (default) takes the best available
        match at any distance and lets ``attested_year`` disclose the staleness."""
        key = _normalise(polity)
        matches: list[tuple[str, str, list]] | None = None
        snapshot: int | None = None
        for candidate in self._years_by_proximity(year):
            if max_distance_years is not None and abs(candidate - year) > max_distance_years:
                break  # ordered by distance — nothing further can be closer
            found = self._index(candidate).get(key)
            if found:
                snapshot, matches = candidate, found
                break
        if snapshot is None or not matches:
            return None

        matched_name = matches[0][0]
        if len(matches) == 1 and matches[0][1] == "Polygon":
            geometry_type, coordinates = "Polygon", matches[0][2]
        else:
            # Several dataset features (or a MultiPolygon) share the name — collect
            # them into one MultiPolygon so the polity renders as a single territory.
            geometry_type = "MultiPolygon"
            coordinates = []
            for _name, feature_type, feature_coordinates in matches:
                if feature_type == "Polygon":
                    coordinates.append(feature_coordinates)
                else:
                    coordinates.extend(feature_coordinates)

        return ResolvedBoundary(
            geometry_type=geometry_type,
            coordinates=coordinates,
            attested_year=snapshot,
            matched_name=matched_name,
        )
