"""Retrieval-constrained JSON Schema for Evidence Analyst generation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable

from ...contracts.enums import Awareness
from ..contracts.analysis import AnalysisDraft, StatementKind
from ..contracts.retrieval import RetrievalBundle

_TRUNCATION_DISCLOSURE = (
    "Retrieval was truncated; this reflects only the returned records, not the "
    "full corpus."
)


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
    if bundle.partial:
        # A partial retrieval bundle cannot support an ANSWERED status
        # (grounding._validate_grounding): allow only partial / abstained.
        status_schema["enum"] = [
            value for value in status_schema["enum"] if value != "answered"
        ]
    properties["suggestedFollowUpToolCall"] = {"type": "null"}

    # AnalysisCitation is a single object whose fields are enum-constrained to the
    # retrieved values, rather than a oneOf of one fully-materialized constant
    # object per (call, record). The emitted contract is unchanged; the exact
    # co-occurrence of (toolCallId, passage/source/target/role) is re-enforced
    # deterministically by grounding.validate_grounding, which is authoritative.
    # This removes combinatorial schema growth in the number of retrieved records.
    index = _citable_index(bundle)
    has_citable = bool(index["recordIds"] and index["callIds"])
    schema["$defs"]["AnalysisCitation"] = (
        _compact_citation_schema(index) if has_citable else {"not": {}}
    )
    if not has_citable:
        properties["status"] = {"const": "abstained", "type": "string"}
        properties["statements"]["maxItems"] = 0
        properties["abstentionReason"] = {
            "minLength": 1,
            "maxLength": 800,
            "type": "string",
        }
    else:
        # Relevant passages were retrieved, so synthesize from them rather than
        # abstain: a simple factual question whose sources are in hand should get a
        # cited answer / the factors surrounding the event, not a non-answer. The
        # honesty guardrails still hold -- every statement cites a retrieved record
        # and is constrained to inferred synthesis (see _statement_variant), the
        # status stays partial when the bundle is partial, and genuine no-evidence
        # (no citations) still abstains above.
        status_schema["enum"] = [
            value for value in status_schema["enum"] if value != "abstained"
        ]
        properties["statements"] = {**properties["statements"], "minItems": 1}

    if _bundle_is_truncated(bundle):
        # grounding rejects an undisclosed truncation. Force the disclosure into
        # the draft's limitations so the model cannot silently omit it.
        properties["limitations"] = _truncation_limitations_schema(
            properties["limitations"]
        )

    base_statement = schema["$defs"]["AnalysisStatement"]
    constraints = _retrieved_constraints(bundle)
    allow_direct_extraction = _has_direct_extraction_basis(bundle)
    kinds = list(StatementKind)
    if not _has_knowledge_basis(bundle):
        # A KNOWLEDGE statement needs a retrieved knowledge-state / awareness
        # record to ground; without one the kind can only force an abstention.
        kinds = [kind for kind in kinds if kind is not StatementKind.KNOWLEDGE]
    # A single statement object with statementKind enum-constrained to the allowed
    # kinds, rather than a oneOf of one full copy per kind. The KNOWLEDGE<->awareness
    # and synthesis<->inferred bindings are re-enforced by the AnalysisStatement
    # Pydantic validators and grounding, which are authoritative -- so this removes
    # duplication (constant schema size in the number of kinds), not validation.
    schema["$defs"]["AnalysisStatement"] = _statement_schema(
        base_statement, kinds, constraints, allow_direct_extraction
    )
    return _strip_generation_annotations(schema)


def _truncation_limitations_schema(existing: dict[str, Any]) -> dict[str, Any]:
    # Force the mandatory truncation disclosure as the sole limitation. A single
    # const-valued array item is the strongest constraint llama.cpp's grammar
    # honors (prefixItems is not), so the model must emit exactly this string --
    # a true, system-known caveat, never a fabricated finding.
    return {
        "type": "array",
        "items": {"const": _TRUNCATION_DISCLOSURE, "type": "string"},
        "minItems": 1,
        "maxItems": 1,
    }


def _has_knowledge_basis(bundle: RetrievalBundle) -> bool:
    """Whether the bundle carries a retrieved awareness / knowledge-state record
    that a KNOWLEDGE statement could ground on (grounding._validate_knowledge)."""

    awareness_values = {item.value for item in Awareness}
    for result in bundle.results:
        if result.output is None:
            continue
        for node in _walk(result.output.model_dump(mode="json")):
            if node.get("awareness") in awareness_values:
                return True
    return False


def _bundle_is_truncated(bundle: RetrievalBundle) -> bool:
    """Mirror grounding's truncation detection: bundle- or result-level flags, or
    any nested ``*truncated`` boolean in a tool output."""

    if bundle.truncated or any(result.truncated for result in bundle.results):
        return True
    for result in bundle.results:
        if result.output is None:
            continue
        for node in _walk(result.output.model_dump(mode="json")):
            if any(
                key.lower().endswith("truncated") and value is True
                for key, value in node.items()
            ):
                return True
    return False


def _statement_schema(
    base: dict[str, Any],
    kinds: list[StatementKind],
    constraints: dict[str, set[str]],
    allow_direct_extraction: bool = True,
) -> dict[str, Any]:
    properties = deepcopy(base["properties"])
    properties["statementKind"] = {"enum": [kind.value for kind in kinds], "type": "string"}
    if not allow_direct_extraction:
        # No retrieved evidence-link or directness metadata exists in this bundle
        # (a passage-only, auto-acquired corpus), so an EXTRACTED_RECORD/DIRECT
        # statement can never pass deterministic grounding -- it would only force
        # an abstention. Constrain the model to the honest, groundable form:
        # inferred synthesis over the retrieved passages, flagged for review.
        properties["statementForm"] = {"const": "evidence_synthesis", "type": "string"}
        properties["directness"] = {"const": "inferred", "type": "string"}
    # knowledgeAwareness is allowed (Awareness-or-null) only when KNOWLEDGE is a
    # permitted kind; otherwise it is null. The AnalysisStatement Pydantic validator
    # enforces the exact KNOWLEDGE<->awareness pairing per statement.
    properties["knowledgeAwareness"] = (
        {"anyOf": [{"$ref": "#/$defs/Awareness"}, {"type": "null"}]}
        if StatementKind.KNOWLEDGE in kinds
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


def _has_direct_extraction_basis(bundle: RetrievalBundle) -> bool:
    """Whether the bundle can ground an EXTRACTED_RECORD/DIRECT statement.

    Mirrors ``grounding._validate_directness``: a direct extraction needs a
    retrieved evidence-link, a record carrying stored directness
    (``directOrInferred``), or an explicit directness-availability marker.
    Passage-only acquired corpora carry none of these, so only inferred
    synthesis can ground and the statement schema is constrained accordingly.
    """

    for result in bundle.results:
        if result.output is None:
            continue
        for node in _walk(result.output.model_dump(mode="json")):
            if _is_evidence_link(node):
                return True
            if node.get("directOrInferred") in {"direct", "inferred"}:
                return True
            if node.get("directOrInferredAvailability") in {"recorded", "not-recorded"}:
                return True
    return False


def _citable_index(bundle: RetrievalBundle) -> dict[str, set[str] | list[str]]:
    """Gather the retrieved values a citation may legally reference, matching the
    sets grounding.validate_grounding resolves against. ``callIds`` lists only
    calls that returned at least one record (citing a record-less call can never
    resolve); ``recordIds`` is the union of per-call record ids plus the reference
    index, i.e. exactly grounding's accepted target set."""

    call_ids: list[str] = []
    record_ids: set[str] = set()
    evidence_link_ids: set[str] = set()
    target_types: set[str] = set()
    for result in bundle.results:
        if result.output is None:
            continue
        per_call: set[str] = set()
        for node in _walk(result.output.model_dump(mode="json")):
            for name, value in node.items():
                if name in {"corpusId", "packageId", "toolCallId"}:
                    continue
                if name.endswith("Id") and isinstance(value, str):
                    per_call.add(value)
                elif name.endswith("Ids") and isinstance(value, list):
                    per_call.update(item for item in value if isinstance(item, str))
            if _is_evidence_link(node):
                evidence_link_ids.add(node["evidenceLinkId"])
                target_types.add(node["targetType"])
        if per_call:
            call_ids.append(result.plannedCallId)
            record_ids |= per_call
    index = bundle.referenceIndex
    record_ids |= set(index.passageIds) | set(index.sourceIds) | set(index.documentIds)
    record_ids |= set(index.claimIds) | set(index.relationshipIds) | set(index.eventIds)
    record_ids |= set(index.knowledgeStateIds) | set(index.placeIds) | set(index.mapSceneIds)
    return {
        "callIds": call_ids,
        "recordIds": record_ids,
        "passageIds": set(index.passageIds),
        "sourceIds": set(index.sourceIds),
        "evidenceLinkIds": evidence_link_ids,
        "targetTypes": target_types,
    }


