"""Period-aware geocoder unit tests.

Every request is served by httpx.MockTransport, so this suite makes zero real
network requests. Test data uses neutral placeholder place names -- the geocoder
is subject-agnostic and never branches on which place it is.

The geocoder implements documented pipeline stage 12 (geographic intelligence):
a place name + the investigation's date range resolve to a sourced, period-aware
location record, preferring period-aware historical gazetteers, and NEVER
asserting a modern location as historical when the period does not match.
"""

from __future__ import annotations

from datetime import date

import httpx
import pytest

from chronicle.acquisition.connectors.base import ConnectorError
from chronicle.acquisition.geocoding import (
    GeoResolution,
    PeriodAwareGeocoder,
    WikidataGeoProvider,
    WorldHistoricalGazetteerProvider,
)
from chronicle.contracts.enums import DatePrecision, LocationPrecision
from chronicle.contracts.shared import HistoricalDate


def _period(earliest: str = "1660-01-01", latest: str = "1670-12-31") -> HistoricalDate:
    return HistoricalDate(
        precision=DatePrecision.RANGE,
        earliest=date.fromisoformat(earliest),
        latest=date.fromisoformat(latest),
        label=f"{earliest[:4]}-{latest[:4]}",
    )


# --- World Historical Gazetteer provider ---------------------------------


def _whg(handler) -> WorldHistoricalGazetteerProvider:
    client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="https://whgazetteer.org"
    )
    return WorldHistoricalGazetteerProvider(client=client)


def _whg_feature(lng: float, lat: float, title: str, start: str, end: str) -> dict:
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lng, lat]},
        "properties": {"title": title, "index_id": 777},
        "when": {"timespans": [{"start": {"in": start}, "end": {"in": end}}]},
    }


def test_whg_resolves_a_period_overlapping_place():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "placeholdertown" in request.url.params.get("name", "").lower()
        return httpx.Response(
            200,
            json={
                "type": "FeatureCollection",
                "features": [_whg_feature(-0.12, 51.5, "Placeholdertown", "1500", "1900")],
            },
        )

    resolution = _whg(handler).resolve("Placeholdertown", _period())

    assert isinstance(resolution, GeoResolution)
    assert resolution.coordinates is not None
    assert resolution.coordinates.lat == pytest.approx(51.5)
    assert resolution.coordinates.lng == pytest.approx(-0.12)
    assert resolution.nameAtTime == "Placeholdertown"
    assert resolution.providerName == "world-historical-gazetteer"
    assert "whgazetteer.org" in resolution.provenanceUrl


def test_whg_rejects_a_place_whose_attested_period_does_not_overlap():
    # Historicity guard: a feature attested only 1800-1900 must NOT be returned
    # for a 1660-1670 investigation -- we never assert an anachronistic location.
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "type": "FeatureCollection",
                "features": [_whg_feature(-0.12, 51.5, "Placeholdertown", "1800", "1900")],
            },
        )

    assert _whg(handler).resolve("Placeholdertown", _period()) is None


def test_whg_returns_none_on_no_results():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"type": "FeatureCollection", "features": []})

    assert _whg(handler).resolve("Nowhere", _period()) is None


def test_whg_raises_connector_error_on_transport_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    with pytest.raises(ConnectorError):
        _whg(handler).resolve("Placeholdertown", _period())


# --- Wikidata provider ----------------------------------------------------


def _wikidata(handler) -> WikidataGeoProvider:
    client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="https://query.wikidata.org"
    )
    return WikidataGeoProvider(client=client)


def test_wikidata_resolves_a_point_from_sparql_wkt():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params.get("format") == "json"
        return httpx.Response(
            200,
            json={
                "results": {
                    "bindings": [
                        {
                            "placeLabel": {"value": "Placeholdertown"},
                            "coord": {"value": "Point(-0.12 51.5)"},
                            "place": {"value": "http://www.wikidata.org/entity/Q999"},
                        }
                    ]
                }
            },
        )

    resolution = _wikidata(handler).resolve("Placeholdertown", _period())

    assert resolution is not None
    assert resolution.coordinates.lat == pytest.approx(51.5)
    assert resolution.coordinates.lng == pytest.approx(-0.12)
    assert resolution.providerName == "wikidata"
    assert resolution.provenanceUrl == "http://www.wikidata.org/entity/Q999"


def test_wikidata_returns_none_on_no_bindings():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": {"bindings": []}})

    assert _wikidata(handler).resolve("Nowhere", _period()) is None


