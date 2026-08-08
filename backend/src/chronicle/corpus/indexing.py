"""Deterministic in-memory indexes over a validated GeneratedInvestigation
(Phase E2). Pure data structure, no behavior beyond construction -- a
plain dataclass, not Pydantic, since it holds references to already-
validated Pydantic record instances and is never itself serialized
(mirrors ai/contracts/structured_generation.py's precedent for in-process-
only shapes).

Every index here is derived, never invented: each entry traces back to an
explicit field on a validated record (documentId, evidenceLinkIds, etc.).
Notably absent: a claims-by-entity index. GeneratedClaim has no entity-
reference field anywhere in the contract, so there is no structural edge
to index -- see corpus/search.py's entity-name text matching for the only
honest way to relate a claim to an entity, which is explicitly a text
match, not a structural association.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from typing import Union

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

RecordIdRecord = Union[GeneratedClaim, GeneratedRelationship, GeneratedKnownAtTime]


@dataclass
class CorpusIndex:
    investigation: GeneratedInvestigation

    sources_by_id: dict[str, Source] = field(default_factory=dict)
    documents_by_id: dict[str, Document] = field(default_factory=dict)
    passages_by_id: dict[str, Passage] = field(default_factory=dict)
    claims_by_id: dict[str, GeneratedClaim] = field(default_factory=dict)
    relationships_by_id: dict[str, GeneratedRelationship] = field(default_factory=dict)
    events_by_id: dict[str, GeneratedEvent] = field(default_factory=dict)
    entities_by_id: dict[str, Entity] = field(default_factory=dict)
    places_by_id: dict[str, Entity] = field(default_factory=dict)
    knowledge_states_by_id: dict[str, GeneratedKnownAtTime] = field(default_factory=dict)
    evidence_links_by_id: dict[str, GeneratedEvidenceLink] = field(default_factory=dict)
    record_ids_by_id: dict[str, RecordIdRecord] = field(default_factory=dict)

    evidence_links_by_target: dict[str, list[GeneratedEvidenceLink]] = field(default_factory=dict)
    evidence_links_by_passage: dict[str, list[GeneratedEvidenceLink]] = field(default_factory=dict)
    passages_by_document: dict[str, list[str]] = field(default_factory=dict)
    passages_by_source: dict[str, list[str]] = field(default_factory=dict)
    passages_by_claim: dict[str, list[str]] = field(default_factory=dict)
    passages_by_relationship: dict[str, list[str]] = field(default_factory=dict)
    passages_by_event: dict[str, list[str]] = field(default_factory=dict)
    passages_by_knowledge_state: dict[str, list[str]] = field(default_factory=dict)
    events_by_place: dict[str, list[str]] = field(default_factory=dict)
    events_sorted_by_date: list[str] = field(default_factory=list)
    knowledge_states_by_entity: dict[str, list[str]] = field(default_factory=dict)
    relationships_by_node: dict[str, list[str]] = field(default_factory=dict)

    @property
    def all_ids(self) -> set[str]:
        return (
            set(self.sources_by_id)
            | set(self.documents_by_id)
            | set(self.passages_by_id)
            | set(self.claims_by_id)
            | set(self.relationships_by_id)
            | set(self.events_by_id)
            | set(self.entities_by_id)
            | set(self.knowledge_states_by_id)
            | set(self.evidence_links_by_id)
        )


def build_index(investigation: GeneratedInvestigation) -> CorpusIndex:
    index = CorpusIndex(investigation=investigation)

    index.sources_by_id = {s.id: s for s in investigation.sources}
    index.documents_by_id = {d.id: d for d in investigation.documents}
    index.passages_by_id = {p.id: p for p in investigation.passages}
    index.claims_by_id = {c.id: c for c in investigation.claims}
    index.relationships_by_id = {r.id: r for r in investigation.relationships}
    index.events_by_id = {e.id: e for e in investigation.events}
    index.entities_by_id = {e.id: e for e in investigation.entities}
    index.places_by_id = {e.id: e for e in investigation.entities if e.entityType == "place"}
    index.knowledge_states_by_id = {k.id: k for k in investigation.knowledgeStates}
    index.evidence_links_by_id = {link.id: link for link in investigation.evidenceLinks}
    index.record_ids_by_id = {
        **index.claims_by_id,
        **index.relationships_by_id,
        **index.knowledge_states_by_id,
    }

    evidence_links_by_target: dict[str, list[GeneratedEvidenceLink]] = defaultdict(list)
    evidence_links_by_passage: dict[str, list[GeneratedEvidenceLink]] = defaultdict(list)
    for link in investigation.evidenceLinks:
        evidence_links_by_target[link.targetId].append(link)
        evidence_links_by_passage[link.passageId].append(link)
    index.evidence_links_by_target = dict(evidence_links_by_target)
    index.evidence_links_by_passage = dict(evidence_links_by_passage)

    passages_by_document: dict[str, list[str]] = defaultdict(list)
    for passage in investigation.passages:
        passages_by_document[passage.documentId].append(passage.id)
    index.passages_by_document = dict(passages_by_document)

    passages_by_source: dict[str, list[str]] = defaultdict(list)
    for passage in investigation.passages:
        document = index.documents_by_id.get(passage.documentId)
        if document is not None:
            passages_by_source[document.sourceId].append(passage.id)
    index.passages_by_source = dict(passages_by_source)

    def _passages_for(record_ids: list[str]) -> list[str]:
        result: dict[str, list[str]] = defaultdict(list)
        for record_id in record_ids:
            links = index.evidence_links_by_target.get(record_id, [])
            for link in links:
                result[record_id].append(link.passageId)
        return result

    index.passages_by_claim = dict(_passages_for(list(index.claims_by_id)))
    index.passages_by_relationship = dict(_passages_for(list(index.relationships_by_id)))
    index.passages_by_event = dict(_passages_for(list(index.events_by_id)))
    index.passages_by_knowledge_state = dict(_passages_for(list(index.knowledge_states_by_id)))

    events_by_place: dict[str, list[str]] = defaultdict(list)
    for event in investigation.events:
        events_by_place[event.placeId].append(event.id)
    index.events_by_place = dict(events_by_place)

    timeline_order = {entry.eventId: entry.order for entry in investigation.timeline}

    def _event_sort_key(event_id: str) -> tuple[int, int | date, str]:
        event = index.events_by_id[event_id]
        if event_id in timeline_order:
            return (0, timeline_order[event_id], event_id)
        return (1, event.eventTime.earliest, event_id)

    index.events_sorted_by_date = sorted(index.events_by_id, key=_event_sort_key)

    knowledge_states_by_entity: dict[str, list[str]] = defaultdict(list)
    for knowledge_state in investigation.knowledgeStates:
        knowledge_states_by_entity[knowledge_state.personOrInstitutionId].append(knowledge_state.id)
    index.knowledge_states_by_entity = dict(knowledge_states_by_entity)

    relationships_by_node: dict[str, list[str]] = defaultdict(list)
    for relationship in investigation.relationships:
        relationships_by_node[relationship.fromId].append(relationship.id)
        relationships_by_node[relationship.toId].append(relationship.id)
    index.relationships_by_node = dict(relationships_by_node)

    return index
