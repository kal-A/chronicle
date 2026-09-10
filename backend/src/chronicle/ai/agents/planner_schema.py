"""Context-constrained JSON Schema for small-model Planner generation."""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Mapping, Sequence

from ..contracts.plan import InvestigationPlan, QuestionType
from ..contracts.run import InvestigationRequest, SelectedRecordType
from ..tools.contracts import ToolSpec


ARGUMENT_RECORD_TYPES: dict[str, frozenset[SelectedRecordType]] = {
    "claimId": frozenset({SelectedRecordType.CLAIM}),
    "claimIds": frozenset({SelectedRecordType.CLAIM}),
    "relationshipId": frozenset({SelectedRecordType.RELATIONSHIP}),
    "relationshipIds": frozenset({SelectedRecordType.RELATIONSHIP}),
    "eventId": frozenset({SelectedRecordType.EVENT}),
    "eventIds": frozenset({SelectedRecordType.EVENT}),
    "entityId": frozenset({SelectedRecordType.ENTITY}),
    "entityIds": frozenset({SelectedRecordType.ENTITY}),
    "actorId": frozenset({SelectedRecordType.ENTITY}),
    "actorIds": frozenset({SelectedRecordType.ENTITY}),
    "knowledgeStateId": frozenset({SelectedRecordType.KNOWLEDGE_STATE}),
    "knowledgeStateIds": frozenset({SelectedRecordType.KNOWLEDGE_STATE}),
    "sourceId": frozenset({SelectedRecordType.SOURCE}),
    "sourceIds": frozenset({SelectedRecordType.SOURCE}),
    "documentId": frozenset({SelectedRecordType.DOCUMENT}),
    "documentIds": frozenset({SelectedRecordType.DOCUMENT}),
    "passageId": frozenset({SelectedRecordType.PASSAGE}),
    "passageIds": frozenset({SelectedRecordType.PASSAGE}),
    "placeId": frozenset({SelectedRecordType.PLACE}),
    "placeIds": frozenset({SelectedRecordType.PLACE}),
    "sceneId": frozenset({SelectedRecordType.MAP_SCENE}),
    "sceneIds": frozenset({SelectedRecordType.MAP_SCENE}),
    "recordId": frozenset(
        {SelectedRecordType.CLAIM, SelectedRecordType.RELATIONSHIP}
    ),
    "startNodeId": frozenset(
        {
            SelectedRecordType.CLAIM,
            SelectedRecordType.RELATIONSHIP,
            SelectedRecordType.KNOWLEDGE_STATE,
        }
    ),
}


def trusted_record_ids(
    request: InvestigationRequest,
) -> dict[SelectedRecordType, set[str]]:
    context = request.workspaceContext
    if context is None:
        return {}
    trusted: dict[SelectedRecordType, set[str]] = {}
    for record in context.selectedRecords:
        trusted.setdefault(record.recordType, set()).add(record.recordId)
    if context.sceneId:
        trusted.setdefault(SelectedRecordType.MAP_SCENE, set()).add(context.sceneId)
    return trusted


def contextual_tool_specs(
    specs: Sequence[ToolSpec],
    request: InvestigationRequest,
) -> list[ToolSpec]:
    """Keep tools whose required literal IDs exist in trusted context."""

    trusted = trusted_record_ids(request)
    return [
        spec
        for spec in specs
        if _has_required_record_ids(spec, trusted)
        and (
            spec.name != "find_counterevidence"
            or _question_calls_for_counterevidence(request.userQuestion)
        )
        and (
            spec.name != "get_timeline_context"
            or _question_calls_for_timeline(request.userQuestion)
        )
        and (
            spec.name != "get_actor_knowledge_state"
            or _question_calls_for_actor_knowledge(request.userQuestion)
        )
    ]


