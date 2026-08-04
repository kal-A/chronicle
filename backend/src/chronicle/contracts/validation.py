"""Port of validateGeneratedInvestigation() from generatedInvestigation.ts.

Rule numbering and order match the TS source exactly (as of the Phase B
implementation) so the two files can be diffed by eye. If you change a rule
here, change it there too, and vice versa — this is the entire point of
Phase C0's parity guarantee.
"""

from __future__ import annotations

from typing import Any, Iterable

from pydantic import ValidationError

from .generated_investigation import (
    SUPPORTED_GENERATED_INVESTIGATION_VERSION,
    GeneratedInvestigation,
)

PRECISION_RANK = {
    "approximate": 0,
    "region": 1,
    "city": 2,
    "building": 3,
}


class GeneratedInvestigationValidationError(Exception):
    pass


def _fail(message: str) -> None:
    raise GeneratedInvestigationValidationError(message)


def _ids_of(records: Iterable[Any]) -> set[str]:
    return {record.id for record in records}


def _require_reference(ids: set[str], target_id: str, owner: str, target: str) -> None:
    if target_id not in ids:
        _fail(f'{owner} references unknown {target} "{target_id}"')


def _ensure_unique_ids(collections: list[tuple[str, list[Any]]]) -> None:
    owners: dict[str, str] = {}
    for name, records in collections:
        for record in records:
            prior_owner = owners.get(record.id)
            if prior_owner:
                _fail(
                    f'ID "{record.id}" is not unique; it appears in '
                    f"{prior_owner} and {name}"
                )
            owners[record.id] = name


def _evidence_for(
    record: Any,
    expected_type: str,
    links_by_id: dict[str, Any],
) -> list[Any]:
    links = []
    for link_id in record.evidenceLinkIds:
        link = links_by_id.get(link_id)
        if not link:
            _fail(f'Record "{record.id}" references unknown EvidenceLink "{link_id}"')
        if link.targetType.value != expected_type or link.targetId != record.id:
            _fail(f'EvidenceLink "{link_id}" does not target {expected_type} "{record.id}"')
        links.append(link)
    return links


