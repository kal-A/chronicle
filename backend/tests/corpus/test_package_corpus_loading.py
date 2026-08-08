"""PackageBackedCorpus.load(): valid packages load and index correctly,
invalid packages are rejected loudly (never silently indexed), and every
get_* getter enforces corpus-scoped existence."""

from __future__ import annotations

import pytest

from chronicle.contracts import SUPPORTED_GENERATED_INVESTIGATION_VERSION
from chronicle.corpus.errors import InvalidPackageError, UnknownRecordError
from chronicle.corpus.package_corpus import PackageBackedCorpus

from .conftest import INVALID_FIXTURES_DIR, load_json

EXPECTED_CAPABILITIES = {
    "blank-cheque-golden": {
        "passages",
        "claims",
        "relationships",
        "timeline",
        "map_context",
        "knowledge_states",
        "source_comparison",
    },
    "concert-of-europe-1814-1822": {
        "passages",
        "claims",
        "relationships",
        "timeline",
        "map_context",
        "source_comparison",
        # deliberately excludes "knowledge_states" -- this corpus has zero
        # KnownAtTime records, and the manifest must say so honestly.
    },
}


def test_valid_package_loads_and_validates(corpus):
    investigation = corpus.get_investigation()
    assert investigation.schemaVersion == SUPPORTED_GENERATED_INVESTIGATION_VERSION


def test_manifest_capabilities_reflect_actual_content(corpus, corpus_id):
    manifest = corpus.get_manifest()
    assert manifest.supportedCapabilities == EXPECTED_CAPABILITIES[corpus_id]


def test_concert_of_europe_has_no_knowledge_state_capability():
    corpus = PackageBackedCorpus.load(
        corpus_id="x",
        package_path=_concert_path(),
        title="t",
        benchmark_role="r",
    )
    assert "knowledge_states" not in corpus.get_manifest().supportedCapabilities
    assert corpus.get_investigation().knowledgeStates == []


def _concert_path():
    from .conftest import REPO_ROOT

    return REPO_ROOT / "fixtures" / "concert-of-europe.generated-investigation.json"


def test_invalid_package_is_rejected():
    with pytest.raises(InvalidPackageError):
        PackageBackedCorpus.load(
            corpus_id="broken",
            package_path=INVALID_FIXTURES_DIR / "unsupported-version.json",
            title="Broken",
            benchmark_role="test",
        )


def test_missing_file_raises_invalid_package_error(tmp_path):
    with pytest.raises(InvalidPackageError):
        PackageBackedCorpus.load(
            corpus_id="missing",
            package_path=tmp_path / "does-not-exist.json",
            title="Missing",
            benchmark_role="test",
        )


def test_malformed_json_raises_invalid_package_error(tmp_path):
    bad_file = tmp_path / "not-json.json"
    bad_file.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(InvalidPackageError):
        PackageBackedCorpus.load(
            corpus_id="malformed",
            package_path=bad_file,
            title="Malformed",
            benchmark_role="test",
        )


@pytest.mark.parametrize(
    "getter_name,bad_id",
    [
        ("get_source", "no-such-source"),
        ("get_document", "no-such-document"),
        ("get_passage", "no-such-passage"),
        ("get_claim", "no-such-claim"),
        ("get_relationship", "no-such-relationship"),
        ("get_event", "no-such-event"),
        ("get_entity", "no-such-entity"),
        ("get_place", "no-such-place"),
        ("get_knowledge_state", "no-such-knowledge-state"),
    ],
)
def test_unknown_id_raises_for_every_getter(corpus, getter_name, bad_id):
    getter = getattr(corpus, getter_name)
    with pytest.raises(UnknownRecordError):
        getter(bad_id)


def test_get_place_rejects_a_person_typed_entity(corpus):
    investigation = corpus.get_investigation()
    person = next(e for e in investigation.entities if e.entityType == "person")
    with pytest.raises(UnknownRecordError):
        corpus.get_place(person.id)


def test_get_entity_accepts_both_person_and_place(corpus):
    investigation = corpus.get_investigation()
    for entity in investigation.entities:
        assert corpus.get_entity(entity.id).id == entity.id


def test_returned_records_are_defensive_copies(corpus):
    source = corpus.get_source(corpus.get_investigation().sources[0].id)
    original_title = source.title
    source.title = "mutated by caller"
    assert corpus.get_source(source.id).title == original_title


def test_returned_investigation_is_a_defensive_copy(corpus):
    investigation = corpus.get_investigation()
    original_title = investigation.sources[0].title
    investigation.sources[0].title = "mutated by caller"
    assert corpus.get_investigation().sources[0].title == original_title


def test_index_escape_hatch_is_a_defensive_copy(corpus):
    exposed = corpus.index
    source_id = next(iter(exposed.sources_by_id))
    original_title = exposed.sources_by_id[source_id].title
    exposed.sources_by_id[source_id].title = "mutated by caller"
    assert corpus.index.sources_by_id[source_id].title == original_title


def test_cached_index_has_no_directly_mutable_attribute(corpus):
    with pytest.raises(AttributeError):
        _ = corpus._index


@pytest.mark.parametrize(
    "attribute",
    ["_corpus_id", "_manifest", "_investigation", "_index"],
)
def test_cached_corpus_state_has_no_public_by_convention_attribute(corpus, attribute):
    with pytest.raises(AttributeError):
        getattr(corpus, attribute)


def test_shadow_attributes_cannot_relabel_or_mutate_cached_corpus(corpus):
    original_corpus_id = corpus.corpus_id
    original_manifest = corpus.get_manifest()
    source_id = corpus.get_investigation().sources[0].id
    original_title = corpus.get_source(source_id).title

    corpus._corpus_id = "forged-corpus"
    corpus._manifest = original_manifest.model_copy(update={"corpusId": "forged-corpus"})
    forged_investigation = corpus.get_investigation()
    forged_investigation.sources[0].title = "MUTATED"
    corpus._investigation = forged_investigation

    assert corpus.corpus_id == original_corpus_id
    assert corpus.get_manifest().corpusId == original_corpus_id
    assert corpus.get_source(source_id).title == original_title


def test_expected_package_identity_mismatch_is_rejected(tmp_path):
    with pytest.raises(InvalidPackageError, match="packageId"):
        PackageBackedCorpus.load(
            corpus_id="registered-corpus",
            package_path=_concert_path(),
            title="t",
            benchmark_role="r",
            expected_package_id="a-different-package",
        )


@pytest.mark.parametrize(
    "expected, value, message",
    [
        ("expected_package_hash", "0" * 64, "hash"),
        ("expected_schema_version", "999.0.0", "schemaVersion"),
        ("expected_package_revision", 999, "packageRevision"),
    ],
)
def test_each_pinned_package_identity_field_is_verified(expected, value, message):
    kwargs = {expected: value}
    with pytest.raises(InvalidPackageError, match=message):
        PackageBackedCorpus.load(
            corpus_id="registered-corpus",
            package_path=_concert_path(),
            title="t",
            benchmark_role="r",
            **kwargs,
        )
