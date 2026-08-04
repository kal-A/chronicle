"""Relationship provider — chronicle_phase_c_adjusted_plan.md §8.

Part of HISTORICAL_MODEL_ASSEMBLED, run after extraction.py. Proposes one
relationship between the two mock claims, classified "directly_supported"
with a genuine supporting EvidenceLink — exercising
validate_generated_investigation()'s rule 7 honestly rather than skipping
evidence-classification requirements by picking an unclassified type.
"""


def propose_relationships(data: dict) -> dict:
    slug = data["slug"]
    claim_1_id, claim_2_id = (claim["id"] for claim in data["claims"])
    relationship_id = f"rel-{slug}-1"
    evidence_id = f"evidence-{relationship_id}-1"

    relationship = {
        "id": relationship_id,
        "relationshipType": "supports",
        "fromId": claim_1_id,
        "toId": claim_2_id,
        "directOrInferred": "inferred",
        "evidenceClassification": "directly_supported",
        "reviewStatus": "proposed",
        "visibility": "public",
        "evidenceLinkIds": [evidence_id],
    }

    passage_id = data["corpus"]["passages"][0]["id"]
    new_link = {
        "id": evidence_id,
        "targetType": "relationship",
        "targetId": relationship_id,
        "passageId": passage_id,
        "role": "supporting",
    }

    return {
        **data,
        "relationships": [relationship],
        "evidenceLinks": [*data["evidenceLinks"], new_link],
    }
