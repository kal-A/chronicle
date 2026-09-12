"""Default free/local connector set + pipeline assembly.

Single definition of "the connectors Chronicle acquires from by default", shared
by the API composition (``create_default_app``) and the acquisition smoke script
so the two never drift. Every connector here is a free/local source; adding a
paid source would need explicit approval (AGENTS.md 5). Topic-agnostic by
construction -- no event or corpus names appear here.
"""

from __future__ import annotations

from pathlib import Path

from ..ai.models.protocol import ModelProvider
from .connectors.base import SourceConnector
from .connectors.curated_resource import CuratedResourceConnector
from .connectors.doc_registry_seed import DocRegistrySeedConnector
from .connectors.gutenberg import GutenbergConnector
from .connectors.internet_archive import InternetArchiveConnector
from .connectors.wikipedia import WikipediaConnector
from .fetch_cache import FetchCache
from .geocoding import (
    PeriodAwareGeocoder,
    WikidataGeoProvider,
    WorldHistoricalGazetteerProvider,
)
from .pipeline import AcquisitionPipeline


def default_connectors(repo_root: Path) -> list[SourceConnector]:
    """The free/local connectors used unless a caller supplies its own."""

    return [
        WikipediaConnector(),
        GutenbergConnector(),
        InternetArchiveConnector(),
        DocRegistrySeedConnector(repo_root),
        CuratedResourceConnector(),
    ]


def default_geocoder() -> PeriodAwareGeocoder:
    """The free, period-aware geo resolver used for structured enrichment.

    Wikidata leads because it disambiguates common names by sitelink prominence
    and rejects anachronistic foundings -- essential for historicity: the World
    Historical Gazetteer's free index is not prominence-ranked and returned
    London, Ontario first for the 1666 Great Fire of London in live testing. The
    gazetteer follows as a period-aware fallback (and a future source of
    period-accurate names). Both are free; adding a paid source would need
    explicit approval (AGENTS.md 5)."""

    return PeriodAwareGeocoder(
        [WikidataGeoProvider(), WorldHistoricalGazetteerProvider()]
    )


def default_pipeline(
    *,
    repo_root: Path,
    cache_dir: Path,
    per_connector_results: int = 3,
    extractor: ModelProvider | None = None,
    geocoder: PeriodAwareGeocoder | None = None,
) -> AcquisitionPipeline:
    """Assemble the default acquisition pipeline over a content-addressed cache.

    Supply both ``extractor`` and ``geocoder`` to enable structured enrichment
    (stages 7/9/12: located events + a timeline); omit either to build an
    evidence-only corpus, the safe default."""

    return AcquisitionPipeline(
        default_connectors(repo_root),
        FetchCache(cache_dir),
        per_connector_results=per_connector_results,
        extractor=extractor,
        geocoder=geocoder,
    )


__all__ = ["default_connectors", "default_geocoder", "default_pipeline"]
