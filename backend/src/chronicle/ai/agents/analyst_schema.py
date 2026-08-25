"""Retrieval-constrained JSON Schema for Evidence Analyst generation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable

from ..contracts.analysis import AnalysisDraft, StatementKind
from ..contracts.retrieval import RetrievalBundle


def build_analyst_response_schema(bundle: RetrievalBundle) -> dict[str, Any]:
    """Constrain Qwen to legal statement fields and retrieved citations."""

    schema = deepcopy(AnalysisDraft.model_json_schema())
    properties = schema["properties"]
    schema["required"] = list(properties)
    properties["analysisVersion"] = {"const": "e3-analyst-v1", "type": "string"}
    properties["runId"] = {"const": bundle.runId, "type": "string"}
    properties["planId"] = {"const": bundle.planId, "type": "string"}
    properties["corpusId"] = {"const": bundle.corpusId, "type": "string"}

    status_schema = schema["$defs"]["AnswerStatus"]
    status_schema["enum"] = [
        value for value in status_schema["enum"] if value != "needs_more_retrieval"
    ]
    properties["suggestedFollowUpToolCall"] = {"type": "null"}

    citations = _citation_variants(bundle)
    schema["$defs"]["AnalysisCitation"] = (
        {"oneOf": citations} if citations else {"not": {}}
    )
    if not citations:
        properties["status"] = {"const": "abstained", "type": "string"}
        properties["statements"]["maxItems"] = 0
        properties["abstentionReason"] = {
            "minLength": 1,
            "maxLength": 800,
            "type": "string",
        }

    base_statement = schema["$defs"]["AnalysisStatement"]
    constraints = _retrieved_constraints(bundle)
    statement_variants = [
        _statement_variant(base_statement, kind, constraints)
        for kind in StatementKind
    ]
    schema["$defs"]["AnalysisStatement"] = {"oneOf": statement_variants}
    return _strip_generation_annotations(schema)


def _statement_variant(
    base: dict[str, Any],
    kind: StatementKind,
    constraints: dict[str, set[str]],
) -> dict[str, Any]:
    properties = deepcopy(base["properties"])
    properties["statementKind"] = {"const": kind.value, "type": "string"}
    properties["knowledgeAwareness"] = (
        {"$ref": "#/$defs/Awareness"}
        if kind is StatementKind.KNOWLEDGE
        else {"type": "null"}
    )
    properties["evidenceClassification"] = _optional_retrieved_enum(
        constraints["classifications"]
    )
    properties["geographicPrecision"] = _optional_retrieved_enum(
        constraints["precisions"]
    )
    properties["requiresHumanReview"] = {"const": True, "type": "boolean"}
    temporal_roles = properties["temporalRoles"]
    if constraints["temporalRoles"]:
        temporal_roles["items"] = {
            "enum": sorted(constraints["temporalRoles"]),
            "type": "string",
        }
        temporal_roles["maxItems"] = min(
            temporal_roles.get("maxItems", 5),
            len(constraints["temporalRoles"]),
        )
    else:
        temporal_roles["items"] = {}
        temporal_roles["maxItems"] = 0
    if constraints["recordIds"]:
        properties["basisRecordRefs"]["items"] = {
            "enum": sorted(constraints["recordIds"]),
            "type": "string",
        }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
    }


def _optional_retrieved_enum(values: set[str]) -> dict[str, Any]:
    if not values:
        return {"type": "null"}
    return {
        "anyOf": [
            {"enum": sorted(values), "type": "string"},
            {"type": "null"},
        ]
    }


def _retrieved_constraints(bundle: RetrievalBundle) -> dict[str, set[str]]:
    constraints = {
        "classifications": set(),
        "precisions": set(),
        "recordIds": set(),
        "temporalRoles": set(),
    }
    allowed_classifications = {
        "directly_supported",
        "indirectly_supported",
        "contextual",
        "correlational",
        "disputed",
        "speculative",
        "insufficient_evidence",
    }
    allowed_precisions = {"building", "city", "region", "approximate"}
    allowed_temporal_roles = {
        "sent_time",
        "received_time",
        "source_date",
        "linked_event_time",
        "linked_actor_awareness_time",
    }
    for result in bundle.results:
        if result.output is None:
            continue
        for node in _walk(result.output.model_dump(mode="json")):
            classification = node.get("evidenceClassification")
            if classification in allowed_classifications:
                constraints["classifications"].add(classification)
            for name in ("precision", "georeferencingPrecision"):
                precision = node.get(name)
                if precision in allowed_precisions:
                    constraints["precisions"].add(precision)
            role = node.get("timeRole") or node.get("role")
            if role in allowed_temporal_roles:
                constraints["temporalRoles"].add(role)
            if node.get("sentTime") is not None:
                constraints["temporalRoles"].add("sent_time")
            if node.get("receivedTime") is not None:
                constraints["temporalRoles"].add("received_time")
            if node.get("sourceDate") is not None or node.get("dateOfSource") is not None:
                constraints["temporalRoles"].add("source_date")
            if node.get("eventTime") is not None:
                constraints["temporalRoles"].add("linked_event_time")
            if node.get("asOfDate") is not None:
                constraints["temporalRoles"].add("linked_actor_awareness_time")
            for name, value in node.items():
                if name in {"corpusId", "packageId", "toolCallId"}:
                    continue
                if name.endswith("Id") and isinstance(value, str):
                    constraints["recordIds"].add(value)
                elif name.endswith("Ids") and isinstance(value, list):
                    constraints["recordIds"].update(
                        item for item in value if isinstance(item, str)
                    )
    return constraints


def _citation_variants(bundle: RetrievalBundle) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    for result in bundle.results:
        if result.output is None:
            continue
        data = result.output.model_dump(mode="json")
        record_ids: set[str] = set()
        for node in _walk(data):
            for name, value in node.items():
                if (
                    name not in {"corpusId", "packageId", "toolCallId"}
                    and name.endswith("Id")
                    and isinstance(value, str)
                ):
                    record_ids.add(value)
                elif name.endswith("Ids") and isinstance(value, list):
                    record_ids.update(item for item in value if isinstance(item, str))

            if not _is_evidence_link(node):
                continue
            signature = (
                result.plannedCallId,
                node["evidenceLinkId"],
                node["passageId"],
                node["sourceId"],
                node["targetType"],
                node["targetId"],
                node["role"],
            )
            if signature in seen:
                continue
            seen.add(signature)
            variants.append(_exact_citation(*signature))

        linked_ids = {
            value
            for signature in seen
            if signature[0] == result.plannedCallId
            for value in signature[1:6]
        }
        for record_id in sorted(record_ids - linked_ids):
            signature = (result.plannedCallId, record_id)
            if signature in seen:
                continue
            seen.add(signature)
            variants.append(_record_citation(result.plannedCallId, record_id))
    return variants


def _exact_citation(
    tool_call_id: str,
    evidence_link_id: str,
    passage_id: str,
    source_id: str,
    target_type: str,
    target_id: str,
    role: str,
) -> dict[str, Any]:
    values = {
        "toolCallId": tool_call_id,
        "evidenceLinkId": evidence_link_id,
        "passageId": passage_id,
        "sourceId": source_id,
        "targetType": target_type,
        "targetId": target_id,
        "role": role,
    }
    return _constant_object(values)


def _record_citation(tool_call_id: str, record_id: str) -> dict[str, Any]:
    return _constant_object(
        {
            "toolCallId": tool_call_id,
            "evidenceLinkId": None,
            "passageId": None,
            "sourceId": None,
            "targetType": None,
            "targetId": record_id,
            "role": None,
        }
    )


def _constant_object(values: dict[str, str | None]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            name: (
                {"type": "null"}
                if value is None
                else {"const": value, "type": "string"}
            )
            for name, value in values.items()
        },
        "required": list(values),
    }


def _is_evidence_link(node: dict[str, Any]) -> bool:
    return {
        "evidenceLinkId",
        "passageId",
        "sourceId",
        "targetType",
        "targetId",
        "role",
    }.issubset(node) and all(
        isinstance(node[name], str)
        for name in (
            "evidenceLinkId",
            "passageId",
            "sourceId",
            "targetType",
            "targetId",
            "role",
        )
    )


def _walk(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _walk(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk(nested)


def _strip_generation_annotations(value: Any) -> Any:
    if isinstance(value, list):
        return [_strip_generation_annotations(item) for item in value]
    if not isinstance(value, dict):
        return value
    return {
        key: _strip_generation_annotations(item)
        for key, item in value.items()
        if key not in {"default", "description", "examples", "title"}
    }


__all__ = ["build_analyst_response_schema"]
