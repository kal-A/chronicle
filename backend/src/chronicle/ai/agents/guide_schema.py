"""Approval-constrained JSON Schema for Investigation Guide generation.

The Guide composes the final ``AgentAnswer`` from the critic-approved statements.
Its bare schema is unconstrained, so a small model routinely emits an invalid
answer -- most often a citation carrying only a ``toolCallId`` with no record id
(``AnswerCitation`` requires at least one retrieved record) -- which fails Pydantic
validation and, after bounded retries, exhausts and forces an abstention even
though a good answer was in reach.

This constrains generation to what will validate: citations are forced empty
(they are mechanically re-attached from the approved statements after generation,
so the model never needs to produce them), map ``actions`` are forced empty (a
passage-only acquired corpus has no map records to target), and ``keyPoints`` are
tied to the approved statement ids -- one per approved statement, matching the
deterministic answer validator. When nothing was approved (reject/abstain) the
answer is pinned to an empty ``abstained`` shape. Every constraint mirrors a rule
``validate_agent_answer`` already enforces -- no fabrication.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from ..contracts.analysis import AnalysisDraft
from ..contracts.answer import AgentAnswer
from ..contracts.critique import CriticDecision
from .validation import approved_statements

_EMPTY_ARRAY = {"type": "array", "items": {}, "maxItems": 0}


def build_guide_response_schema(
    analysis: AnalysisDraft,
    decision: CriticDecision,
) -> dict[str, Any]:
    """Constrain the model to a valid, approval-consistent AgentAnswer."""

    schema = deepcopy(AgentAnswer.model_json_schema())
    props = schema["properties"]
    props["runId"] = {"const": analysis.runId, "type": "string"}
    props["planId"] = {"const": analysis.planId, "type": "string"}
    props["corpusId"] = {"const": analysis.corpusId, "type": "string"}

    # Citations are re-attached canonically after generation; map actions and
    # disagreements have no basis over a passage-only corpus. Force all empty so
    # the model always produces a schema-valid answer.
    props["citations"] = dict(_EMPTY_ARRAY)
    props["actions"] = dict(_EMPTY_ARRAY)
    props["disagreements"] = dict(_EMPTY_ARRAY)

    status_schema = schema["$defs"]["AnswerStatus"]
    status_schema["enum"] = [
        value for value in status_schema["enum"] if value != "needs_more_retrieval"
    ]

    approved = approved_statements(analysis, decision)
    if approved:
        # An approved critique yields an answered/partial answer with exactly one
        # key point per approved statement, whose text must EXACTLY equal the
        # approved statement's text (validate_agent_answer forbids paraphrase).
        # Pin each key point's id+text to a const so the small model cannot
        # rephrase, and (single statement) pin directAnswer to that same text
        # (directAnswer must equal the key-point texts joined).
        status_schema["enum"] = [
            value for value in status_schema["enum"] if value != "abstained"
        ]
        point_consts = [
            {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "statementId": {"const": statement_id, "type": "string"},
                    "text": {"const": text, "type": "string"},
                },
                "required": ["statementId", "text"],
            }
            for statement_id, (text, _statement) in approved.items()
        ]
        count = len(point_consts)
        props["keyPoints"] = {
            "type": "array",
            "minItems": count,
            "maxItems": count,
            "uniqueItems": True,
            "items": point_consts[0] if count == 1 else {"oneOf": point_consts},
        }
        if count == 1:
            props["directAnswer"] = {
                "const": next(iter(approved.values()))[0],
                "type": "string",
            }
    else:
        # Nothing approved -> an abstained answer with everything empty.
        props["status"] = {"const": "abstained", "type": "string"}
        props["keyPoints"] = dict(_EMPTY_ARRAY)

    return _strip_generation_annotations(schema)


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


__all__ = ["build_guide_response_schema"]