def _compact_citation_schema(index: dict[str, set[str] | list[str]]) -> dict[str, Any]:
    """One citation object with per-field enums over the retrieved values. The
    emitted fields are exactly AnalysisCitation's; grounding re-enforces that the
    (toolCallId, passage/source/target/role) tuple actually co-occurred, so this
    does not accept any combination grounding would reject."""

    def enum_or_null(values: set[str] | list[str]) -> dict[str, Any]:
        ordered = sorted(values)
        if not ordered:
            return {"type": "null"}
        return {"anyOf": [{"enum": ordered, "type": "string"}, {"type": "null"}]}

    role_schema = (
        {"anyOf": [{"$ref": "#/$defs/EvidenceLinkRole"}, {"type": "null"}]}
        if index["evidenceLinkIds"]
        else {"type": "null"}
    )
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "toolCallId": {"enum": sorted(index["callIds"]), "type": "string"},
            "evidenceLinkId": enum_or_null(index["evidenceLinkIds"]),
            "passageId": enum_or_null(index["passageIds"]),
            "sourceId": enum_or_null(index["sourceIds"]),
            "targetType": enum_or_null(index["targetTypes"]),
            "targetId": {"enum": sorted(index["recordIds"]), "type": "string"},
            "role": role_schema,
        },
        "required": [
            "toolCallId",
            "evidenceLinkId",
            "passageId",
            "sourceId",
            "targetType",
            "targetId",
            "role",
        ],
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
