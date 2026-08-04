"""Real relationships between the curated claims, including one genuine
`disputed` relationship (Britain vs. the Troppau doctrine) with both a
supporting and a counterevidence link — exercising
validate_generated_investigation()'s rule 7 with real historical content
instead of C2's generic mock disagreement."""

TROPPAU_PASSAGE_ID = "passage-troppau-protocol-1"
CASTLEREAGH_PASSAGE_ID = "passage-castlereagh-state-paper-1"


def propose_relationships(data: dict) -> dict:
    relationships = [
        {
            "id": "rel-troppau-supports-naples",
            "relationshipType": "establishes the doctrine invoked by",
            "fromId": "claim-troppau-doctrine",
            "toId": "claim-naples-intervention",
            "directOrInferred": "inferred",
            "evidenceClassification": "directly_supported",
            "reviewStatus": "proposed",
            "visibility": "public",
            "evidenceLinkIds": ["evidence-rel-troppau-naples-1"],
        },
        {
            "id": "rel-castlereagh-disputes-troppau",
            "relationshipType": "disputes",
            "fromId": "claim-castlereagh-dissent",
            "toId": "claim-troppau-doctrine",
            "directOrInferred": "direct",
            "evidenceClassification": "disputed",
            "reviewStatus": "disputed",
            "visibility": "public",
            "evidenceLinkIds": ["evidence-rel-castlereagh-troppau-supporting", "evidence-rel-castlereagh-troppau-counter"],
        },
        {
            "id": "rel-verona-extends-troppau",
            "relationshipType": "extends",
            "fromId": "claim-verona-spain",
            "toId": "claim-troppau-doctrine",
            "directOrInferred": "inferred",
            "evidenceClassification": "indirectly_supported",
            "reviewStatus": "proposed",
            "visibility": "public",
            "evidenceLinkIds": ["evidence-rel-verona-troppau-1"],
        },
    ]

    new_links = [
        {"id": "evidence-rel-troppau-naples-1", "targetType": "relationship", "targetId": "rel-troppau-supports-naples", "passageId": TROPPAU_PASSAGE_ID, "role": "supporting"},
        {"id": "evidence-rel-castlereagh-troppau-supporting", "targetType": "relationship", "targetId": "rel-castlereagh-disputes-troppau", "passageId": CASTLEREAGH_PASSAGE_ID, "role": "supporting"},
        {"id": "evidence-rel-castlereagh-troppau-counter", "targetType": "relationship", "targetId": "rel-castlereagh-disputes-troppau", "passageId": TROPPAU_PASSAGE_ID, "role": "counterevidence"},
        {"id": "evidence-rel-verona-troppau-1", "targetType": "relationship", "targetId": "rel-verona-extends-troppau", "passageId": TROPPAU_PASSAGE_ID, "role": "supporting"},
    ]

    return {**data, "relationships": relationships, "evidenceLinks": [*data.get("evidenceLinks", []), *new_links]}
