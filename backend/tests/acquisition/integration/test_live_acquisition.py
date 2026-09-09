"""Live acquisition smoke tests against real free APIs.

Marked ``live_network_integration`` and excluded from the default run. Invoke with:

    pytest -m live_network_integration -s

Each test skips itself (rather than failing) when the network is unreachable, so it
is safe to run offline. Run with ``-s`` to see the printed acquisition summary.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import httpx
import pytest

from chronicle.acquisition.connectors.base import ConnectorError
from chronicle.acquisition.connectors.curated_resource import CuratedResourceConnector
from chronicle.acquisition.connectors.doc_registry_seed import DocRegistrySeedConnector
from chronicle.acquisition.connectors.gutenberg import GutenbergConnector
from chronicle.acquisition.connectors.internet_archive import InternetArchiveConnector
from chronicle.acquisition.connectors.wikipedia import WikipediaConnector
from chronicle.acquisition.contracts import DiscoveryQuery
from chronicle.acquisition.fetch_cache import FetchCache
from chronicle.acquisition.pipeline import AcquisitionPipeline
from chronicle.corpus.contracts import PassageSearchRequest
from chronicle.corpus.package_corpus import PackageBackedCorpus

pytestmark = pytest.mark.live_network_integration

REPO_ROOT = Path(__file__).resolve().parents[4]
_TOPIC = "Congress of Vienna"


def _skip_if_offline(exc: Exception) -> None:
    if isinstance(exc, (httpx.TransportError,)) or isinstance(exc, ConnectorError):
        pytest.skip(f"network unavailable or source unreachable: {exc}")
    raise exc


def test_wikipedia_live_discover_and_fetch():
    connector = WikipediaConnector()
    try:
        candidates = connector.discover(DiscoveryQuery(topic=_TOPIC, maxResults=3))
        assert candidates, "expected at least one Wikipedia candidate"
        acquired = connector.fetch(candidates[0])
    except Exception as exc:  # noqa: BLE001 - integration guard
        _skip_if_offline(exc)
        return
    assert acquired is not None
    assert len(acquired.text) > 200
    print(f"\n[wikipedia] {candidates[0].title!r}: {acquired.charCount} chars")


def test_pipeline_builds_a_real_corpus_live(tmp_path):
    connectors = [
        WikipediaConnector(),
        GutenbergConnector(),
        InternetArchiveConnector(),
        DocRegistrySeedConnector(REPO_ROOT),
        CuratedResourceConnector(),
    ]
    pipeline = AcquisitionPipeline(connectors, FetchCache(tmp_path / "cache"), per_connector_results=3)

    try:
        result = pipeline.run(
            topic=_TOPIC,
            interpreted_question="What was decided at the Congress of Vienna?",
            geographic_scope=["Europe"],
            date_earliest=date(1814, 9, 1),
            date_latest=date(1815, 6, 30),
            max_sources=6,
        )
    except Exception as exc:  # noqa: BLE001 - integration guard
        _skip_if_offline(exc)
        return

    print(f"\n[pipeline] topic={_TOPIC!r}")
    print(f"  discovered={result.discovered} acquired={result.acquired} passages={result.passages}")
    for source in result.investigation.sources:
        print(f"    - [{source.sourceType.value}] {source.title[:70]}")
    if result.discovery_errors:
        print(f"  discovery_errors={result.discovery_errors}")

    assert result.acquired >= 1, "expected to acquire at least one source"
    assert result.passages >= 1
    assert len(result.investigation.passages) == result.passages

    # round-trip through the real corpus the agents use
    package_path = tmp_path / "corpus.json"
    package_path.write_text(json.dumps(result.investigation.model_dump(mode="json")), encoding="utf-8")
    corpus = PackageBackedCorpus.load(
        corpus_id="live-smoke",
        package_path=package_path,
        title="Live smoke corpus",
        benchmark_role="live acquisition smoke test",
    )
    hits = corpus.search_passages(PassageSearchRequest(corpusId="live-smoke", query="congress"))
    print(f"  search 'congress' -> {hits.totalMatched} matched")
    assert hits.returnedCount >= 0  # search runs without error over the built corpus
