"""Historical-extraction provider — chronicle_phase_c_adjusted_plan.md §8.

Part of HISTORICAL_MODEL_ASSEMBLED (composed with timeline.py, relationships.py,
geography.py in providers/registry.py). Produces the entities/events/claims/
evidenceLinks that everything downstream (relationships, the composer)
builds on — the first place real schema-shaped historical-model records
appear, deliberately generic and placeholder-labeled.
"""

from ..util import SENTINEL_DATE


def extract_historical_model(data: dict) -> dict:
    slug = data["slug"]
    topic = data["topic"]

    place_id = f"place-{slug}"
    person_id = f"person-{slug}"
    entities = [
        {
            "id": place_id,
            "entityType": "place",
            "canonicalName": f"Unspecified locale ({topic})",
            "reviewStatus": "proposed",
            "periodRecords": [
                {
                    "periodLabel": "Placeholder period — Phase C2 generic mock",
                    "nameAtTime": f"Unspecified locale ({topic})",
                    "controllingPolity": "Unknown — Phase C2 generic mock",
                    "precision": "approximate",
                }
            ],
        },
        {
            "id": person_id,
            "entityType": "person",
            "canonicalName": f"An unnamed figure associated with {topic}",
            "alsoKnownAs": [],
            "description": "Placeholder person entity generated for Phase C2 pipeline verification.",
            "reviewStatus": "proposed",
        },
    ]

    passage_id = data["corpus"]["passages"][0]["id"]
    event_id = f"event-{slug}-1"
    claim_1_id = f"claim-{slug}-1"
    claim_2_id = f"claim-{slug}-2"
    evidence_claim_1_id = f"evidence-{claim_1_id}-1"
    evidence_claim_2_id = f"evidence-{claim_2_id}-1"
    evidence_event_id = f"evidence-{event_id}-1"

    evidence_links = [
        {
            "id": evidence_claim_1_id,
            "targetType": "claim",
            "targetId": claim_1_id,
            "passageId": passage_id,
            "role": "supporting",
        },
        {
            "id": evidence_claim_2_id,
            "targetType": "claim",
            "targetId": claim_2_id,
            "passageId": passage_id,
            "role": "supporting",
        },
        {
            "id": evidence_event_id,
            "targetType": "event",
            "targetId": event_id,
            "passageId": passage_id,
            "role": "supporting",
        },
    ]

    claims = [
        {
            "id": claim_1_id,
            "statement": f"A mock primary account describes an event concerning {topic}.",
            "directOrInferred": "direct",
            "reviewStatus": "proposed",
            "visibility": "public",
            "evidenceLinkIds": [evidence_claim_1_id],
        },
        {
            "id": claim_2_id,
            "statement": f"The mock account's description is consistent with a broader pattern concerning {topic}.",
            "directOrInferred": "inferred",
            "reviewStatus": "proposed",
            "visibility": "public",
            "evidenceLinkIds": [evidence_claim_2_id],
        },
    ]

    events = [
        {
            "id": event_id,
            "title": f"A placeholder event concerning {topic}",
            "placeId": place_id,
            "eventTime": {
                "precision": "approximate",
                "earliest": SENTINEL_DATE,
                "latest": SENTINEL_DATE,
                "label": "Placeholder date",
            },
            "evidenceLinkIds": [evidence_event_id],
            "relatedRecordIds": [claim_1_id],
            "reviewStatus": "proposed",
            "visibility": "public",
        }
    ]

    return {
        **data,
        "entities": entities,
        "events": events,
        "claims": claims,
        "evidenceLinks": evidence_links,
        "knowledgeStates": [],
    }