def build_planner_response_schema(
    request: InvestigationRequest,
    specs: Sequence[ToolSpec],
) -> dict[str, Any]:
    """Couple each advertised tool name to its real, trusted argument schema."""

    schema = deepcopy(InvestigationPlan.model_json_schema())
    schema["required"] = list(schema["properties"])
    schema["properties"]["runId"] = {"const": request.runId, "type": "string"}
    schema["properties"]["corpusId"] = {"const": request.corpusId, "type": "string"}
    _require_nonempty_optional_string(schema["properties"]["unsupportedReason"])

    available_names = {spec.name for spec in specs}
    question_types = schema["$defs"]["QuestionType"]["enum"]
    if (
        "get_actor_knowledge_state" not in available_names
        or not _question_calls_for_actor_knowledge(request.userQuestion)
    ):
        question_types.remove(QuestionType.ACTOR_KNOWLEDGE.value)
    if (
        "get_timeline_context" not in available_names
        or not _question_calls_for_timeline(request.userQuestion)
    ):
        question_types.remove(QuestionType.TIMELINE_ORDERING.value)
    if not available_names.intersection(
        {"find_counterevidence", "get_claim_evidence", "search_passages"}
    ) or not _question_calls_for_counterevidence(request.userQuestion):
        # Gate COUNTEREVIDENCE on the question itself (like ACTOR_KNOWLEDGE and
        # TIMELINE_ORDERING), not merely on tool availability. Over a passage-only
        # corpus search_passages is always present, so without this a small model
        # can misclassify a plain factual question as COUNTEREVIDENCE and emit an
        # incoherent plan that the planner then rejects -> a needless abstention.
        question_types.remove(QuestionType.COUNTEREVIDENCE.value)

    call_schema = schema["$defs"]["PlannedToolCall"]
    trusted = trusted_record_ids(request)
    variants = [
        _tool_call_schema(call_schema, spec, trusted)
        for spec in specs
    ]
    planned_calls = schema["properties"]["plannedToolCalls"]
    if variants:
        planned_calls["items"] = {"oneOf": variants}
        planned_calls["maxItems"] = 1
    else:
        planned_calls["items"] = {}
        planned_calls["maxItems"] = 0
    return _strip_generation_annotations(schema)


def _has_required_record_ids(
    spec: ToolSpec,
    trusted: Mapping[SelectedRecordType, set[str]],
) -> bool:
    properties = spec.inputSchema.get("properties", {})
    for name in spec.inputSchema.get("required", []):
        if name == "corpusId":
            continue
        allowed_types = ARGUMENT_RECORD_TYPES.get(name)
        if allowed_types is None:
            if re.search(r"(?:Id|Ids)$", name):
                return False
            continue
        available = _ids_for_types(trusted, allowed_types)
        property_schema = properties.get(name, {})
        minimum = (
            property_schema.get("minItems", 1)
            if property_schema.get("type") == "array"
            else 1
        )
        if len(available) < minimum:
            return False
    return True


def _question_calls_for_counterevidence(question: str) -> bool:
    """Conservatively expose the counterevidence-only route when relevant."""

    normalized = question.casefold()
    return bool(
        re.search(
            r"\b(counterevidence|contradict(?:s|ed|ion|ory)?|challenge[sd]?|"
            r"disput(?:e|ed|es)|oppos(?:e|ed|ing)|against|alternative account|"
            r"compare[sd]?|comparison|versus|why|caus(?:e|ed|al|ation)|"
            r"led to|because|responsible|influence[sd]?)\b",
            normalized,
        )
    )


def _question_calls_for_timeline(question: str) -> bool:
    normalized = question.casefold()
    return bool(
        re.search(
            r"\b(timeline|chronolog(?:y|ical)|sequence|before|after|first|next|"
            r"preced(?:e|ed|ing)|follow(?:ed|ing)?|in what order|when did|"
            r"how did .* unfold)\b",
            normalized,
        )
    )


def _question_calls_for_actor_knowledge(question: str) -> bool:
    normalized = question.casefold()
    return bool(
        re.search(
            r"\b(knew|know|known|knowledge|aware(?:ness)?|informed|learned|"
            r"received|understood|believed)\b",
            normalized,
        )
    )


def _tool_call_schema(
    base: dict[str, Any],
    spec: ToolSpec,
    trusted: Mapping[SelectedRecordType, set[str]],
) -> dict[str, Any]:
    properties = deepcopy(base["properties"])
    properties["toolName"] = {"const": spec.name, "type": "string"}
    properties["arguments"] = _trusted_argument_schema(spec.inputSchema, trusted)
    if spec.name == "search_passages":
        _force_minimal_search_arguments(properties["arguments"])
    properties["bindings"] = {"items": {}, "maxItems": 0, "type": "array"}
    properties["dependsOn"] = {"items": {}, "maxItems": 0, "type": "array"}
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": [
            "callId",
            "toolName",
            "purposeCode",
            "arguments",
            "bindings",
            "dependsOn",
        ],
    }


