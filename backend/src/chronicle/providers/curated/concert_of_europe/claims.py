"""Real claims for the Concert of Europe congresses. C5 (Verona/Spain) is
deliberately "inferred" and its supporting evidence is the Troppau Protocol
passage rather than a dedicated Verona primary document — an honest,
disclosed gap (see composition.py's generationReport.omissions), the same
pattern docs/research/scene-2-map-source.md uses for its Balkans gap."""

VIENNA_PASSAGE_ID = "passage-vienna-final-act-1"
TROPPAU_PASSAGE_ID = "passage-troppau-protocol-1"
CASTLEREAGH_PASSAGE_ID = "passage-castlereagh-state-paper-1"


def extract_claims(data: dict) -> dict:
    claims = [
        {
            "id": "claim-vienna-settlement",
            "statement": (
                "The Congress of Vienna's General Treaty (9 June 1815) established a new territorial "
                "and diplomatic order for Europe following the Napoleonic Wars."
            ),
            "directOrInferred": "direct",
            "reviewStatus": "proposed",
            "visibility": "public",
            "evidenceLinkIds": ["evidence-claim-vienna-settlement-1"],
        },
        {
            "id": "claim-troppau-doctrine",
            "statement": (
                "The Troppau Protocol (19 November 1820) asserted that the great powers had the right "
                "to treat a state that had undergone a threatening revolutionary change of government as "
                "excluded from the European Alliance, implying a basis for collective intervention."
            ),
            "directOrInferred": "direct",
            "reviewStatus": "proposed",
            "visibility": "public",
            "evidenceLinkIds": ["evidence-claim-troppau-doctrine-1"],
        },
        {
            "id": "claim-naples-intervention",
            "statement": (
                "Austria's 1821 military intervention in Naples, authorized at the Congress of Laibach, "
                "was undertaken pursuant to the principle articulated in the Troppau Protocol."
            ),
            "directOrInferred": "inferred",
            "reviewStatus": "proposed",
            "visibility": "public",
            "evidenceLinkIds": ["evidence-claim-naples-intervention-1"],
        },
        {
            "id": "claim-castlereagh-dissent",
            "statement": (
                "Britain, under Castlereagh, rejected the Troppau Protocol's general claim of a right of "
                "intervention as inconsistent with the original, specific purpose of the Quadruple Alliance."
            ),
            "directOrInferred": "direct",
            "reviewStatus": "proposed",
            "visibility": "public",
            "evidenceLinkIds": ["evidence-claim-castlereagh-dissent-1"],
        },
        {
            "id": "claim-verona-spain",
            "statement": (
                "The Congress of Verona (1822) extended the same interventionist principle asserted at "
                "Troppau to authorize French military action in Spain, over continued British objection."
            ),
            "directOrInferred": "inferred",
            "reviewStatus": "proposed",
            "visibility": "public",
            "evidenceLinkIds": ["evidence-claim-verona-spain-1"],
        },
    ]

    new_links = [
        {"id": "evidence-claim-vienna-settlement-1", "targetType": "claim", "targetId": "claim-vienna-settlement", "passageId": VIENNA_PASSAGE_ID, "role": "supporting"},
        {"id": "evidence-claim-troppau-doctrine-1", "targetType": "claim", "targetId": "claim-troppau-doctrine", "passageId": TROPPAU_PASSAGE_ID, "role": "supporting"},
        {"id": "evidence-claim-naples-intervention-1", "targetType": "claim", "targetId": "claim-naples-intervention", "passageId": TROPPAU_PASSAGE_ID, "role": "supporting"},
        {"id": "evidence-claim-castlereagh-dissent-1", "targetType": "claim", "targetId": "claim-castlereagh-dissent", "passageId": CASTLEREAGH_PASSAGE_ID, "role": "supporting"},
        {
            "id": "evidence-claim-verona-spain-1",
            "targetType": "claim",
            "targetId": "claim-verona-spain",
            "passageId": TROPPAU_PASSAGE_ID,
            "role": "supporting",
            "reviewerNote": (
                "Supported only indirectly, via continuity with the Troppau doctrine — no dedicated "
                "Verona primary document was independently curated in this pass. See generationReport.omissions."
            ),
        },
    ]

    return {**data, "claims": claims, "evidenceLinks": [*data.get("evidenceLinks", []), *new_links]}
