"""InvestigationExperiencePlan stage (Phase D0.4) for the Concert of Europe
curated package — deterministic content over the same real facts
composition.py/relationships.py/timeline.py already curated, exercised
through the same StageFn contract as every other stage here. Replaces the
hand-authored plan D0.3 attached to this package purely in the frontend
fixture registry (src/content/investigationFixtures.ts), proving
InvestigationExperiencePlan is generated data, not React branching — the
same proof C3 established for the base package (plans/current-phase.md).

Field-for-field mirror of the plan D0.3 hand-authored: three lenses
(Sequence, Systems, Uncertainty), one story sequence (Troppau to Naples),
one system path (the intervention doctrine), one perspective comparison
(Metternich vs. Castlereagh). No new historical research — only new
*presentation* data over facts already curated and cited.
"""

VIENNA_SCENE_ID = "scene-congress-of-vienna"
INTERVENTION_SCENE_ID = "scene-principle-of-intervention"


def attach_experience_plan(data: dict) -> dict:
    plan = {
        "opening": {
            "question": "How did the Concert of Europe respond to revolutionary movements?",
            "scopeSummary": "Vienna, Troppau, Laibach, Naples, and Verona, 1814-1822.",
            "leadAnswer": (
                "The intervention principle moved from declaration at Troppau to practical "
                "application at Laibach and Naples, while Britain rejected its use as a general "
                "licence to police revolutions. Its later extension through Verona is less directly "
                "supported in the current corpus."
            ),
            "evidenceCoverageSummary": "Three primary diplomatic sources, with two disclosed sourcing gaps.",
        },
        "workspace": {
            "initialMapScope": {
                "bounds": {
                    "topLeft": {"lat": 60, "lng": -2},
                    "topRight": {"lat": 60, "lng": 27},
                    "bottomRight": {"lat": 36, "lng": 27},
                    "bottomLeft": {"lat": 36, "lng": -2},
                },
                "focusRegions": [{"id": "region-central-europe", "label": "Central Europe"}],
                "contextRegions": [{"id": "region-southern-europe", "label": "Southern Europe"}],
                "initialViewport": {"center": {"lat": 48.2082, "lng": 16.3738}, "zoom": 4},
                "minimumZoom": 3,
                "maximumZoom": 8,
                "geographicRationale": "Vienna, Troppau, Laibach, Naples, and Verona are the five active locations.",
                "representedPeriod": {"precision": "range", "earliest": "1814-09-18", "latest": "1822-12-14"},
                "unavailableHistoricalBoundaries": [],
                "geographicLimitations": [
                    "The only curated period map (Shepherd, 1815) is scoped to the Vienna scene only — "
                    "see docs/research/concert-of-europe-map-source.md.",
                ],
            },
            "initialLensId": "lens-sequence",
            "initialTimeRange": {"precision": "range", "earliest": "1814-09-18", "latest": "1822-12-14"},
            "initialPanelTab": "explore",
            "defaultPanelWidth": 380,
        },
        "lenses": [
            {
                "id": "lens-sequence",
                "label": "Sequence",
                "purpose": "Show what happened, where, and in what order.",
                "historicalQuestion": "What happened, where, and in what order?",
                "visualizationType": "map",
                "applicableTimeRange": {"precision": "range", "earliest": "1814-09-18", "latest": "1822-12-14"},
                "visibleLocations": ["place-vienna", "place-troppau", "place-laibach", "place-naples", "place-verona"],
                "visibleEvents": [
                    "event-congress-of-vienna",
                    "event-troppau-protocol",
                    "event-laibach-authorization",
                    "event-naples-intervention",
                    "event-congress-of-verona",
                ],
                "visibleRelationships": [],
                "visibleRegions": [],
                "legend": [],
                "evidenceReferences": ["evidence-event-vienna-1"],
                "limitations": [],
                "textFallback": [
                    "1. Vienna — Congress of Vienna, 18 September 1814 to 9 June 1815",
                    "2. Troppau — Troppau Protocol signed, 19 November 1820",
                    "3. Laibach — Austrian intervention in Naples authorized, early 1821",
                    "4. Naples — Austrian forces suppress the constitutional government, March 1821",
                    "5. Verona — French intervention in Spain authorized, 20 October to 14 December 1822",
                ],
            },
            {
                "id": "lens-systems",
                "label": "Systems",
                "purpose": (
                    "Show the mechanism connecting Troppau's doctrine to Naples, Britain's dissent, "
                    "and its weaker extension to Verona."
                ),
                "historicalQuestion": "What mechanisms and relationships connected the selected events?",
                "visualizationType": "graph",
                "applicableTimeRange": {"precision": "range", "earliest": "1820-11-19", "latest": "1822-12-14"},
                "visibleLocations": [],
                "visibleEvents": [],
                "visibleRelationships": [
                    "rel-troppau-supports-naples",
                    "rel-castlereagh-disputes-troppau",
                    "rel-verona-extends-troppau",
                ],
                "visibleRegions": [],
                "legend": [],
                "evidenceReferences": ["evidence-claim-troppau-doctrine-1"],
                "limitations": [
                    "The Verona extension is supported only indirectly, via continuity with the Troppau doctrine.",
                ],
                "textFallback": [
                    "Troppau doctrine — establishes the doctrine invoked by — Naples intervention",
                    "Castlereagh's dissent — disputes — Troppau doctrine",
                    "Verona/Spain — extends (indirectly supported) — Troppau doctrine",
                ],
            },
            {
                "id": "lens-uncertainty",
                "label": "Uncertainty",
                "purpose": "Show which parts of this investigation remain weak, approximate, or unsupported.",
                "historicalQuestion": "Which parts remain weak, approximate, disputed, or unsupported?",
                "visualizationType": "map",
                "applicableTimeRange": {"precision": "range", "earliest": "1822-10-20", "latest": "1822-12-14"},
                "visibleLocations": ["place-verona"],
                "visibleEvents": ["event-congress-of-verona"],
                "visibleRelationships": ["rel-verona-extends-troppau"],
                "visibleRegions": [],
                "legend": [],
                "evidenceReferences": [],
                "limitations": [
                    "No dedicated Congress of Verona primary document was independently curated in this pass.",
                    "No period-accurate map is attached to this scene — the only curated plate documents the "
                    "1815 Vienna settlement.",
                ],
                "textFallback": [
                    "Weak: the Verona/Spain claim rests on continuity with Troppau, not a dedicated Verona source.",
                    "Absent: no period map for 1820-1822 — disclosed, not hidden.",
                ],
            },
        ],
        "storySequences": [
            {
                "id": "story-troppau-to-naples",
                "title": "From doctrine to intervention",
                "summary": "The Troppau Protocol, its authorization at Laibach, and its execution in Naples.",
                "stepIds": ["event-troppau-protocol", "event-laibach-authorization", "event-naples-intervention"],
                "defaultLensId": "lens-sequence",
                "defaultTimeRange": {"precision": "range", "earliest": "1820-11-19", "latest": "1821-03-24"},
            },
        ],
        "systemPaths": [
            {
                "id": "path-intervention-doctrine",
                "title": "The intervention doctrine",
                "lensId": "lens-systems",
                "nodeIds": [
                    "claim-troppau-doctrine",
                    "claim-naples-intervention",
                    "claim-castlereagh-dissent",
                    "claim-verona-spain",
                ],
                "relationshipIds": [
                    "rel-troppau-supports-naples",
                    "rel-castlereagh-disputes-troppau",
                    "rel-verona-extends-troppau",
                ],
                "summary": (
                    "Troppau establishes the doctrine invoked at Naples; Britain disputes it; Verona "
                    "extends it with weaker support."
                ),
                "limitations": ["The Verona edge is indirectly supported only."],
            },
        ],
        "perspectiveComparisons": [
            {
                "id": "comparison-metternich-castlereagh",
                "title": "Metternich vs. Castlereagh on intervention",
                "entityIds": ["person-metternich", "person-castlereagh"],
                "claimIds": ["claim-troppau-doctrine", "claim-castlereagh-dissent"],
                "summary": (
                    "Austria asserted a general right of intervention; Britain rejected it as unmoored "
                    "from the 1815 Alliance's original purpose."
                ),
            },
        ],
        "contextualPrompts": [],
        "recommendedSelections": [],
        "limitations": [],
        "inspector": {
            "defaultEvidenceDepth": "standard",
            "exposeGenerationReport": True,
            "exposeRejectedSources": False,
        },
    }

    package = {**data["package"], "experiencePlan": plan}
    return {**data, "package": package}
