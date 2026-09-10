"""AcquisitionPipeline: topic + scope -> a built, evidence-backed corpus.

Ties the stages together: discover candidates across connectors, fetch full text
(through the cache), chunk into passages, and build a valid GeneratedInvestigation.
Scope (interpreted question, geography, date range) is supplied by the caller — a
later LLM scope-resolution stage will populate it; the pipeline itself stays
deterministic given its inputs and connectors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from ..contracts.enums import RequestedDepth, RequestType
from ..contracts.generated_investigation import GeneratedInvestigation
from .chunking import DEFAULT_TARGET_CHARS, chunk_source
from .connectors.base import ConnectorError, SourceConnector
from .contracts import AcquiredSource, DiscoveryQuery, ExtractedPassage
from .corpus_builder import build_corpus
from .discovery import discover_sources
from .fetch_cache import FetchCache


@dataclass
class AcquisitionResult:
    investigation: GeneratedInvestigation
    discovered: int
    acquired: int
    passages: int
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
    ) -> None:
        if not connectors:
            raise ValueError("AcquisitionPipeline requires at least one connector")
        self._connectors = connectors
        self._by_name = {connector.name: connector for connector in connectors}
        self._cache = cache
        self._target_chars = target_chars
        self._per_connector_results = per_connector_results
        self._max_passages_per_source = max_passages_per_source

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
        )
        return AcquisitionResult(
            investigation=investigation,
            discovered=len(discovery.candidates),
            acquired=len(acquired),
            passages=len(passages),
            discovery_errors=discovery.errors,
            reference_resources=discovery.references,
            fetch_errors=fetch_errors,
        )
