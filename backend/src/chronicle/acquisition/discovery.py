"""Discovery aggregation: fan a query across connectors, merge, gate, dedupe.

Runs every connector's ``discover``, drops candidates whose full text is not
available (metadata/snippets are never evidence), deduplicates by candidate id,
and preserves a deterministic order (connector order, then each connector's own
result order). A connector that fails is skipped, not fatal — one dead source
must never sink the whole investigation; its error is collected for reporting.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .connectors.base import ConnectorError, SourceConnector
from .contracts import DiscoveryQuery, SourceCandidate


@dataclass
class DiscoveryResult:
    #: ingestable candidates (full text retrievable) — become corpus evidence
    candidates: list[SourceCandidate] = field(default_factory=list)
    #: reputable pointers whose full text is not freely retrievable — surfaced as
    #: references, never ingested as evidence (rights/free-source discipline)
    references: list[SourceCandidate] = field(default_factory=list)
    #: connector name -> error message, for connectors that failed this run
    errors: dict[str, str] = field(default_factory=dict)


def discover_sources(
    connectors: list[SourceConnector],
    query: DiscoveryQuery,
    *,
    max_total: int | None = None,
) -> DiscoveryResult:
    result = DiscoveryResult()
    seen: set[str] = set()
    for connector in connectors:
        try:
            candidates = connector.discover(query)
        except ConnectorError as error:
            result.errors[connector.name] = str(error)
            continue
        for candidate in candidates:
            if candidate.candidateId in seen:
                continue
            seen.add(candidate.candidateId)
            if not candidate.fullTextAvailable:
                # the evidence gate: not ingestable, but kept as a reference pointer
                result.references.append(candidate)
                continue
            result.candidates.append(candidate)
            if max_total is not None and len(result.candidates) >= max_total:
                return result
    return result
