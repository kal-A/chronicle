"""Python mirror of experiencePlan.test.ts — proves the optional
InvestigationExperiencePlan field validates the same way in both languages."""

import copy

import pytest

from chronicle.contracts import (
    GeneratedInvestigationValidationError,
    validate_generated_investigation,
)


def _base_package() -> dict:
    return {
        "schemaVersion": "1.0.0",
        "packageId": "investigation-test",
        "packageRevision": 1,
        "generatedAt": "2026-08-03T12:00:00.000Z",
        "request": {
            "id": "request-test",
            "rawInput": "Why did the test decision happen?",
            "requestType": "causal-investigation",
            "requestedDepth": "focused",
            "createdAt": "2026-08-03T11:00:00.000Z",
        },
        "scope": {
            "interpretedQuestion": "Why did the test decision happen?",
            "dateRange": {"precision": "range", "earliest": "1900-01-01", "latest": "1900-01-02"},
            "geographicScope": ["Test City"],
            "themes": ["diplomacy"],
            "inclusions": ["the decision"],
            "exclusions": ["later consequences"],
            "approvalStatus": "approved",
        },
        "status": "draft",
        "presentation": {
            "title": "A test investigation",
            "synthesis": [
                {
                    "id": "narrative-1",
                    "order": 0,
                    "text": "The surviving passage directly supports the decision claim.",
                    "isMaterialAssertion": True,
                    "referencedRecordIds": ["claim-1"],
                    "relatedEventId": "event-1",
                }
            ],
            "findings": [],
            "sceneIds": ["scene-1"],
            "perspectiveIds": [],
        },
        "entities": [
            {
                "id": "place-1",
                "entityType": "place",
                "canonicalName": "Test City",
                "reviewStatus": "reviewed",
                "coordinates": {"lat": 50, "lng": 10},
                "periodRecords": [
                    {
                        "periodLabel": "1900",
                        "nameAtTime": "Test City",
                        "controllingPolity": "Test Polity",
                        "precision": "city",
                    }
                ],
            }
        ],
        "events": [
            {
                "id": "event-1",
                "title": "A decision was recorded",
                "placeId": "place-1",
                "eventTime": {"precision": "exact", "earliest": "1900-01-01", "latest": "1900-01-01"},
                "evidenceLinkIds": ["evidence-event-1"],
                "relatedRecordIds": ["claim-1"],
                "reviewStatus": "reviewed",
                "visibility": "public",
            }
        ],
        "decisions": [],
        "communications": [],
        "knowledgeStates": [],
        "claims": [
            {
                "id": "claim-1",
                "statement": "The decision was recorded in the surviving document.",
                "directOrInferred": "direct",
                "reviewStatus": "reviewed",
                "visibility": "public",
                "evidenceLinkIds": ["evidence-claim-1"],
            }
        ],
        "relationships": [],
        "perspectives": [],
        "conflicts": [],
        "uncertainties": [],
        "researchGaps": [],
        "sources": [
            {
                "id": "source-1",
                "title": "Test source",
                "sourceType": "primary-official-diplomatic",
                "authorOrOrigin": "Test archive",
                "dateOfSource": {"precision": "exact", "earliest": "1900-01-01", "latest": "1900-01-01"},
                "originalLanguage": "English",
                "rightsStatus": "public-domain",
                "curationStatus": "reviewed",
                "knownLimitations": "Created only for contract testing.",
                "linkOrLocation": "test://source-1",
            }
        ],
        "documents": [
            {
                "id": "document-1",
                "sourceId": "source-1",
                "editionCitation": "Test edition, p. 1.",
                "visibility": "public",
                "knownLimitations": "Created only for contract testing.",
            }
        ],
        "passages": [
            {"id": "passage-1", "documentId": "document-1", "excerpt": "The decision was recorded.", "locator": "p. 1"}
        ],
        "evidenceLinks": [
            {"id": "evidence-claim-1", "targetType": "claim", "targetId": "claim-1", "passageId": "passage-1", "role": "supporting"},
            {"id": "evidence-event-1", "targetType": "event", "targetId": "event-1", "passageId": "passage-1", "role": "supporting"},
        ],
        "claimLedgers": [],
        "timeline": [{"id": "timeline-1", "eventId": "event-1", "order": 0}],
        "mapAssets": [],
        "mapScenes": [],
        "scenes": [
            {
                "id": "scene-1",
                "title": "The recorded decision",
                "curationStatus": "reviewed",
                "dateRange": {"precision": "range", "earliest": "1900-01-01", "latest": "1900-01-02"},
                "placeIds": ["place-1"],
                "entityIds": ["place-1"],
                "sourceIds": ["source-1"],
                "documentIds": ["document-1"],
                "passageIds": ["passage-1"],
                "eventIds": ["event-1"],
                "claimIds": ["claim-1"],
                "relationshipIds": [],
                "knowledgeStateIds": [],
                "narrativeBlockIds": ["narrative-1"],
            }
        ],
        "interactionSpec": {
            "defaultSceneId": "scene-1",
            "focusKinds": ["scene", "event", "entity", "claim", "relationship", "source", "passage", "timeRange"],
            "enabledFacets": ["narrative", "timeline", "map", "graph", "evidence"],
            "omittedCapabilities": [],
        },
        "generationReport": {
            "outcome": "complete",
            "stages": [{"id": "fixture-migration", "status": "passed"}],
            "omissions": [],
            "warnings": [],
            "verificationChecks": [{"id": "references", "status": "passed", "message": "All references resolve."}],
        },
    }


