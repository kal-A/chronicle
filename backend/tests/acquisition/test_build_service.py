"""CorpusBuildService: the bridge from an arbitrary topic to a registered,
investigatable corpus.

The service runs the P1 acquisition pipeline, persists the built
GeneratedInvestigation as a package file, and registers it in the same
CorpusRegistry the four agents already use -- so a freshly acquired topic loads
and searches through the unchanged PackageBackedCorpus path, exactly like a
builtin fixture. These tests use a fake pipeline returning a genuinely built
package (so registration + load + search are exercised for real) without any
network or Ollama.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

from chronicle.acquisition.build_service import CorpusBuildService
from chronicle.acquisition.chunking import chunk_source
from chronicle.acquisition.contracts import AcquiredSource, SourceCandidate
from chronicle.acquisition.corpus_builder import build_corpus
from chronicle.acquisition.pipeline import AcquisitionResult
from chronicle.contracts.enums import RightsStatus, SourceType
from chronicle.corpus import CorpusRegistry
from chronicle.corpus.contracts import PassageSearchRequest


def _acquired(candidate_id: str, title: str, body: str) -> AcquiredSource:
    candidate = SourceCandidate(
        candidateId=candidate_id,
        connector="wikipedia",
        title=title,
        sourceType=SourceType.TERTIARY_REFERENCE,
        fullTextAvailable=True,
        rightsStatus=RightsStatus.LICENSED,
        url=f"https://example.org/{candidate_id}",
        language="en",
    )
    return AcquiredSource(
        candidate=candidate,
        text=body,
        contentType="text/plain",
        contentSha256=f"hash-{candidate_id}",
        charCount=len(body),
        retrievedAt=datetime(2026, 9, 9, tzinfo=timezone.utc),
    )


def _built_result() -> AcquisitionResult:
    src = _acquired(
        "wikipedia:en:1",
        "Alpha Overview",
        "Alpha describes the zeppelin registry in detail. " * 20,
    )
    passages = chunk_source(src)
    investigation = build_corpus(
        topic="a placeholder subject",
        interpreted_question="What happened in the placeholder subject?",
        geographic_scope=["Somewhere"],
        date_earliest=date(1800, 1, 1),
        date_latest=date(1850, 12, 31),
        acquired=[src],
        passages=passages,
    )
    return AcquisitionResult(
        investigation=investigation,
        discovered=1,
        acquired=1,
        passages=len(passages),
    )


@dataclass
class _FakePipeline:
    """Records the run() kwargs and returns a pre-built result."""

    result: AcquisitionResult
    calls: list[dict] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.calls = []

    def run(self, **kwargs) -> AcquisitionResult:
        self.calls.append(kwargs)
        return self.result


def _service(tmp_path, registry, pipeline) -> CorpusBuildService:
    return CorpusBuildService(
        pipeline=pipeline,
        registry=registry,
        build_dir=tmp_path / "built",
    )


def test_build_registers_a_corpus_that_loads_and_searches(tmp_path):
    registry = CorpusRegistry()
    result = _built_result()
    pipeline = _FakePipeline(result)
    service = _service(tmp_path, registry, pipeline)

    outcome = service.build(
        topic="a placeholder subject",
        interpreted_question="What happened in the placeholder subject?",
        geographic_scope=["Somewhere"],
        date_earliest=date(1800, 1, 1),
        date_latest=date(1850, 12, 31),
    )

    # the pipeline was driven with the caller's scope
    assert pipeline.calls[0]["topic"] == "a placeholder subject"
    assert pipeline.calls[0]["geographic_scope"] == ["Somewhere"]

    # the built corpus is registered under the deterministic package id
    assert outcome.corpusId == result.investigation.packageId
    assert outcome.corpusId in registry.list_corpus_ids()
    assert outcome.alreadyRegistered is False
    assert outcome.acquisition.acquired == 1

    # and is loadable + searchable through the unchanged PackageBackedCorpus path
    corpus = registry.get_corpus(outcome.corpusId)
    hits = corpus.search_passages(
        PassageSearchRequest(corpusId=outcome.corpusId, query="zeppelin")
    )
    assert hits.totalMatched >= 1


def test_rebuilding_same_topic_is_idempotent(tmp_path):
    registry = CorpusRegistry()
    result = _built_result()
    service = _service(tmp_path, registry, _FakePipeline(result))
    scope = dict(
        topic="a placeholder subject",
        interpreted_question="What happened in the placeholder subject?",
        geographic_scope=["Somewhere"],
        date_earliest=date(1800, 1, 1),
        date_latest=date(1850, 12, 31),
    )

    first = service.build(**scope)
    second = service.build(**scope)

    assert first.corpusId == second.corpusId
    assert first.alreadyRegistered is False
    assert second.alreadyRegistered is True
    assert registry.list_corpus_ids().count(first.corpusId) == 1


class _FakeEmbedder:
    """Deterministic tiny embedder; enough to exercise indexing + reranking."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_one(text) for text in texts]

    def embed_one(self, text: str) -> list[float]:
        return [float(len(text) % 7 + 1), 1.0, 0.0]


def test_build_with_embedder_registers_a_hybrid_corpus(tmp_path):
    from chronicle.acquisition.hybrid_corpus import HybridCorpus

    registry = CorpusRegistry()
    result = _built_result()
    service = CorpusBuildService(
        pipeline=_FakePipeline(result),
        registry=registry,
        build_dir=tmp_path / "built",
        embedder=_FakeEmbedder(),
    )

    outcome = service.build(
        topic="a placeholder subject",
        interpreted_question="What happened?",
        geographic_scope=["Somewhere"],
        date_earliest=date(1800, 1, 1),
        date_latest=date(1850, 12, 31),
    )

    assert outcome.semantic is True
    corpus = registry.get_corpus(outcome.corpusId)
    assert isinstance(corpus, HybridCorpus)
    # search still works through the hybrid wrapper
    hits = corpus.search_passages(
        PassageSearchRequest(corpusId=outcome.corpusId, query="zeppelin")
    )
    assert hits.totalMatched >= 1


def test_build_without_embedder_registers_plain_corpus(tmp_path):
    from chronicle.acquisition.hybrid_corpus import HybridCorpus

    registry = CorpusRegistry()
    service = _service(tmp_path, registry, _FakePipeline(_built_result()))

    outcome = service.build(
        topic="a placeholder subject",
        interpreted_question="What happened?",
        geographic_scope=["Somewhere"],
        date_earliest=date(1800, 1, 1),
        date_latest=date(1850, 12, 31),
    )

    assert outcome.semantic is False
    assert not isinstance(registry.get_corpus(outcome.corpusId), HybridCorpus)


def test_build_writes_a_loadable_package_file(tmp_path):
    registry = CorpusRegistry()
    result = _built_result()
    service = _service(tmp_path, registry, _FakePipeline(result))

    outcome = service.build(
        topic="a placeholder subject",
        interpreted_question="What happened?",
        geographic_scope=["Somewhere"],
        date_earliest=date(1800, 1, 1),
        date_latest=date(1850, 12, 31),
    )

    assert outcome.packagePath.exists()
    assert outcome.packagePath.suffix == ".json"
