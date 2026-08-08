"""PackageBackedCorpus (Phase E2): the only InvestigationCorpus
implementation today, backed by an existing, already-generated,
already-validated GeneratedInvestigation JSON package on disk. No
database -- in-memory indexes built once at load time, per ADR-003's
finding that the corpus service queries the already-generated package's
own embedded records, not a database that doesn't exist.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from ..contracts.generated_investigation import (
    Document,
    Entity,
    GeneratedClaim,
    GeneratedEvent,
    GeneratedEvidenceLink,
    GeneratedInvestigation,
    GeneratedKnownAtTime,
    GeneratedRelationship,
    Passage,
    Source,
)
from ..contracts.validation import GeneratedInvestigationValidationError, validate_generated_investigation
from ..workflow.hashing import stable_json_hash
from .contracts import CorpusManifest, PassageSearchRequest, PassageSearchResult
from .errors import CorpusBoundaryError, InvalidPackageError, UnknownRecordError
from .indexing import CorpusIndex, build_index
from .search import search_passages as _search_passages

# A manifest's supported_capabilities are derived from what the package
# actually contains, never hardcoded per corpus -- see manifest.py's
# BUILTIN_CORPUS_SOURCES, which carries no capability list of its own.
CAPABILITY_PASSAGES = "passages"
CAPABILITY_CLAIMS = "claims"
CAPABILITY_RELATIONSHIPS = "relationships"
CAPABILITY_TIMELINE = "timeline"
CAPABILITY_MAP_CONTEXT = "map_context"
CAPABILITY_KNOWLEDGE_STATES = "knowledge_states"
CAPABILITY_SOURCE_COMPARISON = "source_comparison"


def _derive_capabilities(investigation: GeneratedInvestigation) -> set[str]:
    capabilities: set[str] = set()
    if investigation.passages:
        capabilities.add(CAPABILITY_PASSAGES)
    if investigation.claims:
        capabilities.add(CAPABILITY_CLAIMS)
    if investigation.relationships:
        capabilities.add(CAPABILITY_RELATIONSHIPS)
    if investigation.timeline:
        capabilities.add(CAPABILITY_TIMELINE)
    if investigation.mapScenes and investigation.mapAssets:
        capabilities.add(CAPABILITY_MAP_CONTEXT)
    if investigation.knowledgeStates:
        capabilities.add(CAPABILITY_KNOWLEDGE_STATES)
    if len(investigation.sources) >= 2:
        capabilities.add(CAPABILITY_SOURCE_COMPARISON)
    return capabilities


class PackageBackedCorpus:
    """Implements InvestigationCorpus structurally (see protocol.py)."""

    def __init__(
        self,
        *,
        corpus_id: str,
        manifest: CorpusManifest,
        investigation: GeneratedInvestigation,
        index: CorpusIndex,
    ) -> None:
        self.__corpus_id = corpus_id
        self.__manifest = manifest
        self.__investigation = investigation
        self.__index = index

    @property
    def corpus_id(self) -> str:
        return self.__corpus_id

    @classmethod
    def load(
        cls,
        *,
        corpus_id: str,
        package_path: str | Path,
        title: str,
        benchmark_role: str,
        expected_package_id: str | None = None,
        expected_package_hash: str | None = None,
        expected_schema_version: str | None = None,
        expected_package_revision: int | None = None,
    ) -> "PackageBackedCorpus":
        path = Path(package_path)
        if not path.exists():
            raise InvalidPackageError(f'No package file found at "{package_path}" for corpus "{corpus_id}"')

        try:
            raw_text = path.read_text(encoding="utf-8")
            data = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise InvalidPackageError(f'Corpus "{corpus_id}" package is not valid JSON: {exc}') from exc

        try:
            investigation = validate_generated_investigation(data)
        except GeneratedInvestigationValidationError as exc:
            raise InvalidPackageError(f'Corpus "{corpus_id}" package failed validation: {exc}') from exc

        package_hash = stable_json_hash(data)
        expected_checks = (
            ("packageId", expected_package_id, investigation.packageId),
            ("hash", expected_package_hash, package_hash),
            ("schemaVersion", expected_schema_version, investigation.schemaVersion),
            ("packageRevision", expected_package_revision, investigation.packageRevision),
        )
        for label, expected, actual in expected_checks:
            if expected is not None and actual != expected:
                raise InvalidPackageError(
                    f'Corpus "{corpus_id}" expected package {label} {expected!r}, got {actual!r}'
                )

        # The index owns this validated object. Every public read returns a
        # deep copy so callers cannot mutate the registry's cached corpus.
        index = build_index(investigation)
        manifest = CorpusManifest(
            corpusId=corpus_id,
            packagePath=str(package_path),
            title=title,
            benchmarkRole=benchmark_role,
            packageHash=package_hash,
            schemaVersion=investigation.schemaVersion,
            supportedCapabilities=_derive_capabilities(investigation),
            # Derived from the package's own GenerationReport, never
            # authored/invented alongside the manifest -- if the package's
            # own report discloses no omissions, the manifest says none.
            knownOmissions=list(investigation.generationReport.omissions),
        )
        return cls(corpus_id=corpus_id, manifest=manifest, investigation=investigation, index=index)

    def get_manifest(self) -> CorpusManifest:
        return self.__manifest.model_copy(deep=True)

    def get_investigation(self) -> GeneratedInvestigation:
        return self.__investigation.model_copy(deep=True)

    def _lookup(self, table: dict, record_id: str, kind: str):
        record = table.get(record_id)
        if record is None:
            raise UnknownRecordError(
                f'Corpus "{self.__corpus_id}" has no {kind} "{record_id}" '
                "(unknown, or it belongs to a different corpus)"
            )
        return record.model_copy(deep=True)

    def get_source(self, source_id: str) -> Source:
        return self._lookup(self.__index.sources_by_id, source_id, "Source")

    def get_document(self, document_id: str) -> Document:
        return self._lookup(self.__index.documents_by_id, document_id, "Document")

    def get_passage(self, passage_id: str) -> Passage:
        return self._lookup(self.__index.passages_by_id, passage_id, "Passage")

    def get_claim(self, claim_id: str) -> GeneratedClaim:
        return self._lookup(self.__index.claims_by_id, claim_id, "Claim")

    def get_relationship(self, relationship_id: str) -> GeneratedRelationship:
        return self._lookup(self.__index.relationships_by_id, relationship_id, "Relationship")

    def get_event(self, event_id: str) -> GeneratedEvent:
        return self._lookup(self.__index.events_by_id, event_id, "Event")

    def get_entity(self, entity_id: str) -> Entity:
        return self._lookup(self.__index.entities_by_id, entity_id, "Entity")

    def get_place(self, place_id: str) -> Entity:
        entity = self._lookup(self.__index.entities_by_id, place_id, "Place")
        if entity.entityType != "place":
            raise UnknownRecordError(f'"{place_id}" exists in corpus "{self.__corpus_id}" but is not a Place')
        return entity

    def get_knowledge_state(self, knowledge_state_id: str) -> GeneratedKnownAtTime:
        return self._lookup(self.__index.knowledge_states_by_id, knowledge_state_id, "KnownAtTime")

    def search_passages(self, request: PassageSearchRequest) -> PassageSearchResult:
        if request.corpusId != self.__corpus_id:
            raise CorpusBoundaryError(
                f'Search request scoped to corpus "{request.corpusId}" cannot be run '
                f'against corpus "{self.__corpus_id}"'
            )
        return _search_passages(self.__index, request)

    def get_evidence_links_for(self, record_id: str) -> list[GeneratedEvidenceLink]:
        return [record.model_copy(deep=True) for record in self.__index.evidence_links_by_target.get(record_id, [])]

    def get_passages_for(self, record_id: str) -> list[Passage]:
        links = self.__index.evidence_links_by_target.get(record_id, [])
        passages = []
        for link in links:
            passage = self.__index.passages_by_id.get(link.passageId)
            if passage is not None:
                passages.append(passage.model_copy(deep=True))
        return passages

    def get_relationships_touching(self, node_id: str) -> list[GeneratedRelationship]:
        ids = self.__index.relationships_by_node.get(node_id, [])
        return [self.__index.relationships_by_id[rid].model_copy(deep=True) for rid in ids]

    def get_events_at_place(self, place_id: str) -> list[GeneratedEvent]:
        ids = self.__index.events_by_place.get(place_id, [])
        return [self.__index.events_by_id[eid].model_copy(deep=True) for eid in ids]

    def get_events_ordered(self) -> list[GeneratedEvent]:
        return [self.__index.events_by_id[eid].model_copy(deep=True) for eid in self.__index.events_sorted_by_date]

    def get_knowledge_states_for(self, entity_id: str) -> list[GeneratedKnownAtTime]:
        ids = self.__index.knowledge_states_by_entity.get(entity_id, [])
        return [self.__index.knowledge_states_by_id[kid].model_copy(deep=True) for kid in ids]

    @property
    def index(self) -> CorpusIndex:
        """Defensive-copy inspection escape hatch outside the protocol.

        Production tools use evidence-preserving corpus methods instead;
        callers cannot mutate the cached index through this projection.
        """
        return deepcopy(self.__index)
