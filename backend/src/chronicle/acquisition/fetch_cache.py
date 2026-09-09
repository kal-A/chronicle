"""Content-addressed fetch cache: avoid re-downloading sources across runs.

Keyed by candidate id (stable per source), stored as one JSON file per acquired
source under a local cache directory. A cache hit skips the network entirely, so
re-running an investigation over the same topic is fast and reproducible. Only
successful acquisitions are cached; a ``None`` fetch (full text unavailable) is not
cached, so a transient miss can be retried next run.

Local filesystem only — no external service, honouring the no-paid-infra rule.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from .connectors.base import SourceConnector
from .contracts import AcquiredSource, SourceCandidate


class FetchCache:
    def __init__(self, cache_dir: str | Path) -> None:
        self._dir = Path(cache_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, candidate_id: str) -> Path:
        key = hashlib.sha256(candidate_id.encode("utf-8")).hexdigest()
        return self._dir / f"{key}.json"

    def get(self, candidate_id: str) -> AcquiredSource | None:
        path = self._path_for(candidate_id)
        if not path.exists():
            return None
        try:
            return AcquiredSource.model_validate_json(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return None  # corrupt cache entry -> treat as a miss

    def put(self, source: AcquiredSource) -> None:
        path = self._path_for(source.candidate.candidateId)
        path.write_text(source.model_dump_json(), encoding="utf-8")

    def get_or_fetch(
        self, connector: SourceConnector, candidate: SourceCandidate
    ) -> AcquiredSource | None:
        cached = self.get(candidate.candidateId)
        if cached is not None:
            return cached
        acquired = connector.fetch(candidate)
        if acquired is not None:
            self.put(acquired)
        return acquired
