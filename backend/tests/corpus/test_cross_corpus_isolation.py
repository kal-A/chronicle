"""Cross-corpus isolation, including deliberately overlapping record IDs.

Record IDs are only unique inside a package. These tests therefore avoid the
invalid assumption that two corpora have globally disjoint IDs and prove that
the lookup key is effectively ``(corpusId, recordId)`` instead.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from chronicle.corpus import CorpusRegistry
from chronicle.corpus.contracts import PassageSearchRequest
from chronicle.corpus.errors import CorpusBoundaryError
from chronicle.corpus.manifest import CorpusSource

REPO_ROOT = Path(__file__).resolve().parents[3]
GOLDEN_FIXTURE = REPO_ROOT / "fixtures" / "blank-cheque.golden-investigation.json"


def _write_synthetic_package(tmp_path: Path, corpus_id: str, sentinel: str) -> Path:
    data = json.loads(GOLDEN_FIXTURE.read_text(encoding="utf-8"))
    data["packageId"] = corpus_id
    data["request"]["rawInput"] = f"Synthetic generalization corpus {sentinel}"
    data["scope"]["interpretedQuestion"] = f"What does {sentinel} demonstrate?"
    data["passages"][0]["excerpt"] = f"{sentinel} appears only in this corpus."
    path = tmp_path / f"{corpus_id}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.fixture
def overlapping_registry(tmp_path: Path) -> CorpusRegistry:
    sources = []
    for corpus_id, sentinel in (
        ("synthetic-alpha", "alphauniqueterm"),
        ("synthetic-beta", "betauniqueterm"),
    ):
        sources.append(
            CorpusSource(
                corpus_id=corpus_id,
                package_path=_write_synthetic_package(tmp_path, corpus_id, sentinel),
                title=f"Synthetic {corpus_id}",
                benchmark_role="Explicit test-only generalization corpus.",
                expected_package_id=corpus_id,
                expected_schema_version="1.0.0",
                expected_package_revision=1,
            )
        )
    return CorpusRegistry(sources)


def test_synthetic_corpora_deliberately_share_all_record_ids(overlapping_registry):
    alpha = overlapping_registry.get_corpus("synthetic-alpha").get_investigation()
    beta = overlapping_registry.get_corpus("synthetic-beta").get_investigation()

    assert {record.id for record in alpha.sources} == {record.id for record in beta.sources}
    assert {record.id for record in alpha.documents} == {record.id for record in beta.documents}
    assert {record.id for record in alpha.passages} == {record.id for record in beta.passages}
    assert {record.id for record in alpha.claims} == {record.id for record in beta.claims}


def test_same_record_id_resolves_to_content_from_the_selected_corpus(overlapping_registry):
    alpha = overlapping_registry.get_corpus("synthetic-alpha")
    beta = overlapping_registry.get_corpus("synthetic-beta")
    shared_id = alpha.get_investigation().passages[0].id

    assert alpha.get_passage(shared_id).excerpt == "alphauniqueterm appears only in this corpus."
    assert beta.get_passage(shared_id).excerpt == "betauniqueterm appears only in this corpus."


@pytest.mark.parametrize(
    ("corpus_id", "own_term", "other_term"),
    [
        ("synthetic-alpha", "alphauniqueterm", "betauniqueterm"),
        ("synthetic-beta", "betauniqueterm", "alphauniqueterm"),
    ],
)
def test_search_isolated_by_corpus_even_when_passage_ids_overlap(
    overlapping_registry, corpus_id, own_term, other_term
):
    corpus = overlapping_registry.get_corpus(corpus_id)
    own = corpus.search_passages(PassageSearchRequest(corpusId=corpus_id, query=own_term))
    other = corpus.search_passages(PassageSearchRequest(corpusId=corpus_id, query=other_term))

    assert own.returnedCount == 1
    assert own.hits[0].excerpt == f"{own_term} appears only in this corpus."
    assert other.returnedCount == 0


def test_search_scoped_to_another_corpus_is_rejected(overlapping_registry):
    alpha = overlapping_registry.get_corpus("synthetic-alpha")

    with pytest.raises(CorpusBoundaryError):
        alpha.search_passages(PassageSearchRequest(corpusId="synthetic-beta", query="term"))


def test_public_reads_are_defensive_copies_within_and_across_corpora(overlapping_registry):
    alpha = overlapping_registry.get_corpus("synthetic-alpha")
    beta = overlapping_registry.get_corpus("synthetic-beta")
    alpha_copy = alpha.get_investigation()
    original_alpha_count = len(alpha_copy.sources)
    original_beta_count = len(beta.get_investigation().sources)

    alpha_copy.sources.append(alpha_copy.sources[0])

    assert len(alpha.get_investigation().sources) == original_alpha_count
    assert len(beta.get_investigation().sources) == original_beta_count
