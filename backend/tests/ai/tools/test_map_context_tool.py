"""get_map_context preserves stored geography while bounding model-facing output."""

from __future__ import annotations

import pytest

from chronicle.ai.tools.contracts import ToolExecutionContext
from chronicle.ai.tools.errors import (
    CorpusRetrievalError,
    MalformedToolInputError,
    ResultLimitExceededError,
)


EXPECTED_TOTALS = {
    "blank-cheque-golden": 3,
    "concert-of-europe-1814-1822": 6,
}


def _invoke_map(tool_registry, corpus, corpus_id, context, **tool_input):
    return tool_registry.invoke(
        "get_map_context",
        {"corpusId": corpus_id, **tool_input},
        context,
        corpus,
    )[0]


def test_no_filter_returns_every_place_and_scene_with_exact_counts(
    tool_registry, corpus, corpus_id, context
):
    output = _invoke_map(
        tool_registry,
        corpus,
        corpus_id,
        context,
        maxResults=EXPECTED_TOTALS[corpus_id],
    )

    assert output.totalCount == EXPECTED_TOTALS[corpus_id]
    assert output.returnedCount == EXPECTED_TOTALS[corpus_id]
    assert output.truncated is False
    assert len(output.places) + len(output.mapScenes) == EXPECTED_TOTALS[corpus_id]


def test_map_context_true_truncation_is_explicit(tool_registry, corpus, corpus_id, context):
    output = _invoke_map(tool_registry, corpus, corpus_id, context, maxResults=1)

    assert output.totalCount == EXPECTED_TOTALS[corpus_id]
    assert output.returnedCount == 1
    assert output.truncated is True


def test_map_context_exactly_at_limit_is_not_truncated(tool_registry, corpus, corpus_id, context):
    total = EXPECTED_TOTALS[corpus_id]
    output = _invoke_map(tool_registry, corpus, corpus_id, context, maxResults=total)

    assert output.returnedCount == total
    assert output.totalCount == total
    assert output.truncated is False


def test_map_context_respects_context_maximum_results(tool_registry, corpus, corpus_id):
    context = ToolExecutionContext(corpusId=corpus_id, maximumResults=1)
    with pytest.raises(ResultLimitExceededError):
        _invoke_map(tool_registry, corpus, corpus_id, context, maxResults=2)


@pytest.mark.parametrize("field_name", ["placeIds", "eventIds", "sceneIds"])
def test_map_context_bounds_every_input_id_list(tool_registry, corpus, corpus_id, context, field_name):
    with pytest.raises(MalformedToolInputError):
        _invoke_map(
            tool_registry,
            corpus,
            corpus_id,
            context,
            **{field_name: ["repeated-id"] * 51},
        )


def test_place_filter_preserves_exact_coordinates_and_period_records(
    tool_registry, corpus, corpus_id, context
):
    place = next(entity for entity in corpus.get_investigation().entities if entity.entityType == "place")
    output = _invoke_map(
        tool_registry,
        corpus,
        corpus_id,
        context,
        placeIds=[place.id],
        maxResults=8,
    )
    entry = output.places[0]

    assert entry.placeId == place.id
    assert (
        entry.coordinates.model_dump(mode="json") if entry.coordinates is not None else None
    ) == (place.coordinates.model_dump(mode="json") if place.coordinates is not None else None)
    assert [record.model_dump(mode="json") for record in entry.periodRecords] == [
        {
            "periodLabel": stored.periodLabel,
            "nameAtTime": stored.nameAtTime,
            "controllingPolity": stored.controllingPolity,
            "precision": stored.precision.value,
        }
        for stored in place.periodRecords
    ]


