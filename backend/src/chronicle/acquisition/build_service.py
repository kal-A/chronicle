"""Bridge an arbitrary topic to a registered, investigatable corpus.

``CorpusBuildService`` is the seam between the P1 acquisition pipeline and the
runtime the four agents already run on. It runs the pipeline, persists the built
:class:`GeneratedInvestigation` as a package file, and registers a
:class:`CorpusSource` in the :class:`CorpusRegistry`. The built package is then
loaded and searched through the *unchanged* ``PackageBackedCorpus`` path -- same
validation, same indexing, same tools -- so an auto-acquired topic is
investigatable exactly like a curated fixture. There is no in-memory shortcut
and no parallel corpus type: the built package goes through the same file-load +
schema-validation gate as every builtin corpus, which keeps the historical
integrity guarantees intact.

The package id is deterministic in topic + acquired content (see
``deterministic_package_id``), so rebuilding the same topic is idempotent: the
service detects the already-registered corpus and reuses it rather than
duplicating work or raising.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Protocol

from ..contracts.enums import RequestedDepth, RequestType
from ..corpus.manifest import CorpusRegistry, CorpusSource
from .pipeline import AcquisitionResult


class SupportsAcquisitionRun(Protocol):
    """The slice of ``AcquisitionPipeline`` the service depends on."""

    def run(
        self,
        *,
        topic: str,
        interpreted_question: str,
        geographic_scope: list[str],
        date_earliest: date,
        date_latest: date,
        **kwargs: object,
    ) -> AcquisitionResult: ...


@dataclass(frozen=True)
class CorpusBuildResult:
    corpusId: str
    packagePath: Path
    acquisition: AcquisitionResult
    #: True when the deterministic corpus already existed and was reused.
    alreadyRegistered: bool


class CorpusBuildService:
    """Run acquisition for a topic, persist the package, and register it."""

    def __init__(
        self,
        *,
        pipeline: SupportsAcquisitionRun,
        registry: CorpusRegistry,
        build_dir: Path | str,
    ) -> None:
        self._pipeline = pipeline
        self._registry = registry
        self._build_dir = Path(build_dir)

    def build(
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
    ) -> CorpusBuildResult:
        result = self._pipeline.run(
            topic=topic,
            interpreted_question=interpreted_question,
            geographic_scope=geographic_scope,
            date_earliest=date_earliest,
            date_latest=date_latest,
            terms=terms,
            languages=languages,
            max_sources=max_sources,
            date_label=date_label,
            request_type=request_type,
            requested_depth=requested_depth,
            generated_at=generated_at,
        )
        investigation = result.investigation
        corpus_id = investigation.packageId
        package_path = self._build_dir / f"{corpus_id}.json"

        if corpus_id in self._registry.list_corpus_ids():
            # Deterministic id: the same topic + content was already built and
            # registered. Reuse it rather than rewrite or raise.
            return CorpusBuildResult(
                corpusId=corpus_id,
                packagePath=package_path,
                acquisition=result,
                alreadyRegistered=True,
            )

        self._build_dir.mkdir(parents=True, exist_ok=True)
        package_path.write_text(
            json.dumps(investigation.model_dump(mode="json")),
            encoding="utf-8",
        )
        self._registry.register(
            CorpusSource(
                corpus_id=corpus_id,
                package_path=package_path,
                title=_title_for(topic),
                benchmark_role=(
                    "Auto-acquired draft corpus built from free/local sources for an "
                    "arbitrary topic; PARTIAL/unreviewed scaffolding, no fabricated history."
                ),
                # Verify the id on load; hash/revision are freshly computed, not
                # asserted, since this package was just built this run.
                expected_package_id=corpus_id,
            )
        )
        return CorpusBuildResult(
            corpusId=corpus_id,
            packagePath=package_path,
            acquisition=result,
            alreadyRegistered=False,
        )


def _title_for(topic: str) -> str:
    cleaned = " ".join(topic.split()).strip()
    return cleaned[:200] if cleaned else "Untitled acquired corpus"


__all__ = ["CorpusBuildResult", "CorpusBuildService", "SupportsAcquisitionRun"]
