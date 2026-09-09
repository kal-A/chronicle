"""Corpus registry (Phase E2): a plain data list of registered corpora,
mirroring providers/registry.py's PROVIDER_SETS flat-dict-of-data
precedent -- no per-corpus branching logic, only data.

Corpus manifests point at repo-root fixtures/*.json by relative path --
a new pattern for backend/src/chronicle/ (only backend/tests/ currently
reaches up to repo-root fixtures/), accepted here rather than duplicating
the JSON source of truth into backend/, per the approved E2 plan's
decision 5. This means chronicle.corpus cannot be run outside this exact
monorepo checkout without fixtures/ present at a fixed relative offset --
acceptable for now, since E2 has no packaging/deployment story, but worth
knowing if that ever changes.

Importing this module does no file I/O -- CorpusRegistry.load()/
get_corpus() do, explicitly, on first use per corpus_id. Never load a
corpus as a side effect of import.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .contracts import CorpusManifest
from .errors import DuplicateCorpusIdError, UnknownCorpusError
from .package_corpus import PackageBackedCorpus

REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURES_DIR = REPO_ROOT / "fixtures"


@dataclass(frozen=True)
class CorpusSource:
    """Static registration data for one corpus -- everything knowable
    without reading the package file. Compare CorpusManifest, which adds
    fields only knowable once the package is actually loaded (hash,
    schema version, capabilities, omissions)."""

    corpus_id: str
    package_path: Path
    title: str
    benchmark_role: str
    expected_package_id: str | None = None
    expected_package_hash: str | None = None
    expected_schema_version: str | None = None
    expected_package_revision: int | None = None


BUILTIN_CORPUS_SOURCES: list[CorpusSource] = [
    CorpusSource(
        corpus_id="blank-cheque-golden",
        package_path=FIXTURES_DIR / "blank-cheque.golden-investigation.json",
        title="The Blank Cheque and the July Crisis, 1914",
        benchmark_role=(
            "Benchmark B (docs/ai-core-instructions/04_DOMAIN_GENERALIZATION_AND_EVALUATION.md): "
            "crisis escalation, communications, knowledge, and causation."
        ),
        expected_package_id="blank-cheque-golden",
        expected_package_hash="719171be10a0f82b6120f196bd805a21ed3d791736d556388d86612cd369b822",
        expected_schema_version="1.0.0",
        expected_package_revision=1,
    ),
    CorpusSource(
        corpus_id="concert-of-europe-1814-1822",
        package_path=FIXTURES_DIR / "concert-of-europe.generated-investigation.json",
        title="The Concert of Europe and Revolutionary Intervention, 1814-1822",
        benchmark_role=(
            "Benchmark A (docs/ai-core-instructions/04_DOMAIN_GENERALIZATION_AND_EVALUATION.md): "
            "modern diplomatic and intervention history."
        ),
        expected_package_id="concert-of-europe-1814-1822",
        expected_package_hash="738611d11b0666f6eebec0b500b3747ef5b23310c4801007f84a665982727827",
        expected_schema_version="1.0.0",
        expected_package_revision=1,
    ),
]


class CorpusRegistry:
    """Loads and caches PackageBackedCorpus instances by corpus_id. A
    corpus is only ever loaded (file read + validated + indexed) on
    first request, never eagerly and never at import time."""

    def __init__(self, sources: list[CorpusSource] | None = None) -> None:
        self._sources: dict[str, CorpusSource] = {}
        self._loaded: dict[str, PackageBackedCorpus] = {}
        for source in sources if sources is not None else BUILTIN_CORPUS_SOURCES:
            self.register(source)

    def register(self, source: CorpusSource) -> None:
        if source.corpus_id in self._sources:
            raise DuplicateCorpusIdError(f'Corpus id "{source.corpus_id}" is already registered')
        self._sources[source.corpus_id] = source

    def list_corpus_ids(self) -> list[str]:
        return sorted(self._sources)

    def get_corpus(self, corpus_id: str) -> PackageBackedCorpus:
        if corpus_id not in self._sources:
            raise UnknownCorpusError(f'No corpus registered with id "{corpus_id}"')
        if corpus_id not in self._loaded:
            source = self._sources[corpus_id]
            self._loaded[corpus_id] = PackageBackedCorpus.load(
                corpus_id=source.corpus_id,
                package_path=source.package_path,
                title=source.title,
                benchmark_role=source.benchmark_role,
                expected_package_id=source.expected_package_id,
                expected_package_hash=source.expected_package_hash,
                expected_schema_version=source.expected_schema_version,
                expected_package_revision=source.expected_package_revision,
            )
        return self._loaded[corpus_id]

    def preload(self, corpus_id: str, corpus: PackageBackedCorpus) -> None:
        """Seed the loaded-corpus cache with an already-constructed instance.

        Used when a corpus needs to be returned wrapped (e.g. a HybridCorpus
        adding semantic re-ranking) rather than plain-loaded from its file. The
        corpus_id must already be registered (so listing/manifest resolution
        still works); this only substitutes the cached instance ``get_corpus``
        returns. Structural typing: any InvestigationCorpus is accepted."""

        if corpus_id not in self._sources:
            raise UnknownCorpusError(f'No corpus registered with id "{corpus_id}"')
        self._loaded[corpus_id] = corpus

    def get_manifest(self, corpus_id: str) -> CorpusManifest:
        return self.get_corpus(corpus_id).get_manifest()

    def list_manifests(self) -> list[CorpusManifest]:
        return [self.get_manifest(corpus_id) for corpus_id in self.list_corpus_ids()]