def _valid_experience_plan() -> dict:
    time_range = {"precision": "range", "earliest": "1900-01-01", "latest": "1900-01-02"}
    return {
        "opening": {
            "question": "Why did the test decision happen?",
            "scopeSummary": "One decision, one city, one day.",
            "leadAnswer": "The decision was recorded and is directly supported.",
            "evidenceCoverageSummary": "One primary source, fully cited.",
        },
        "workspace": {
            "initialMapScope": {
                "bounds": {
                    "topLeft": {"lat": 55, "lng": 5},
                    "topRight": {"lat": 55, "lng": 15},
                    "bottomRight": {"lat": 45, "lng": 15},
                    "bottomLeft": {"lat": 45, "lng": 5},
                },
                "focusRegions": [{"id": "region-test", "label": "Test Region"}],
                "contextRegions": [],
                "initialViewport": {"center": {"lat": 50, "lng": 10}, "zoom": 5},
                "minimumZoom": 2,
                "maximumZoom": 10,
                "geographicRationale": "Test City is the only location in this fixture.",
                "representedPeriod": time_range,
                "unavailableHistoricalBoundaries": [],
                "geographicLimitations": [],
            },
            "initialLensId": "lens-sequence",
            "initialTimeRange": time_range,
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
                "applicableTimeRange": time_range,
                "visibleLocations": ["place-1"],
                "visibleEvents": ["event-1"],
                "visibleRelationships": [],
                "visibleRegions": [],
                "legend": [],
                "evidenceReferences": ["evidence-claim-1"],
                "limitations": [],
                "textFallback": ["1. Test City -- A decision was recorded, 1 January 1900"],
            }
        ],
        "storySequences": [
            {
                "id": "story-1",
                "title": "The decision",
                "summary": "A single-step sequence.",
                "stepIds": ["event-1"],
                "defaultLensId": "lens-sequence",
                "defaultTimeRange": time_range,
            }
        ],
        "systemPaths": [
            {
                "id": "path-1",
                "title": "The decision path",
                "lensId": "lens-sequence",
                "nodeIds": ["claim-1"],
                "relationshipIds": [],
                "summary": "A single-node path.",
                "limitations": [],
            }
        ],
        "perspectiveComparisons": [],
        "contextualPrompts": [
            {
                "id": "prompts-no-selection",
                "appliesTo": "no-selection",
                "prompts": [{"id": "prompt-1", "text": "What is the main conclusion?", "targetLensId": "lens-sequence"}],
            }
        ],
        "recommendedSelections": [
            {"id": "selection-1", "kind": "event", "recordId": "event-1", "label": "A decision was recorded"}
        ],
        "limitations": [
            {"id": "limitation-1", "summary": "Only one source is curated.", "affectedLensIds": ["lens-sequence"]}
        ],
        "inspector": {"defaultEvidenceDepth": "standard", "exposeGenerationReport": True, "exposeRejectedSources": False},
    }