def test_map_scene_preserves_marker_precision_and_asset_georeferencing(
    tool_registry, corpus, corpus_id, context
):
    investigation = corpus.get_investigation()
    stored_scene = investigation.mapScenes[0]
    stored_asset = next(asset for asset in investigation.mapAssets if asset.id == stored_scene.mapAssetId)
    output = _invoke_map(
        tool_registry,
        corpus,
        corpus_id,
        context,
        sceneIds=[stored_scene.sceneId],
        maxResults=8,
    )
    scene = output.mapScenes[0]

    assert [marker.model_dump(mode="json") for marker in scene.markers] == [
        {"placeId": marker.placeId, "precision": marker.precision.value}
        for marker in stored_scene.markers
    ]
    assert scene.georeferencingNote == stored_asset.georeferencingNote
    assert scene.periodFitDecision == stored_asset.periodFitDecision.value
    assert scene.georeferencingPrecision == stored_asset.georeferencingPrecision.value
    assert scene.sourceCitation == stored_asset.sourceCitation
    assert scene.attribution == stored_asset.attribution
    assert scene.license == stored_asset.license
    assert scene.bounds == stored_asset.bounds
    assert scene.defaultView == stored_asset.defaultView


def test_explicit_scene_filter_prioritizes_the_requested_scene_under_a_tight_cap(
    tool_registry, corpus, corpus_id
):
    stored_scene = corpus.get_investigation().mapScenes[0]
    output = _invoke_map(
        tool_registry,
        corpus,
        corpus_id,
        ToolExecutionContext(corpusId=corpus_id, maximumResults=1),
        sceneIds=[stored_scene.sceneId],
        maxResults=1,
    )
    assert [scene.mapSceneId for scene in output.mapScenes] == [stored_scene.id]


def test_map_context_uses_one_global_nested_collection_budget(
    tool_registry, corpus, corpus_id
):
    context = ToolExecutionContext(corpusId=corpus_id, maximumResults=1)
    output = _invoke_map(tool_registry, corpus, corpus_id, context, maxResults=1)

    nested_count = (
        sum(len(place.periodRecords) + len(place.linkedEventIds) for place in output.places)
        + sum(len(scene.markers) for scene in output.mapScenes)
        + len(output.geographicLimitations)
        + len(output.unavailableHistoricalBoundaries)
    )
    assert nested_count <= 1


def test_map_context_preserves_full_represented_period_and_boundary_limitations(
    tool_registry, corpus, corpus_id, context
):
    investigation = corpus.get_investigation()
    output = _invoke_map(
        tool_registry,
        corpus,
        corpus_id,
        context,
        maxResults=EXPECTED_TOTALS[corpus_id],
    )

    if investigation.experiencePlan is None:
        assert output.representedPeriod is None
        assert output.geographicLimitations == []
        assert output.unavailableHistoricalBoundaries == []
    else:
        scope = investigation.experiencePlan.workspace.initialMapScope
        assert output.representedPeriod.model_dump(mode="json") == scope.representedPeriod.model_dump(mode="json")
        assert output.geographicLimitations == scope.geographicLimitations
        assert output.unavailableHistoricalBoundaries == scope.unavailableHistoricalBoundaries


def test_event_filter_resolves_to_stored_event_place(tool_registry, corpus, corpus_id, context):
    event = corpus.get_investigation().events[0]
    output = _invoke_map(
        tool_registry,
        corpus,
        corpus_id,
        context,
        eventIds=[event.id],
        maxResults=8,
    )
    assert event.placeId in {place.placeId for place in output.places}


def test_unknown_place_raises(tool_registry, corpus, corpus_id, context):
    with pytest.raises(CorpusRetrievalError):
        _invoke_map(
            tool_registry,
            corpus,
            corpus_id,
            context,
            placeIds=["no-such-place"],
        )


def test_unknown_scene_raises(tool_registry, corpus, corpus_id, context):
    with pytest.raises(CorpusRetrievalError):
        _invoke_map(
            tool_registry,
            corpus,
            corpus_id,
            context,
            sceneIds=["no-such-scene"],
        )


def test_map_tool_spec_explains_when_not_to_use_it(tool_registry):
    definition = tool_registry.get("get_map_context")
    assert "stored places" in definition.use_when
    assert "infer" in definition.avoid_when
    assert "marker precision" in definition.output_summary
