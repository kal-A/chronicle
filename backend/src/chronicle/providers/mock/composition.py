"""Investigation composer — chronicle_phase_c_adjusted_plan.md §8.

Assembles every accumulated stage output into a GeneratedInvestigation-
shaped dict (INVESTIGATION_COMPOSED's output). The next stage (verification)
validates it against C0's Pydantic contract; nothing here is trusted to be
correct on its own — composing correctly, not fabricating confidence, is
the job.
"""

from ...contracts.generated_investigation import SUPPORTED_GENERATED_INVESTIGATION_VERSION
from ..util import MOCK_CONTENT_WARNING, SENTINEL_DATETIME


def compose_investigation(data: dict) -> dict:
    slug = data["slug"]
    topic = data["topic"]

    claim_1_id = data["claims"][0]["id"]
    scene_id = f"scene-{slug}"
    narrative_id = f"narrative-{slug}-1"
    ledger_id = f"ledger-{claim_1_id}"
    finding_id = f"finding-{slug}-1"

    narrative_block = {
        "id": narrative_id,
        "order": 0,
        "text": f"A synthetic, Phase-C2-generated account concerning {topic}. Not real historical narrative.",
        "isMaterialAssertion": True,
        "referencedRecordIds": [claim_1_id],
        "relatedEventId": data["events"][0]["id"],
    }

    claim_1_evidence_link_ids = [
        link["id"]
        for link in data["evidenceLinks"]
        if link["targetType"] == "claim" and link["targetId"] == claim_1_id
    ]
    claim_ledger = {
        "id": ledger_id,
        "claimId": claim_1_id,
        "evidenceLinkIds": claim_1_evidence_link_ids,
        "conclusion": "supported",
        "limitations": ["Phase C2 generic mock — not real historical scholarship."],
    }

    finding = {
        "id": finding_id,
        "recordType": "claim",
        "recordId": claim_1_id,
        "label": "The mock account describes an event.",
        "importance": "major",
    }

    place_id = data["entities"][0]["id"]
    person_id = data["entities"][1]["id"]

    scene = {
        "id": scene_id,
        "title": f"A generic investigation into: {topic}",
        "curationStatus": "prototype-curated",
        "dateRange": data["scope"]["dateRange"],
        "placeIds": [place_id],
        "entityIds": [place_id, person_id],
        "sourceIds": [s["id"] for s in data["corpus"]["sources"]],
        "documentIds": [d["id"] for d in data["corpus"]["documents"]],
        "passageIds": [p["id"] for p in data["corpus"]["passages"]],
        "eventIds": [e["id"] for e in data["events"]],
        "claimIds": [c["id"] for c in data["claims"]],
        "relationshipIds": [r["id"] for r in data["relationships"]],
        "knowledgeStateIds": [],
        "narrativeBlockIds": [narrative_id],
        "mapSceneId": None,
    }

    package = {
        "schemaVersion": SUPPORTED_GENERATED_INVESTIGATION_VERSION,
        "packageId": f"generic-mock-{slug}",
        "packageRevision": 1,
        "generatedAt": SENTINEL_DATETIME,
        "request": {
            "id": f"request-{slug}",
            "rawInput": topic,
            "requestType": "event-reconstruction",
            "requestedDepth": "focused",
            "createdAt": SENTINEL_DATETIME,
        },
        "scope": data["scope"],
        "status": "partial",
        "presentation": {
            "title": f"A generic investigation into: {topic}",
            "synthesis": [narrative_block],
            "findings": [finding],
            "sceneIds": [scene_id],
            "perspectiveIds": [],
        },
        "entities": data["entities"],
        "events": data["events"],
        "decisions": [],
        "communications": [],
        "knowledgeStates": data["knowledgeStates"],
        "claims": data["claims"],
        "relationships": data["relationships"],
        "perspectives": [],
        "conflicts": [],
        "uncertainties": [],
        "researchGaps": [],
        "sources": data["corpus"]["sources"],
        "documents": data["corpus"]["documents"],
        "passages": data["corpus"]["passages"],
        "evidenceLinks": data["evidenceLinks"],
        "claimLedgers": [claim_ledger],
        "timeline": data["timeline"],
        "mapAssets": data["mapAssets"],
        "mapScenes": data["mapScenes"],
        "scenes": [scene],
        "interactionSpec": {
            "defaultSceneId": scene_id,
            "focusKinds": [
                "scene",
                "event",
                "entity",
                "claim",
                "relationship",
                "source",
                "passage",
                "timeRange",
            ],
            "enabledFacets": ["narrative", "timeline", "map", "graph", "evidence"],
            "omittedCapabilities": ["real-geographic-map"],
        },
        "generationReport": {
            "outcome": "partial",
            "stages": [
                {"id": stage_id, "status": "passed"}
                for stage_id in [
                    "SCOPE_PROPOSED",
                    "DISCOVERY_QUERIES_PREPARED",
                    "SOURCE_CANDIDATES_DISCOVERED",
                    "SOURCES_ASSESSED",
                    "CORPUS_PREPARED",
                    "HISTORICAL_MODEL_ASSEMBLED",
                    "INVESTIGATION_COMPOSED",
                ]
            ],
            "omissions": [
                "No real geographic/map data available for generic mock topics in Phase C2 — "
                "mapAssets/mapScenes intentionally empty."
            ],
            "warnings": [MOCK_CONTENT_WARNING],
            "verificationChecks": [],
        },
    }

    return {**data, "package": package}