def test_accepts_a_package_with_a_valid_experience_plan():
    package = _base_package()
    package["experiencePlan"] = _valid_experience_plan()
    result = validate_generated_investigation(package)
    assert result.experiencePlan is not None
    assert result.experiencePlan.lenses[0].id == "lens-sequence"


def test_accepts_a_package_with_no_experience_plan(golden_investigation):
    result = validate_generated_investigation(golden_investigation)
    assert result.experiencePlan is None


@pytest.mark.parametrize(
    "mutate,message_fragment",
    [
        (lambda plan: plan["lenses"][0].__setitem__("visibleLocations", ["place-missing"]), "unknown Place"),
        (lambda plan: plan["workspace"].__setitem__("initialLensId", "lens-missing"), "unknown InvestigationLens"),
        (lambda plan: plan["storySequences"][0].__setitem__("stepIds", ["event-missing"]), "unknown Event"),
        (lambda plan: plan["systemPaths"][0].__setitem__("nodeIds", ["record-missing"]), "unknown record"),
        (
            lambda plan: plan["contextualPrompts"][0]["prompts"][0].__setitem__("targetLensId", "lens-missing"),
            "unknown InvestigationLens",
        ),
        (lambda plan: plan["limitations"][0].__setitem__("affectedLensIds", ["lens-missing"]), "unknown InvestigationLens"),
    ],
)
def test_rejects_broken_experience_plan_references(mutate, message_fragment):
    package = _base_package()
    plan = _valid_experience_plan()
    mutate(plan)
    package["experiencePlan"] = plan

    with pytest.raises(GeneratedInvestigationValidationError) as excinfo:
        validate_generated_investigation(package)
    assert message_fragment in str(excinfo.value)


def test_rejects_lens_id_colliding_with_an_existing_package_id():
    package = _base_package()
    plan = _valid_experience_plan()
    plan["lenses"][0]["id"] = "claim-1"
    package["experiencePlan"] = plan

    with pytest.raises(GeneratedInvestigationValidationError, match="not unique"):
        validate_generated_investigation(package)


def test_golden_fixture_with_added_experience_plan_still_validates(golden_investigation):
    package = copy.deepcopy(golden_investigation)
    time_range = {"precision": "range", "earliest": "1914-07-05", "latest": "1914-07-06"}
    package["experiencePlan"] = {
        "opening": {
            "question": "What did the blank cheque promise?",
            "scopeSummary": "The 5-6 July 1914 assurance and its reception in Vienna.",
            "leadAnswer": "Germany assured Austria-Hungary of full support.",
            "evidenceCoverageSummary": "Multiple primary diplomatic sources.",
        },
        "workspace": {
            "initialMapScope": {
                "bounds": {
                    "topLeft": {"lat": 55, "lng": 5},
                    "topRight": {"lat": 55, "lng": 20},
                    "bottomRight": {"lat": 45, "lng": 20},
                    "bottomLeft": {"lat": 45, "lng": 5},
                },
                "focusRegions": [{"id": "region-central-europe", "label": "Central Europe"}],
                "contextRegions": [],
                "initialViewport": {"center": {"lat": 50, "lng": 14}, "zoom": 5},
                "minimumZoom": 3,
                "maximumZoom": 10,
                "geographicRationale": "Berlin and Vienna are the two active locations.",
                "representedPeriod": time_range,
                "unavailableHistoricalBoundaries": [],
                "geographicLimitations": [],
            },
            "initialLensId": "lens-sequence",
            "initialTimeRange": time_range,
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
                "applicableTimeRange": time_range,
                "visibleLocations": ["place-berlin", "place-vienna"],
                "visibleEvents": ["event-1-assurance-given"],
                "visibleRelationships": [],
                "visibleRegions": [],
                "legend": [],
                "evidenceReferences": ["evidence-claim-c1-assurance-reported-1"],
                "limitations": [],
                "textFallback": ["1. Berlin -- assurance given, 5 July 1914"],
            }
        ],
        "storySequences": [],
        "systemPaths": [],
        "perspectiveComparisons": [],
        "contextualPrompts": [],
        "recommendedSelections": [],
        "limitations": [],
        "inspector": {"defaultEvidenceDepth": "standard", "exposeGenerationReport": True, "exposeRejectedSources": False},
    }

    result = validate_generated_investigation(package)
    assert result.experiencePlan is not None
