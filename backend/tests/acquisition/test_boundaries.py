"""Unit tests for the deterministic boundary resolver (ADR-004 addendum, T3).

Run against a tiny committed fixture (two snapshots, a few fake polities), never
the ~69 MB fetched dataset, so the suite is fully offline.
"""

from pathlib import Path

from chronicle.acquisition.boundaries import BoundaryResolver

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "boundaries"


def _resolver() -> BoundaryResolver:
    return BoundaryResolver(FIXTURE_DIR)


def test_available_years_parsed_from_filenames():
    assert _resolver().available_years() == [-300, -200]


def test_picks_nearest_naming_snapshot_either_direction():
    resolver = _resolver()
    # -218 is 18 yrs from bc200 and 82 from bc300 -> bc200
    near_later = resolver.resolve("Alpha", -218)
    assert near_later is not None and near_later.attested_year == -200
    # -260 is 40 yrs from bc300 and 60 from bc200 -> bc300
    near_earlier = resolver.resolve("Alpha", -260)
    assert near_earlier is not None and near_earlier.attested_year == -300
    # equidistant (-250): tie-break prefers the earlier (at-or-before) snapshot
    tie = resolver.resolve("Alpha", -250)
    assert tie is not None and tie.attested_year == -300
    # the two snapshots carry different Alpha polygons — it picks the right one
    assert near_later.coordinates != near_earlier.coordinates


def test_matching_is_case_and_punctuation_insensitive():
    assert _resolver().resolve("  alpha ", -150) is not None


def test_no_name_match_returns_none():
    assert _resolver().resolve("Zeta", -150) is None


def test_searches_outward_when_the_nearest_snapshot_lacks_the_polity():
    resolver = _resolver()
    # Gamma exists only in bc200; from -250 the nearest snapshot (bc300) lacks it,
    # so the resolver searches outward, finds it in bc200, and discloses that year.
    resolved = resolver.resolve("Gamma", -250)
    assert resolved is not None and resolved.attested_year == -200


def test_max_distance_caps_anachronistic_matches():
    resolver = _resolver()
    # Without a cap, -500 takes the nearest naming snapshot (bc300, 200 yrs off).
    assert resolver.resolve("Alpha", -500) is not None
    # With a tight cap, nothing is within range -> None (never a fabricated frontier).
    assert resolver.resolve("Alpha", -500, max_distance_years=100) is None


def test_non_area_geometry_is_ignored():
    assert _resolver().resolve("Point Place", -150) is None


def test_resolved_boundary_carries_provenance():
    resolved = _resolver().resolve("Gamma", -150)
    assert resolved is not None
    assert resolved.source_dataset == "historical-basemaps"
    assert resolved.license == "GPL-3.0"
    assert resolved.matched_name == "Gamma"
    assert resolved.geometry_type == "MultiPolygon"


def test_missing_directory_yields_no_years_and_no_match(tmp_path):
    resolver = BoundaryResolver(tmp_path / "does-not-exist")
    assert resolver.available_years() == []
    assert resolver.resolve("Alpha", -150) is None
