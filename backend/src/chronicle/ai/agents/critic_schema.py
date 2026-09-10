"""Verdict-constrained JSON Schema for Historical Critic generation.

The Critic's ``CriticDecision`` carries per-verdict cross-field rules (a ``reject``
needs at least one rejected statement, ``retrieve_more`` needs exactly one tool
call and defers dispositions, ``approve`` needs an accepted statement and cannot
downgrade/reject, and so on -- see ``CriticDecision._validate_verdict_shape``).
The bare model schema does not encode those rules, so a local model routinely
emits an invalid shape (e.g. ``reject`` with no rejected statements), fails
Pydantic validation, and -- after bounded retries -- exhausts, forcing the run to
abstain at finalization.

This module builds a ``oneOf`` of const-discriminated per-verdict variants (the
same technique that guides the Analyst) so the model is constrained to a legal
verdict shape at generation time. It also drops the ``approve`` /
``approve_with_downgrades`` verdicts when the analysis is ungrounded (which the
deterministic critic validator forbids), and constrains accepted statement ids to
the analysis's own statements. No fabrication: every constraint mirrors a rule the
deterministic validator already enforces.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from ..contracts.analysis import AnalysisDraft, GroundingValidationReport
from ..contracts.critique import CriticDecision, CriticVerdict


def build_critic_response_schema(
    analysis: AnalysisDraft,
    grounding: GroundingValidationReport,
) -> dict[str, Any]:
    """Constrain the model to a legal, grounded-aware CriticDecision shape."""

    schema = deepcopy(CriticDecision.model_json_schema())
    defs = schema.get("$defs", {})
    base_props = schema["properties"]
    base_props["runId"] = {"const": analysis.runId, "type": "string"}
    base_props["planId"] = {"const": analysis.planId, "type": "string"}
    base_props["corpusId"] = {"const": analysis.corpusId, "type": "string"}

    statement_ids = [statement.statementId for statement in analysis.statements]
    allowed = list(CriticVerdict)
    if not grounding.valid:
        # The deterministic validator forbids approving/exposing an ungrounded
        # analysis: offer only reject / abstain / retrieve_more.
        allowed = [
            verdict
            for verdict in allowed
            if verdict
            not in {CriticVerdict.APPROVE, CriticVerdict.APPROVE_WITH_DOWNGRADES}
        ]

    variants = [_verdict_variant(base_props, verdict, statement_ids) for verdict in allowed]
    return _strip_generation_annotations({"oneOf": variants, "$defs": defs})


def _verdict_variant(
    base_props: dict[str, Any],
    verdict: CriticVerdict,
    statement_ids: list[str],
) -> dict[str, Any]:
    props = deepcopy(base_props)
    props["verdict"] = {"const": verdict.value, "type": "string"}
    if statement_ids:
        props["acceptedStatementIds"] = {
            **props["acceptedStatementIds"],
            "items": {"enum": sorted(statement_ids), "type": "string"},
        }

    if verdict is CriticVerdict.RETRIEVE_MORE:
        # Exactly one follow-up call; all statement dispositions deferred.
        props["additionalToolCalls"] = {**props["additionalToolCalls"], "minItems": 1, "maxItems": 1}
        _force_empty(props, "acceptedStatementIds")
        _force_empty(props, "downgradedStatements")
        _force_empty(props, "rejectedStatements")
    else:
        _force_empty(props, "additionalToolCalls")
        if verdict is CriticVerdict.APPROVE:
            props["acceptedStatementIds"] = {**props["acceptedStatementIds"], "minItems": 1}
            _force_empty(props, "downgradedStatements")
            _force_empty(props, "rejectedStatements")
        elif verdict is CriticVerdict.APPROVE_WITH_DOWNGRADES:
            props["downgradedStatements"] = {**props["downgradedStatements"], "minItems": 1}
        elif verdict is CriticVerdict.REJECT:
            props["rejectedStatements"] = {**props["rejectedStatements"], "minItems": 1}
        elif verdict is CriticVerdict.ABSTAIN:
            _force_empty(props, "acceptedStatementIds")
            _force_empty(props, "downgradedStatements")
            _force_empty(props, "rejectedStatements")

    return {
        "type": "object",
        "additionalProperties": False,
        "properties": props,
        "required": list(props),
    }


def _force_empty(props: dict[str, Any], key: str) -> None:
    field = dict(props[key])
    field["maxItems"] = 0
    field.pop("minItems", None)
    props[key] = field


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


__all__ = ["build_critic_response_schema"]