def _wikidata_binding(label: str, lng: float, lat: float, sitelinks: str, inception: str | None) -> dict:
    binding = {
        "placeLabel": {"value": label},
        "coord": {"value": f"Point({lng} {lat})"},
        "sitelinks": {"value": sitelinks},
        "place": {"value": f"http://www.wikidata.org/entity/{label}"},
    }
    if inception is not None:
        binding["inception"] = {"value": inception}
    return binding


def test_wikidata_prefers_the_most_prominent_in_period_place():
    # Disambiguation: the famous, period-plausible namesake (more sitelinks,
    # ancient founding) must win over a distant modern namesake -- the live bug
    # that placed the 1666 Great Fire of London in London, Ontario.
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"results": {"bindings": [
                _wikidata_binding("Placeholdertown", -0.1275, 51.507, "356", "0047-01-01T00:00:00Z"),
                _wikidata_binding("Placeholdertown", -81.25, 42.98, "86", "1826-01-01T00:00:00Z"),
            ]}},
        )

    resolution = _wikidata(handler).resolve("Placeholdertown", _period())

    assert resolution is not None
    assert resolution.coordinates.lat == pytest.approx(51.507)  # the prominent one


def test_wikidata_skips_a_candidate_founded_after_the_investigation():
    # Anachronism guard: a place founded in 1826 cannot host a 1660-1670 event,
    # even if it is the only (or most prominent) label match.
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"results": {"bindings": [
                _wikidata_binding("Placeholdertown", -81.25, 42.98, "86", "1826-01-01T00:00:00Z"),
            ]}},
        )

    assert _wikidata(handler).resolve("Placeholdertown", _period()) is None


def test_whg_prefers_an_in_period_feature_over_a_period_agnostic_one():
    # When the index returns an agnostic (no-timespan) namesake first and an
    # actually-in-period attestation second, the in-period one is the stronger
    # historicity match and must win despite order.
    def handler(request: httpx.Request) -> httpx.Response:
        agnostic = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-81.25, 42.98]},
            "properties": {"title": "Placeholdertown", "index_id": 1},
        }
        in_period = _whg_feature(-0.12, 51.5, "Placeholdertown", "1500", "1800")
        return httpx.Response(
            200, json={"type": "FeatureCollection", "features": [agnostic, in_period]}
        )

    resolution = _whg(handler).resolve("Placeholdertown", _period())

    assert resolution is not None
    assert resolution.coordinates.lat == pytest.approx(51.5)  # the in-period feature


# --- PeriodAwareGeocoder (provider chain) ---------------------------------


class _StubProvider:
    def __init__(self, name: str, result=None, error: Exception | None = None) -> None:
        self.name = name
        self._result = result
        self._error = error
        self.calls = 0

    def resolve(self, place_name: str, period: HistoricalDate):
        self.calls += 1
        if self._error is not None:
            raise self._error
        return self._result


def _resolution(provider: str) -> GeoResolution:
    from chronicle.contracts.shared import Coordinates

    return GeoResolution(
        canonicalName="Placeholdertown",
        nameAtTime="Placeholdertown",
        coordinates=Coordinates(lat=51.5, lng=-0.12),
        precision=LocationPrecision.CITY,
        providerName=provider,
        provenanceUrl=f"https://example/{provider}",
    )


def test_geocoder_prefers_the_first_provider_that_resolves():
    primary = _StubProvider("whg", result=_resolution("whg"))
    secondary = _StubProvider("wikidata", result=_resolution("wikidata"))

    resolution = PeriodAwareGeocoder([primary, secondary]).resolve("Placeholdertown", _period())

    assert resolution.providerName == "whg"
    assert secondary.calls == 0  # short-circuits once resolved


def test_geocoder_falls_back_when_first_provider_returns_none():
    primary = _StubProvider("whg", result=None)
    secondary = _StubProvider("wikidata", result=_resolution("wikidata"))

    resolution = PeriodAwareGeocoder([primary, secondary]).resolve("Placeholdertown", _period())

    assert resolution.providerName == "wikidata"


def test_geocoder_survives_a_provider_error_and_tries_the_next():
    primary = _StubProvider("whg", error=ConnectorError("whg down"))
    secondary = _StubProvider("wikidata", result=_resolution("wikidata"))

    resolution = PeriodAwareGeocoder([primary, secondary]).resolve("Placeholdertown", _period())

    assert resolution.providerName == "wikidata"


def test_geocoder_returns_none_when_nothing_resolves():
    primary = _StubProvider("whg", result=None)
    secondary = _StubProvider("wikidata", result=None)

    assert PeriodAwareGeocoder([primary, secondary]).resolve("Nowhere", _period()) is None
