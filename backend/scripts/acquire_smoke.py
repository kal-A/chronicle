"""Watch the acquisition pipeline research a real topic against free sources.

Run from the backend directory with the project venv:

    python scripts/acquire_smoke.py "Congress of Vienna" --earliest 1814 --latest 1815

Hits real Wikipedia / Gutenberg / Internet Archive APIs plus the in-repo doc
registers, builds an evidence corpus, loads it through the real PackageBackedCorpus,
and prints a summary with a sample passage search. This is a demonstration/smoke
tool, not part of the test suite.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from datetime import date
from pathlib import Path

from chronicle.acquisition.connectors.curated_resource import CuratedResourceConnector
from chronicle.acquisition.connectors.doc_registry_seed import DocRegistrySeedConnector
from chronicle.acquisition.connectors.gutenberg import GutenbergConnector
from chronicle.acquisition.connectors.internet_archive import InternetArchiveConnector
from chronicle.acquisition.connectors.wikipedia import WikipediaConnector
from chronicle.acquisition.fetch_cache import FetchCache
from chronicle.acquisition.pipeline import AcquisitionPipeline
from chronicle.corpus.contracts import PassageSearchRequest
from chronicle.corpus.package_corpus import PackageBackedCorpus

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description="Acquisition pipeline smoke run")
    parser.add_argument("topic", nargs="?", default="Congress of Vienna")
    parser.add_argument("--question", default=None)
    parser.add_argument("--scope", default="Europe", help="comma-separated geographic scope")
    parser.add_argument("--earliest", type=int, default=1814)
    parser.add_argument("--latest", type=int, default=1815)
    parser.add_argument("--max-sources", type=int, default=6)
    parser.add_argument("--search", default="congress", help="sample passage query to run")
    args = parser.parse_args()

    connectors = [
        WikipediaConnector(),
        GutenbergConnector(),
        InternetArchiveConnector(),
        DocRegistrySeedConnector(REPO_ROOT),
        CuratedResourceConnector(),
    ]
    cache_dir = Path(tempfile.gettempdir()) / "chronicle-acquire-smoke"
    pipeline = AcquisitionPipeline(connectors, FetchCache(cache_dir), per_connector_results=3)

    print(f"Researching: {args.topic!r}  ({args.earliest}-{args.latest})")
    print(f"Connectors: {[c.name for c in connectors]}")
    print("Discovering + acquiring (live network)...\n")

    result = pipeline.run(
        topic=args.topic,
        interpreted_question=args.question or f"What happened regarding {args.topic}?",
        geographic_scope=[s.strip() for s in args.scope.split(",") if s.strip()],
        date_earliest=date(args.earliest, 1, 1),
        date_latest=date(args.latest, 12, 31),
        max_sources=args.max_sources,
    )

    print(f"discovered={result.discovered}  acquired={result.acquired}  passages={result.passages}")
    print(f"packageId={result.investigation.packageId}  status={result.investigation.status.value}\n")
    print("Acquired sources:")
    for source in result.investigation.sources:
        print(f"  - [{source.sourceType.value}] {source.title[:80]}")
        print(f"      {source.linkOrLocation}")
    if result.reference_resources:
        print("\nReputable references (surfaced, not ingested):")
        for ref in result.reference_resources:
            print(f"  - {ref.title} :: {ref.url}  [{ref.rightsStatus.value}]")
    if result.discovery_errors:
        print(f"\ndiscovery errors: {result.discovery_errors}")

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
        json.dump(result.investigation.model_dump(mode="json"), handle)
        package_path = handle.name
    corpus = PackageBackedCorpus.load(
        corpus_id="smoke",
        package_path=package_path,
        title="Smoke corpus",
        benchmark_role="smoke",
    )
    hits = corpus.search_passages(PassageSearchRequest(corpusId="smoke", query=args.search, maxResults=3))
    print(f"\nSample search {args.search!r}: {hits.totalMatched} matched, showing {hits.returnedCount}")
    for hit in hits.hits:
        print(f"  - {hit.sourceTitle[:60]} :: {hit.excerpt[:120]!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
