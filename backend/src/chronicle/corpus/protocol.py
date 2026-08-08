"""The provider-independent InvestigationCorpus protocol (Phase E2).

A structural typing.Protocol, matching Phase E1's ModelProvider precedent
(docs/decisions/ADR-003-llm-agent-system-is-product-core.md) -- read-only,
deterministic, corpus-scoped. PackageBackedCorpus (package_corpus.py) is
the only implementation today; a future non-JSON-backed corpus (e.g. one
backed by a real database, Phase G+) could satisfy this same shape without
touching any tool that consumes it.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..contracts.generated_investigation import (
    Document,
    Entity,
    GeneratedClaim,
    GeneratedEvent,
    GeneratedEvidenceLink,
    GeneratedInvestigation,
    GeneratedRelationship,
    Passage,
    Source,
)
from ..contracts.generated_investigation import GeneratedKnownAtTime as KnownAtTime
from .contracts import CorpusManifest, PassageSearchRequest, PassageSearchResult


@runtime_checkable
class InvestigationCorpus(Protocol):
    @property
    def corpus_id(self) -> str: ...

    def get_manifest(self) -> CorpusManifest: ...

    def get_investigation(self) -> GeneratedInvestigation: ...

    def get_source(self, source_id: str) -> Source: ...

    def get_document(self, document_id: str) -> Document: ...

    def get_passage(self, passage_id: str) -> Passage: ...

    def get_claim(self, claim_id: str) -> GeneratedClaim: ...

    def get_relationship(self, relationship_id: str) -> GeneratedRelationship: ...

    def get_event(self, event_id: str) -> GeneratedEvent: ...

    def get_entity(self, entity_id: str) -> Entity: ...

    def get_place(self, place_id: str) -> Entity:
        """Same underlying record type as get_entity -- Chronicle has no
        separate Place collection, places are Entity records with
        entityType == "place". Raises UnknownRecordError if the id exists
        but isn't place-typed, not a silent type coercion."""
        ...

    def get_knowledge_state(self, knowledge_state_id: str) -> KnownAtTime: ...

    def search_passages(self, request: PassageSearchRequest) -> PassageSearchResult: ...

    # Generic evidence-preserving queries every corpus implementation must
    # support, beyond single-record lookup -- adjusted in per the spec's
    # own allowance ("adjust this interface after inspecting the current
    # contracts"). Each traces back to an explicit stored field; none
    # infer a relationship the data doesn't assert.

    def get_evidence_links_for(self, record_id: str) -> list[GeneratedEvidenceLink]:
        """Stored EvidenceLinks whose targetId is this record."""
        ...

    def get_passages_for(self, record_id: str) -> list[Passage]:
        """Passages evidencing this record, via its EvidenceLinks."""
        ...

    def get_relationships_touching(self, node_id: str) -> list[GeneratedRelationship]:
        """Relationships where node_id is fromId or toId."""
        ...

    def get_events_at_place(self, place_id: str) -> list[GeneratedEvent]: ...

    def get_events_ordered(self) -> list[GeneratedEvent]:
        """Every event in stored TimelineEntry order, then by earliest
        event time and ID as deterministic fallbacks."""
        ...

    def get_knowledge_states_for(self, entity_id: str) -> list[KnownAtTime]: ...
