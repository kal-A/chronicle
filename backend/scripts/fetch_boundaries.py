"""Fetch the historical-basemaps world boundary snapshots for the geometry
resolver (ADR-004 addendum, Slice T3).

Source: https://github.com/aourednik/historical-basemaps  (GPL-3.0)
These `world_<year>.geojson` files are a **backend resolver input**, not shipped
to the browser — the resolver reads them during acquisition and bakes only each
investigation's resolved polygons into its TerritoryGeometry records. They are
large (~81 MB total) and therefore gitignored; run this once to populate them:

    python backend/scripts/fetch_boundaries.py

Uses only the standard library (no new dependencies). Idempotent: existing files
are skipped unless --force is passed.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

CONTENTS_API = "https://api.github.com/repos/aourednik/historical-basemaps/contents/geojson"
DEST = Path(__file__).resolve().parents[1] / "data" / "boundaries"
_UA = {"User-Agent": "ChronicleResearchBot/0.1 (+https://github.com/; historical boundary fetch)"}


def _get(url: str) -> bytes:
    request = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 (trusted hosts)
        return response.read()


def _listing() -> list[dict]:
    entries = json.loads(_get(CONTENTS_API))
    return [
        entry
        for entry in entries
        if entry.get("type") == "file" and entry["name"].startswith("world_") and entry["name"].endswith(".geojson")
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="re-download files that already exist")
    args = parser.parse_args()

    DEST.mkdir(parents=True, exist_ok=True)
    files = _listing()
    print(f"historical-basemaps: {len(files)} world_*.geojson snapshots -> {DEST}")

    downloaded = skipped = 0
    for entry in files:
        target = DEST / entry["name"]
        if target.exists() and not args.force:
            skipped += 1
            continue
        target.write_bytes(_get(entry["download_url"]))
        downloaded += 1
        print(f"  {entry['name']}  ({entry['size'] / 1024:.0f} KB)")

    print(f"done: {downloaded} downloaded, {skipped} already present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