def _force_minimal_search_arguments(arguments: dict[str, Any]) -> None:
    """Pin search_passages to a plain query search by forcing every optional
    filter to its always-valid absent shape. A small model over-specifies these
    filters two ways: (1) dateRange<->dateRoles must be set together (a Pydantic
    cross-field rule the JSON schema cannot express for the decoder), so setting
    one alone makes the runner reject the call; (2) evidenceRoles /
    sourceClassifications filter on passage metadata an auto-acquired corpus does
    not carry, so the search returns zero matches and the analyst abstains on a
    non-answer. Dropping the filters leaves a plain query search -- exactly what a
    passage corpus needs -- that reliably surfaces the relevant passages. Scope
    filtering happens at discovery/acquisition, not this per-call filter."""

    properties = arguments.get("properties")
    if not isinstance(properties, dict):
        return
    if "dateRange" in properties:
        properties["dateRange"] = {"type": "null"}
    for field in ("dateRoles", "evidenceRoles", "sourceClassifications"):
        if field in properties:
            properties[field] = {"type": "array", "items": {}, "maxItems": 0}


def _trusted_argument_schema(
    input_schema: dict[str, Any],
    trusted: Mapping[SelectedRecordType, set[str]],
) -> dict[str, Any]:
    rendered = _inline_local_refs(deepcopy(input_schema), input_schema.get("$defs", {}))
    rendered.pop("$defs", None)
    properties = rendered.get("properties", {})
    properties.pop("corpusId", None)
    rendered["required"] = [
        name for name in rendered.get("required", []) if name != "corpusId"
    ]
    rendered["additionalProperties"] = False
    for name in list(properties):
        if not re.search(r"(?:Id|Ids)$", name):
            continue
        allowed_types = ARGUMENT_RECORD_TYPES.get(name)
        if allowed_types is None:
            if name not in rendered["required"]:
                properties.pop(name)
            continue
        allowed_ids = _ids_for_types(trusted, allowed_types)
        if not allowed_ids:
            if name not in rendered["required"]:
                properties.pop(name)
            continue
        if properties[name].get("type") == "array":
            item_schema = properties[name].setdefault("items", {"type": "string"})
            item_schema["enum"] = allowed_ids
        else:
            properties[name]["enum"] = allowed_ids
    return rendered


def _inline_local_refs(value: Any, definitions: Mapping[str, Any]) -> Any:
    if isinstance(value, list):
        return [_inline_local_refs(item, definitions) for item in value]
    if not isinstance(value, dict):
        return value
    reference = value.get("$ref")
    if isinstance(reference, str) and reference.startswith("#/$defs/"):
        name = reference.rsplit("/", 1)[-1]
        resolved = _inline_local_refs(deepcopy(definitions[name]), definitions)
        siblings = {
            key: _inline_local_refs(item, definitions)
            for key, item in value.items()
            if key != "$ref"
        }
        return {**resolved, **siblings}
    return {
        key: _inline_local_refs(item, definitions)
        for key, item in value.items()
        if key != "$defs"
    }


def _ids_for_types(
    trusted: Mapping[SelectedRecordType, set[str]],
    record_types: frozenset[SelectedRecordType],
) -> list[str]:
    return sorted(
        record_id
        for record_type in record_types
        for record_id in trusted.get(record_type, set())
    )


def _require_nonempty_optional_string(schema: dict[str, Any]) -> None:
    for variant in schema.get("anyOf", []):
        if variant.get("type") == "string":
            variant["minLength"] = 1


def _strip_generation_annotations(value: Any) -> Any:
    """Keep decoder constraints while removing prose-only schema metadata."""

    if isinstance(value, list):
        return [_strip_generation_annotations(item) for item in value]
    if not isinstance(value, dict):
        return value
    return {
        key: _strip_generation_annotations(item)
        for key, item in value.items()
        if key not in {"default", "description", "examples", "title"}
    }


__all__ = [
    "ARGUMENT_RECORD_TYPES",
    "build_planner_response_schema",
    "contextual_tool_specs",
    "trusted_record_ids",
]
