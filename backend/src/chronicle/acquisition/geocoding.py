"""Period-aware geographic resolution (documented pipeline stage 12).

Resolves a place name, *for the investigation's date range*, to a sourced
location record, preferring period-aware historical gazetteers over modern-only
sources. Historicity is a hard requirement: a 17th-century investigation must be
placed with 17th-century-accurate geography, so a provider that advertises a
place's attested period must not return it when that period does not overlap the
investigation -- we never assert a modern or anachronistic location as historical
(see docs/architecture/geographic-and-map-generation.md, "Rendering cannot exceed
the evidence's precision").

Providers share the injected-``httpx.Client`` pattern of the source connectors so
tests drive them with ``httpx.MockTransport`` and make zero real requests. The
resolver is subject-agnostic: it never branches on which place or topic it is.

Two providers ship now behind a small protocol -- Wikidata (broad coverage,
disambiguated by sitelink prominence + inception) and World Historical Gazetteer
(period-scoped records) -- with Pleiades / GeoNames / OpenHistoricalMap addable
later behind the same interface. The default resolver tries Wikidata first
because the gazetteer's free index is not prominence-ranked and mislocates
common names (see acquisition/defaults.py::default_geocoder). Endpoint shapes are
pinned by the unit tests and confirmed at live integration.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

import httpx

from ..contracts.enums import LocationPrecision
from ..contracts.shared import Coordinates, HistoricalDate
from .connectors.base import (
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_USER_AGENT,
    ConnectorError,
)


@dataclass(frozen=True)
class GeoResolution:
    """A sourced, period-aware location for one place name.

    ``coordinates`` may be None when a provider knows the place but not a point
    precise enough to render -- the caller keeps the place at low precision
    rather than inventing a location."""

    canonicalName: str
    nameAtTime: str
    coordinates: Coordinates | None
    precision: LocationPrecision
    providerName: str
    provenanceUrl: str


class GeoProvider(Protocol):
    """One geographic source behind a uniform period-aware resolve()."""

    name: str

    def resolve(self, place_name: str, period: HistoricalDate) -> GeoResolution | None:
        """Return a resolution, or None if the source cannot place it *in period*.
        Raises ConnectorError only on transport failure, never on "no match"."""
        ...


# Period-fit ranks for a gazetteer feature (lower is a stronger historicity
# match): attested in period beats period-agnostic beats non-overlapping.
_PERIOD_ATTESTED = 0
_PERIOD_AGNOSTIC = 1
_PERIOD_NONOVERLAP = 2


def _period_years(period: HistoricalDate) -> tuple[int, int]:
    return period.lower_key[0], period.upper_key[0]  # signed years, BC-safe (ADR-005)


_YEAR_RE = re.compile(r"-?\d{1,4}")


def _parse_year(value: object) -> int | None:
    if value is None:
        return None
    match = _YEAR_RE.search(str(value))
    return int(match.group()) if match else None


def _overlaps(start: int | None, end: int | None, lo: int, hi: int) -> bool:
    """True when an attested [start, end] timespan overlaps [lo, hi]. A missing
    bound is treated as open (period-agnostic on that side)."""

    start_ok = end is None or end >= lo
    end_ok = start is None or start <= hi
    return start_ok and end_ok


class WorldHistoricalGazetteerProvider:
    """World Historical Gazetteer: historical place names + coords + attested
    timespans. Preferred because its records are period-scoped."""

    name = "world-historical-gazetteer"
    base_url = "https://whgazetteer.org"

    def __init__(
        self,
        client: httpx.Client | None = None,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._client = client or httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={"User-Agent": DEFAULT_USER_AGENT},
            follow_redirects=True,
        )

    def resolve(self, place_name: str, period: HistoricalDate) -> GeoResolution | None:
        try:
            response = self._client.get("/api/index/", params={"name": place_name})
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise ConnectorError(f"world-historical-gazetteer lookup failed: {exc}") from exc
        except ValueError as exc:
            raise ConnectorError(
                f"world-historical-gazetteer returned invalid JSON: {exc}"
            ) from exc

        lo, hi = _period_years(period)
        # Collect locatable candidates, rejecting any whose attested period does
        # not overlap the investigation, and prefer a feature actually attested
        # in period over a period-agnostic one (no timespans) -- the first is the
        # stronger historicity match. Among equals, payload order is preserved.
        best: tuple[int, dict, list] | None = None
        for feature in payload.get("features", []):
            geometry = feature.get("geometry") or {}
            if geometry.get("type") != "Point":
                continue
            coords = geometry.get("coordinates") or []
            if len(coords) < 2:
                continue
            fit = self._period_fit(feature, lo, hi)
            if fit == _PERIOD_NONOVERLAP:
                continue  # historicity guard: attested period must overlap
            if best is None or fit < best[0]:
                best = (fit, feature, coords)
            if fit == _PERIOD_ATTESTED:
                break  # cannot do better than an in-period attestation
        if best is None:
            return None
        _fit, feature, coords = best
        properties = feature.get("properties") or {}
        title = properties.get("title") or place_name
        index_id = properties.get("index_id")
        provenance = (
            f"{self.base_url}/places/{index_id}/portal"
            if index_id is not None
            else f"{self.base_url}/search?name={place_name}"
        )
        lng, lat = float(coords[0]), float(coords[1])
        return GeoResolution(
            canonicalName=title,
            nameAtTime=title,
            coordinates=Coordinates(lat=lat, lng=lng),
            precision=LocationPrecision.CITY,
            providerName=self.name,
            provenanceUrl=provenance,
        )

    @staticmethod
    def _period_fit(feature: dict, lo: int, hi: int) -> int:
        """_PERIOD_ATTESTED if a timespan overlaps the period, _PERIOD_AGNOSTIC
        if the feature has no attested bounds, _PERIOD_NONOVERLAP if it has
        bounds and none overlap."""

        timespans = ((feature.get("when") or {}).get("timespans")) or []
        if not timespans:
            return _PERIOD_AGNOSTIC
        for span in timespans:
            start = _parse_year((span.get("start") or {}).get("in"))
            end = _parse_year((span.get("end") or {}).get("in"))
            if _overlaps(start, end, lo, hi):
                return _PERIOD_ATTESTED
        return _PERIOD_NONOVERLAP


_WKT_POINT_RE = re.compile(r"Point\(\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*\)")


def _sparql_literal(value: str) -> str:
    """Escape a place name for safe inclusion in a SPARQL string literal."""

    return value.replace("\\", "\\\\").replace('"', '\\"')


class WikidataGeoProvider:
    """Wikidata: broad coverage via SPARQL, with coordinate location (P625),
    inception (P571), and sitelink count as a prominence signal.

    Disambiguation is the whole point here. A bare label match for a common name
    (e.g. "London") returns dozens of namesakes in arbitrary order, so a naive
    first-match confidently mislocates -- observed live placing the 1666 Great
    Fire of London in London, Ontario. Two historicity guards fix this:
    (1) results are ordered by **sitelink count** (prominence), so the place the
    world overwhelmingly means wins; (2) a candidate whose **inception postdates
    the investigation** is rejected as anachronistic (a city founded in 1826
    cannot host a 1666 event) -- the same discipline as the gazetteer's
    period-overlap guard. A candidate with no inception is period-agnostic and
    kept. ``nameAtTime`` is the modern canonical label (an honest approximation;
    period-name refinement from a period-aware gazetteer is a later enhancement)."""

    name = "wikidata"
    base_url = "https://query.wikidata.org"

    def __init__(
        self,
        client: httpx.Client | None = None,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._client = client or httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/sparql-results+json"},
            follow_redirects=True,
        )

    def resolve(self, place_name: str, period: HistoricalDate) -> GeoResolution | None:
        literal = _sparql_literal(place_name)
        query = (
            "SELECT ?place ?placeLabel ?coord ?sitelinks ?inception WHERE { "
            f'?place rdfs:label "{literal}"@en . '
            "?place wdt:P625 ?coord . "
            "?place wikibase:sitelinks ?sitelinks . "
            "OPTIONAL { ?place wdt:P571 ?inception . } "
            'SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . } } '
            "ORDER BY DESC(?sitelinks) LIMIT 10"
        )
        try:
            response = self._client.get("/sparql", params={"format": "json", "query": query})
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise ConnectorError(f"wikidata lookup failed: {exc}") from exc
        except ValueError as exc:
            raise ConnectorError(f"wikidata returned invalid JSON: {exc}") from exc

        _lo, hi = _period_years(period)
        # Bindings arrive in descending prominence; take the first that is not
        # anachronistic so the most prominent period-plausible place wins.
        for binding in (payload.get("results") or {}).get("bindings") or []:
            wkt = (binding.get("coord") or {}).get("value")
            match = _WKT_POINT_RE.search(wkt or "")
            if match is None:
                continue
            inception = _parse_year((binding.get("inception") or {}).get("value"))
            if inception is not None and inception > hi:
                continue  # founded after the investigation -> never asserted
            lng, lat = float(match.group(1)), float(match.group(2))
            label = (binding.get("placeLabel") or {}).get("value") or place_name
            provenance = (binding.get("place") or {}).get("value") or self.base_url
            return GeoResolution(
                canonicalName=label,
                nameAtTime=label,
                coordinates=Coordinates(lat=lat, lng=lng),
                precision=LocationPrecision.CITY,
                providerName=self.name,
                provenanceUrl=provenance,
            )
        return None


class PeriodAwareGeocoder:
    """Resolve a place by trying period-aware providers in priority order.

    A provider that raises (transport failure) is skipped so one flaky source
    never blocks the rest -- mirroring the acquisition pipeline's per-source
    resilience. Returns the first resolution, or None when no provider can place
    the name in period (the caller then keeps the place at low precision with no
    coordinates, never a fabricated one)."""

    def __init__(self, providers: list[GeoProvider]) -> None:
        self._providers = providers

    def resolve(self, place_name: str, period: HistoricalDate) -> GeoResolution | None:
        for provider in self._providers:
            try:
                resolution = provider.resolve(place_name, period)
            except ConnectorError:
                continue
            if resolution is not None:
                return resolution
        return None


__all__ = [
    "GeoResolution",
    "GeoProvider",
    "PeriodAwareGeocoder",
    "WikidataGeoProvider",
    "WorldHistoricalGazetteerProvider",
]
