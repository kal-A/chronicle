"""AcquisitionPipeline: topic + scope -> a built, evidence-backed corpus.

Ties the stages together: discover candidates across connectors, fetch full text
(through the cache), chunk into passages, and build a valid GeneratedInvestigation.
Scope (interpreted question, geography, date range) is supplied by the caller — a
later LLM scope-resolution stage will populate it; the pipeline itself stays
deterministic given its inputs and connectors.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime

from ..ai.models.protocol import ModelProvider
from ..contracts.enums import DatePrecision, RequestedDepth, RequestType
from ..contracts.generated_investigation import GeneratedInvestigation
from ..contracts.shared import HistoricalDate, Passage
from .assembly import Enrichment, assemble_enrichment
from .boundaries import BoundaryResolver
from .chunking import DEFAULT_TARGET_CHARS, chunk_source
from .connectors.base import ConnectorError, SourceConnector
from .contracts import AcquiredSource, DiscoveryQuery, ExtractedPassage
from .corpus_builder import build_corpus
from .discovery import discover_sources
from .fetch_cache import FetchCache
from .geocoding import PeriodAwareGeocoder


@dataclass
class AcquisitionResult:
    investigation: GeneratedInvestigation
    discovered: int
    acquired: int
    passages: int
    #: grounded events extracted and located (0 when enrichment is disabled or
    #: nothing datable/located was found -- the corpus is then evidence-only)
    events: int = 0
    #: extracted places the period-aware geocoder could place with coordinates
    located_places: int = 0
    discovery_errors: dict[str, str] = field(default_factory=dict)
    #: reputable pointers surfaced but not ingested (e.g. licensed/paid resources)
    reference_resources: list[SourceCandidate] = field(default_factory=list)
    #: per-source fetch failures skipped so one flaky source can't fail the build
    fetch_errors: dict[str, str] = field(default_factory=dict)


class AcquisitionPipeline:
    def __init__(
        self,
        connectors: list[SourceConnector],
        cache: FetchCache,
        *,
        target_chars: int = DEFAULT_TARGET_CHARS,
        per_connector_results: int = 5,
        max_passages_per_source: int = 40,
        extractor: ModelProvider | None = None,
        geocoder: PeriodAwareGeocoder | None = None,
        boundary_resolver: BoundaryResolver | None = None,
    ) -> None:
        if not connectors:
            raise ValueError("AcquisitionPipeline requires at least one connector")
        self._connectors = connectors
        self._by_name = {connector.name: connector for connector in connectors}
        self._cache = cache
        self._target_chars = target_chars
        self._per_connector_results = per_connector_results
        self._max_passages_per_source = max_passages_per_source
        # Structured enrichment (stages 7/9/12) is opt-in: supply BOTH an event
        # extractor and a period-aware geocoder to turn passages into located
        # events + a timeline. Absent either, the pipeline builds an
        # evidence-only corpus exactly as before.
        self._extractor = extractor
        self._geocoder = geocoder
        # Optional territory layer (ADR-004): with a boundary resolver, enrichment
        # also extracts grounded control states and resolves each to a sourced
        # polygon. Absent it, geography stays points + events only.
        self._boundary_resolver = boundary_resolver

    def run(
        self,
        *,
        topic: str,
        interpreted_question: str,
        geographic_scope: list[str],
        date_earliest: date,
        date_latest: date,
        terms: list[str] | None = None,
        languages: list[str] | None = None,
        max_sources: int = 8,
        date_label: str | None = None,
        request_type: RequestType = RequestType.EVENT_RECONSTRUCTION,
        requested_depth: RequestedDepth = RequestedDepth.STANDARD,
        generated_at: datetime | None = None,
    ) -> AcquisitionResult:
        query = DiscoveryQuery(
            topic=topic,
            terms=terms or [],
            maxResults=self._per_connector_results,
            languages=languages or ["en"],
            earliestYear=date_earliest.year,
            latestYear=date_latest.year,
        )
        discovery = discover_sources(self._connectors, query, max_total=max_sources)

        acquired: list[AcquiredSource] = []
        passages: list[ExtractedPassage] = []
        fetch_errors: dict[str, str] = {}
        for candidate in discovery.candidates:
            connector = self._by_name.get(candidate.connector)
            if connector is None:
                continue
            try:
                source = self._cache.get_or_fetch(connector, candidate)
            except ConnectorError as exc:
                # A single flaky/forbidden source (e.g. a 403) must not fail the
                # whole acquisition: skip it, record why, and keep going with the
                # sources that do succeed (partial acquisition).
                fetch_errors[candidate.candidateId] = str(exc)[:300]
                continue
            if source is None:
                continue
            acquired.append(source)
            source_passages = chunk_source(source, target_chars=self._target_chars)
            passages.extend(source_passages[: self._max_passages_per_source])

        enrich = self._build_enricher(
            topic=topic,
            date_earliest=date_earliest,
            date_latest=date_latest,
            date_label=date_label,
        )
        investigation = build_corpus(
            topic=topic,
            interpreted_question=interpreted_question,
            geographic_scope=geographic_scope,
            date_earliest=date_earliest,
            date_latest=date_latest,
            acquired=acquired,
            passages=passages,
            date_label=date_label,
            request_type=request_type,
            requested_depth=requested_depth,
            generated_at=generated_at,
            enrich=enrich,
        )
        located_places = sum(
            1
            for entity in investigation.entities
            if entity.entityType == "place" and entity.coordinates is not None
        )
        return AcquisitionResult(
            investigation=investigation,
            discovered=len(discovery.candidates),
            acquired=len(acquired),
            passages=len(passages),
            events=len(investigation.events),
            located_places=located_places,
            discovery_errors=discovery.errors,
            reference_resources=discovery.references,
            fetch_errors=fetch_errors,
        )

    def _build_enricher(
        self,
        *,
        topic: str,
        date_earliest: date,
        date_latest: date,
        date_label: str | None,
    ) -> Callable[[list[Passage]], Enrichment] | None:
        """A closure binding the injected extractor + geocoder over the built
        passages, or None when enrichment is disabled (keeps build_corpus on its
        evidence-only path)."""

        if self._extractor is None or self._geocoder is None:
            return None

        period = HistoricalDate(
            precision=DatePrecision.EXACT if date_earliest == date_latest else DatePrecision.RANGE,
            earliest=date_earliest,
            latest=date_latest,
            label=date_label,
        )
        extractor = self._extractor
        geocoder = self._geocoder
        boundary_resolver = self._boundary_resolver

        def enrich(built_passages: list[Passage]) -> Enrichment:
            return assemble_enrichment(
                built_passages,
                period,
                topic,
                extractor=extractor,
                geocoder=geocoder,
                boundary_resolver=boundary_resolver,
            )

        return enrich
