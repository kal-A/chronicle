"""Investigation composer for the Concert of Europe curated package —
same role as providers/mock/composition.py, but assembling two real,
evidence-backed scenes instead of one generic placeholder scene, and
disclosing two genuine, researched gaps (no period map for 1820-1822; no
dedicated Verona primary document) rather than a single contrived one.
"""

from ....contracts.generated_investigation import SUPPORTED_GENERATED_INVESTIGATION_VERSION
from ...util import SENTINEL_DATETIME

CURATED_CONTENT_NOTE = (
    "This package is real, hand-researched content curated for Phase C3 — unlike Phase C2's mock "
    "packages, it is not synthetic, but it is a prototype curation pass (see each Source's "
    "knownLimitations and this report's omissions), not independently peer-reviewed scholarship."
)

VIENNA_SCENE_ID = "scene-congress-of-vienna"
INTERVENTION_SCENE_ID = "scene-principle-of-intervention"


def compose_investigation(data: dict) -> dict:
    vienna_source_ids = ["source-vienna-final-act"]
    intervention_source_ids = ["source-troppau-protocol", "source-castlereagh-state-paper"]

    narrative_vienna = {
        "id": "narrative-vienna-settlement",
        "order": 0,
        "text": (
            "Between September 1814 and June 1815, the victorious powers of the Napoleonic Wars "
            "assembled at Vienna and, on 9 June 1815, signed a General Treaty redrawing the map of "
            "Europe -- redistributing territory among Prussia, Russia, and Austria and reorganizing "
            "the German states into a new Confederation. This settlement created the diplomatic "
            "framework -- the 'Concert of Europe' -- within which the later congresses at Troppau, "
            "Laibach, and Verona operated."
        ),
        "isMaterialAssertion": True,
        "referencedRecordIds": ["claim-vienna-settlement"],
        "relatedEventId": "event-congress-of-vienna",
    }

    narrative_troppau = {
        "id": "narrative-troppau-doctrine",
        "order": 1,
        "text": (
            "In November 1820, meeting at Troppau, Austria, Prussia, and Russia signed a Protocol "
            "asserting that a state whose government changed through revolution in a way that "
            "threatened other states thereby excluded itself from the European Alliance -- a "
            "principle that, months later at Laibach, the same powers invoked to authorize Austrian "
            "military intervention against the constitutional government in Naples. Britain, under "
            "Castlereagh, rejected the Protocol's general claim: the 1815 Alliance, Castlereagh "
            "argued, had been formed against a specific defeated enemy, not as a standing license to "
            "police other states' internal arrangements."
        ),
        "isMaterialAssertion": True,
        "referencedRecordIds": [
            "claim-troppau-doctrine",
            "claim-naples-intervention",
            "claim-castlereagh-dissent",
            "rel-troppau-supports-naples",
            "rel-castlereagh-disputes-troppau",
        ],
        "relatedEventId": "event-troppau-protocol",
    }

    narrative_verona = {
        "id": "narrative-verona-spain",
        "order": 2,
        "text": (
            "At Verona in the autumn of 1822 -- the last of the Congresses, and the first without "
            "Castlereagh, who had died that August -- the same interventionist principle was extended "
            "to authorize French military action against the revolutionary government in Spain, over "
            "the continued objection of Britain's new Foreign Secretary, George Canning. This claim's "
            "evidentiary support is weaker than the others in this package: no dedicated Verona primary "
            "document was independently curated in this pass, so it rests on continuity with the "
            "Troppau doctrine rather than direct Verona-specific evidence -- an explicit, disclosed gap."
        ),
        "isMaterialAssertion": True,
        "referencedRecordIds": ["claim-verona-spain", "rel-verona-extends-troppau"],
        "relatedEventId": "event-congress-of-verona",
    }

    ledger_troppau = {
        "id": "ledger-claim-troppau-doctrine",
        "claimId": "claim-troppau-doctrine",
        "evidenceLinkIds": ["evidence-claim-troppau-doctrine-1"],
        "conclusion": "supported",
        "limitations": [
            "Cited via secondary reprints corroborating consistent wording of the Protocol's key "
            "clause; a directly hosted, independently verified full primary-text transcription was "
            "not located in this curation pass."
        ],
    }

    findings = [
        {
            "id": "finding-troppau-doctrine",
            "recordType": "claim",
            "recordId": "claim-troppau-doctrine",
            "label": "The Troppau Protocol asserted a right to treat revolutionary states as excluded from the European Alliance.",
            "importance": "major",
        },
        {
            "id": "finding-castlereagh-dissent",
            "recordType": "claim",
            "recordId": "claim-castlereagh-dissent",
            "label": "Britain rejected the Protocol's general claim of a right of intervention.",
            "importance": "supporting",
        },
        {
            "id": "finding-castlereagh-disputes-troppau",
            "recordType": "relationship",
            "recordId": "rel-castlereagh-disputes-troppau",
            "label": "Britain's dissent directly disputed the Troppau doctrine, evidenced on both sides.",
            "importance": "supporting",
        },
    ]

    vienna_scene = {
        "id": VIENNA_SCENE_ID,
        "title": "The Congress System Established, 1814-1815",
        "curationStatus": "prototype-curated",
        "dateRange": {
            "precision": "range",
            "earliest": "1814-09-18",
            "latest": "1815-06-09",
            "label": "The Congress of Vienna",
        },
        "placeIds": ["place-vienna"],
        "entityIds": ["place-vienna", "person-metternich", "person-alexander-i", "person-castlereagh"],
        "sourceIds": vienna_source_ids,
        "documentIds": [f"document-{sid.removeprefix('source-')}" for sid in vienna_source_ids],
        "passageIds": ["passage-vienna-final-act-1"],
        "eventIds": ["event-congress-of-vienna"],
        "claimIds": ["claim-vienna-settlement"],
        "relationshipIds": [],
        "knowledgeStateIds": [],
        "narrativeBlockIds": [narrative_vienna["id"]],
        "mapSceneId": "map-scene-vienna",
    }

    intervention_scene = {
        "id": INTERVENTION_SCENE_ID,
        "title": "The Principle of Intervention, 1820-1822",
        "curationStatus": "prototype-curated",
        "dateRange": {
            "precision": "range",
            "earliest": "1820-11-19",
            "latest": "1822-12-14",
            "label": "Troppau to Verona",
        },
        "placeIds": ["place-troppau", "place-laibach", "place-naples", "place-verona"],
        "entityIds": [
            "place-troppau",
            "place-laibach",
            "place-naples",
            "place-verona",
            "person-metternich",
            "person-alexander-i",
            "person-castlereagh",
            "person-canning",
        ],
        "sourceIds": intervention_source_ids,
        "documentIds": [f"document-{sid.removeprefix('source-')}" for sid in intervention_source_ids],
        "passageIds": ["passage-troppau-protocol-1", "passage-castlereagh-state-paper-1"],
        "eventIds": [
            "event-troppau-protocol",
            "event-laibach-authorization",
            "event-naples-intervention",
            "event-congress-of-verona",
        ],
        "claimIds": ["claim-troppau-doctrine", "claim-naples-intervention", "claim-castlereagh-dissent", "claim-verona-spain"],
        "relationshipIds": ["rel-troppau-supports-naples", "rel-castlereagh-disputes-troppau", "rel-verona-extends-troppau"],
        "knowledgeStateIds": [],
        "narrativeBlockIds": [narrative_troppau["id"], narrative_verona["id"]],
        "mapSceneId": None,
    }

    package = {
        "schemaVersion": SUPPORTED_GENERATED_INVESTIGATION_VERSION,
        "packageId": "concert-of-europe-1814-1822",
        "packageRevision": 1,
        "generatedAt": SENTINEL_DATETIME,
        "request": {
            "id": "request-concert-of-europe",
            "rawInput": data["topic"],
            "requestType": "causal-investigation",
            "requestedDepth": "standard",
            "createdAt": SENTINEL_DATETIME,
        },
        "scope": data["scope"],
        "status": "partial",
        "presentation": {
            "title": "The Concert of Europe and Revolutionary Intervention, 1814-1822",
            "synthesis": [narrative_vienna, narrative_troppau, narrative_verona],
            "findings": findings,
            "sceneIds": [VIENNA_SCENE_ID, INTERVENTION_SCENE_ID],
            "perspectiveIds": [],
        },
        "entities": data["entities"],
        "events": data["events"],
        "decisions": [],
        "communications": [],
        "knowledgeStates": [],
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
        "claimLedgers": [ledger_troppau],
        "timeline": data["timeline"],
        "mapAssets": data["mapAssets"],
        "mapScenes": data["mapScenes"],
        "scenes": [vienna_scene, intervention_scene],
        "interactionSpec": {
            "defaultSceneId": VIENNA_SCENE_ID,
            "focusKinds": ["scene", "event", "entity", "claim", "relationship", "source", "passage", "timeRange"],
            "enabledFacets": ["narrative", "timeline", "map", "graph", "evidence"],
            "omittedCapabilities": ["period map for the 1820-1822 scene"],
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
                "No period-accurate map is attached to the 1820-1822 scene: the only rights-cleared "
                "period map curated for this package (Shepherd's 1911 atlas, 'Treaty Adjustments, "
                "1814, 1815') documents the 1815 Vienna settlement, not the Troppau/Laibach/Verona-era "
                "situation five to seven years later, and reusing it there would misrepresent period fit.",
                "No dedicated primary document for the Congress of Verona's Spain decision was "
                "independently located and curated in this pass; claim-verona-spain and "
                "rel-verona-extends-troppau are supported only indirectly, via continuity with the "
                "Troppau Protocol.",
                "The Troppau Protocol and Castlereagh's State Paper are cited via secondary reprints "
                "and paraphrase respectively, not independently verified primary-text transcriptions "
                "(see each Source's knownLimitations).",
            ],
            "warnings": [CURATED_CONTENT_NOTE],
            "verificationChecks": [],
        },
    }

    return {**data, "package": package}