def validate_generated_investigation(data: Any) -> GeneratedInvestigation:
    try:
        investigation = GeneratedInvestigation.model_validate(data)
    except ValidationError as error:
        messages = "; ".join(
            f"{'.'.join(str(part) for part in issue['loc'])}: {issue['msg']}"
            for issue in error.errors()
        )
        raise GeneratedInvestigationValidationError(
            f"GeneratedInvestigation schema validation failed: {messages}"
        ) from error

    # Rule 1: exact supported-version match.
    if investigation.schemaVersion != SUPPORTED_GENERATED_INVESTIGATION_VERSION:
        _fail(
            f'Unsupported GeneratedInvestigation schema version "{investigation.schemaVersion}"; '
            f'this renderer supports "{SUPPORTED_GENERATED_INVESTIGATION_VERSION}"'
        )

    # Rule 2: global ID uniqueness across every collection.
    _ensure_unique_ids([
        ("entities", investigation.entities),
        ("events", investigation.events),
        ("decisions", investigation.decisions),
        ("communications", investigation.communications),
        ("knowledgeStates", investigation.knowledgeStates),
        ("claims", investigation.claims),
        ("relationships", investigation.relationships),
        ("perspectives", investigation.perspectives),
        ("conflicts", investigation.conflicts),
        ("uncertainties", investigation.uncertainties),
        ("researchGaps", investigation.researchGaps),
        ("sources", investigation.sources),
        ("documents", investigation.documents),
        ("passages", investigation.passages),
        ("evidenceLinks", investigation.evidenceLinks),
        ("claimLedgers", investigation.claimLedgers),
        ("timeline", investigation.timeline),
        ("mapAssets", investigation.mapAssets),
        ("mapScenes", investigation.mapScenes),
        ("scenes", investigation.scenes),
        ("synthesis", investigation.presentation.synthesis),
        ("findings", investigation.presentation.findings),
    ])

    entity_ids = _ids_of(investigation.entities)
    place_ids = {e.id for e in investigation.entities if e.entityType == "place"}
    source_ids = _ids_of(investigation.sources)
    document_ids = _ids_of(investigation.documents)
    passage_ids = _ids_of(investigation.passages)
    event_ids = _ids_of(investigation.events)
    claim_ids = _ids_of(investigation.claims)
    relationship_ids = _ids_of(investigation.relationships)
    knowledge_state_ids = _ids_of(investigation.knowledgeStates)
    scene_ids = _ids_of(investigation.scenes)
    narrative_ids = _ids_of(investigation.presentation.synthesis)
    perspective_ids = _ids_of(investigation.perspectives)
    map_asset_ids = _ids_of(investigation.mapAssets)
    map_scene_ids = _ids_of(investigation.mapScenes)
    record_ids = claim_ids | relationship_ids | knowledge_state_ids
    links_by_id = {link.id: link for link in investigation.evidenceLinks}

    # Rule 3: Document -> Source.
    for document in investigation.documents:
        _require_reference(source_ids, document.sourceId, f'Document "{document.id}"', "Source")

    # Rule 4: Passage -> Document.
    for passage in investigation.passages:
        _require_reference(document_ids, passage.documentId, f'Passage "{passage.id}"', "Document")

    # Rule 5: EvidenceLink -> Passage, and -> its typed target.
    for link in investigation.evidenceLinks:
        _require_reference(passage_ids, link.passageId, f'EvidenceLink "{link.id}"', "Passage")
        targets = {
            "claim": claim_ids,
            "relationship": relationship_ids,
            "knownAtTime": knowledge_state_ids,
            "event": event_ids,
        }[link.targetType.value]
        _require_reference(targets, link.targetId, f'EvidenceLink "{link.id}"', link.targetType.value)

    # Rule 6: every Claim needs >=1 supporting EvidenceLink.
    for claim in investigation.claims:
        links = _evidence_for(claim, "claim", links_by_id)
        if not any(link.role.value == "supporting" for link in links):
            _fail(f'Claim "{claim.id}" requires a supporting EvidenceLink')

    # Rule 7: Relationship endpoints + evidence-classification support rules.
    for relationship in investigation.relationships:
        _require_reference(record_ids, relationship.fromId, f'Relationship "{relationship.id}"', "record")
        _require_reference(record_ids, relationship.toId, f'Relationship "{relationship.id}"', "record")
        links = _evidence_for(relationship, "relationship", links_by_id)
        has_supporting = any(link.role.value == "supporting" for link in links)
        has_counterevidence = any(link.role.value == "counterevidence" for link in links)
        if relationship.evidenceClassification.value in ("directly_supported", "indirectly_supported") and not has_supporting:
            _fail(f'Relationship "{relationship.id}" requires a supporting EvidenceLink')
        if relationship.evidenceClassification.value == "disputed" and not (has_supporting and has_counterevidence):
            _fail(f'Disputed Relationship "{relationship.id}" requires supporting and counterevidence links')

    # Rule 8: KnownAtTime -> Entity, and evidence targeting.
    for knowledge_state in investigation.knowledgeStates:
        _require_reference(entity_ids, knowledge_state.personOrInstitutionId, f'KnownAtTime "{knowledge_state.id}"', "Entity")
        _evidence_for(knowledge_state, "knownAtTime", links_by_id)

    # Rule 9: Event -> Place, evidence targeting, relatedRecordIds.
    for event in investigation.events:
        _require_reference(place_ids, event.placeId, f'Event "{event.id}"', "Place")
        _evidence_for(event, "event", links_by_id)
        for record_id in event.relatedRecordIds:
            _require_reference(record_ids, record_id, f'Event "{event.id}"', "displayable record")

    # Rule 10: ClaimEvidenceLedger -> Claim, and its links must target that claim.
    ledgers_by_claim_id = {ledger.claimId: ledger for ledger in investigation.claimLedgers}
    for ledger in investigation.claimLedgers:
        _require_reference(claim_ids, ledger.claimId, f'ClaimEvidenceLedger "{ledger.id}"', "Claim")
        for link_id in ledger.evidenceLinkIds:
            link = links_by_id.get(link_id)
            if not link:
                _fail(f'ClaimEvidenceLedger "{ledger.id}" references unknown EvidenceLink "{link_id}"')
            if link.targetType.value != "claim" or link.targetId != ledger.claimId:
                _fail(f'ClaimEvidenceLedger "{ledger.id}" includes evidence for another record')

    # Rule 11: NarrativeBlock relatedEventId / referencedRecordIds.
    for block in investigation.presentation.synthesis:
        if block.relatedEventId:
            _require_reference(event_ids, block.relatedEventId, f'NarrativeBlock "{block.id}"', "Event")
        for record_id in block.referencedRecordIds:
            _require_reference(record_ids, record_id, f'NarrativeBlock "{block.id}"', "Claim, Relationship, or KnownAtTime record")

    # Rule 12: FindingReference -> its typed record, and major-claim ledger support.
    for finding in investigation.presentation.findings:
        ids = {
            "claim": claim_ids,
            "relationship": relationship_ids,
            "knowledge-state": knowledge_state_ids,
        }[finding.recordType.value]
        _require_reference(ids, finding.recordId, f'Finding "{finding.id}"', finding.recordType.value)
        if finding.recordType.value == "claim" and finding.importance.value == "major":
            ledger = ledgers_by_claim_id.get(finding.recordId)
            if not ledger:
                _fail(f'Major finding "{finding.id}" requires a ClaimEvidenceLedger for claim "{finding.recordId}"')
            has_supporting_passage = any(
                (links_by_id.get(link_id).role.value == "supporting" if links_by_id.get(link_id) else False)
                for link_id in ledger.evidenceLinkIds
            )
            if not has_supporting_passage:
                _fail(f'Major finding "{finding.id}" lacks a supporting Passage through its claim ledger')

    # Rule 13: Presentation sceneIds / perspectiveIds.
    for scene_id in investigation.presentation.sceneIds:
        _require_reference(scene_ids, scene_id, "Presentation", "Scene")
    for perspective_id in investigation.presentation.perspectiveIds:
        _require_reference(perspective_ids, perspective_id, "Presentation", "Perspective")

    # Rule 14: every InvestigationScene's id-array fields resolve.
    for scene in investigation.scenes:
        references: list[tuple[list[str], set[str], str]] = [
            (scene.placeIds, place_ids, "Place"),
            (scene.entityIds, entity_ids, "Entity"),
            (scene.sourceIds, source_ids, "Source"),
            (scene.documentIds, document_ids, "Document"),
            (scene.passageIds, passage_ids, "Passage"),
            (scene.eventIds, event_ids, "Event"),
            (scene.claimIds, claim_ids, "Claim"),
            (scene.relationshipIds, relationship_ids, "Relationship"),
            (scene.knowledgeStateIds, knowledge_state_ids, "KnownAtTime"),
            (scene.narrativeBlockIds, narrative_ids, "NarrativeBlock"),
        ]
        for ids, known_ids, type_name in references:
            for record_id in ids:
                _require_reference(known_ids, record_id, f'Scene "{scene.id}"', type_name)
        if scene.mapSceneId:
            _require_reference(map_scene_ids, scene.mapSceneId, f'Scene "{scene.id}"', "MapScene")

    # Rule 15: MapScene -> Scene/MapAsset, rights/period-fit gates, marker precision.
    places_by_id = {e.id: e for e in investigation.entities if e.entityType == "place"}
    map_assets_by_id = {asset.id: asset for asset in investigation.mapAssets}
    for map_scene in investigation.mapScenes:
        _require_reference(scene_ids, map_scene.sceneId, f'MapScene "{map_scene.id}"', "Scene")
        _require_reference(map_asset_ids, map_scene.mapAssetId, f'MapScene "{map_scene.id}"', "MapAsset")
        asset = map_assets_by_id[map_scene.mapAssetId]
        if asset.rightsStatus.value not in ("public-domain", "licensed"):
            _fail(f'Map asset "{asset.id}" cannot be displayed because its rights status is "{asset.rightsStatus.value}"')
        if asset.periodFitDecision.value not in ("approved", "conditional"):
            _fail(f'Map asset "{asset.id}" cannot be displayed without an approved period-fit decision')
        for marker in map_scene.markers:
            place = places_by_id.get(marker.placeId)
            if not place:
                _fail(f'Map marker references unknown Place "{marker.placeId}" in MapScene "{map_scene.id}"')
            supported_rank = max(PRECISION_RANK[period.precision.value] for period in place.periodRecords)
            if PRECISION_RANK[marker.precision.value] > supported_rank:
                _fail(f'Map marker precision "{marker.precision.value}" exceeds Place "{place.id}" evidence precision')

    # Rule 16: TimelineEntry -> Event.
    for entry in investigation.timeline:
        _require_reference(event_ids, entry.eventId, f'TimelineEntry "{entry.id}"', "Event")

    # Rule 17: InteractionSpecification.defaultSceneId -> Scene.
    _require_reference(scene_ids, investigation.interactionSpec.defaultSceneId, "InteractionSpecification", "Scene")

    # Rule 18: no failed required verification checks.
    if any(check.status.value == "failed" for check in investigation.generationReport.verificationChecks):
        _fail("GenerationReport contains a failed required verification check")

    # Rule 19: partial status <-> partial report outcome.
    if investigation.status.value == "partial" and investigation.generationReport.outcome.value != "partial":
        _fail("A partial package must carry a partial GenerationReport outcome")

    # Rule 20: published packages require reviewed/disputed + public records.
    if investigation.status.value == "published":
        public_records = [
            *investigation.claims,
            *investigation.relationships,
            *investigation.knowledgeStates,
            *investigation.events,
        ]
        for record in public_records:
            if record.reviewStatus.value not in ("reviewed", "disputed"):
                _fail(f'Published package record "{record.id}" must be reviewed or disputed')
            if record.visibility.value != "public":
                _fail(f'Published package record "{record.id}" must be public')
        for document in investigation.documents:
            if document.visibility.value != "public":
                _fail(f'Published package Document "{document.id}" must be public')

    return investigation
