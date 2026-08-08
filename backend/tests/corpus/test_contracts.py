from datetime import date
import json
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from chronicle.corpus.contracts import (
    DEFAULT_RESULT_COUNT,
    MAX_RESULT_COUNT,
    DateRangeFilter,
    EvidenceLinkProjection,
    PassageDateRole,
    PassageSearchRequest,
)
from chronicle.corpus.projections import project_evidence_link


def test_date_range_requires_at_least_one_bound():
    with pytest.raises(ValidationError):
        DateRangeFilter()


def test_date_range_rejects_reversed_bounds():
    with pytest.raises(ValidationError):
        DateRangeFilter(earliest=date(1914, 7, 2), latest=date(1914, 7, 1))


def test_search_rejects_whitespace_only_query():
    with pytest.raises(ValidationError):
        PassageSearchRequest(corpusId="corpus-a", query="   ")


@pytest.mark.parametrize("query", ["!!!", "---", "___"])
def test_search_rejects_queries_without_a_word_or_number(query):
    with pytest.raises(ValidationError):
        PassageSearchRequest(corpusId="corpus-a", query=query)


def test_search_date_filter_requires_explicit_time_roles():
    with pytest.raises(ValidationError):
        PassageSearchRequest(
            corpusId="corpus-a",
            query="dispatch",
            dateRange=DateRangeFilter(earliest=date(1914, 7, 1)),
        )


def test_search_rejects_time_roles_without_a_date_filter():
    with pytest.raises(ValidationError):
        PassageSearchRequest(
            corpusId="corpus-a",
            query="dispatch",
            dateRoles=[PassageDateRole.SENT_TIME],
        )


def test_search_has_qwen_safe_default_and_hard_limit():
    request = PassageSearchRequest(corpusId="corpus-a", query="dispatch")
    assert request.maxResults == DEFAULT_RESULT_COUNT == 8
    assert MAX_RESULT_COUNT == 20
    with pytest.raises(ValidationError):
        PassageSearchRequest(corpusId="corpus-a", query="dispatch", maxResults=21)


def test_search_schema_advertises_legal_evidence_and_source_enums():
    rendered_schema = json.dumps(PassageSearchRequest.model_json_schema())
    assert "supporting" in rendered_schema
    assert "counterevidence" in rendered_schema
    assert "primary-official-diplomatic" in rendered_schema


def test_evidence_link_projection_keeps_role_attached_to_target_and_scope():
    projection = EvidenceLinkProjection(
        evidenceLinkId="evidence-1",
        targetType="relationship",
        targetId="relationship-c",
        role="counterevidence",
        reviewerNote="Qualifies the relationship.",
        reviewStatus="proposed",
        visibility="public",
        passageId="passage-1",
        documentId="document-1",
        sourceId="source-1",
    )

    assert projection.role == "counterevidence"
    assert projection.targetId == "relationship-c"
    assert projection.reviewStatus == "proposed"


def test_canonical_projection_builder_derives_target_qualification_and_scope():
    value = lambda text: SimpleNamespace(value=text)  # noqa: E731 - compact enum stand-in
    projection = project_evidence_link(
        link=SimpleNamespace(
            id="evidence-1",
            targetType=value("relationship"),
            targetId="relationship-c",
            role=value("counterevidence"),
            reviewerNote="Disputes the causal reading.",
        ),
        passage=SimpleNamespace(id="passage-1"),
        document=SimpleNamespace(id="document-1", sourceId="source-1"),
        source=SimpleNamespace(id="source-1"),
        target=SimpleNamespace(reviewStatus=value("disputed"), visibility=value("public")),
    )

    assert projection.targetId == "relationship-c"
    assert projection.role == "counterevidence"
    assert projection.reviewStatus == "disputed"
    assert projection.sourceId == "source-1"
