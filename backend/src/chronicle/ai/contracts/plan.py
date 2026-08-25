"""Bounded, model-facing investigation plan contracts for Phase E3."""

from __future__ import annotations

from enum import Enum
import json
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

ShortText = Annotated[str, Field(min_length=1, max_length=500)]
Identifier = Annotated[str, Field(min_length=1, max_length=100)]


class PlanDisposition(str, Enum):
    PROCEED = "proceed"
    ABSTAIN = "abstain"


class QuestionType(str, Enum):
    DIRECT_EVIDENCE = "direct_evidence"
    EXPLANATION = "explanation"
    TIMELINE_ORDERING = "timeline_ordering"
    RELATIONSHIP_TRACE = "relationship_trace"
    SOURCE_COMPARISON = "source_comparison"
    ACTOR_KNOWLEDGE = "actor_knowledge"
    COUNTEREVIDENCE = "counterevidence"
    DISPUTED_INTERPRETATION = "disputed_interpretation"
    MISSING_EVIDENCE = "missing_evidence"
    INVALID_PREMISE = "invalid_premise"
    OUT_OF_CORPUS = "out_of_corpus"


class RequiredEvidenceType(str, Enum):
    PASSAGE = "passage"
    SOURCE_METADATA = "source_metadata"
    CLAIM_EVIDENCE = "claim_evidence"
    RELATIONSHIP_EVIDENCE = "relationship_evidence"
    TIMELINE = "timeline"
    KNOWLEDGE_STATE = "knowledge_state"
    COUNTEREVIDENCE = "counterevidence"
    MAP_CONTEXT = "map_context"


class ToolPurpose(str, Enum):
    FIND_SUPPORT = "find_support"
    FIND_COUNTEREVIDENCE = "find_counterevidence"
    VERIFY_SOURCE = "verify_source"
    COMPARE_SOURCES = "compare_sources"
    TRACE_RELATIONSHIP = "trace_relationship"
    ESTABLISH_TIMELINE = "establish_timeline"
    CHECK_KNOWLEDGE = "check_knowledge"
    ESTABLISH_GEOGRAPHY = "establish_geography"
    SEARCH_CONTEXT = "search_context"


class ArgumentBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    argumentName: str = Field(min_length=1, max_length=80)
    sourceCallId: str = Field(min_length=1, max_length=80)
    recordType: str = Field(min_length=1, max_length=80)
    ordinal: int = Field(default=0, ge=0, le=19)


class PlannedToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    callId: str = Field(min_length=1, max_length=80)
    toolName: str = Field(min_length=1, max_length=100)
    purposeCode: ToolPurpose
    arguments: dict[Identifier, JsonValue] = Field(default_factory=dict, max_length=20)
    bindings: list[ArgumentBinding] = Field(default_factory=list, max_length=8)
    dependsOn: list[Identifier] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def _bound_serialized_arguments(self) -> "PlannedToolCall":
        if len(json.dumps(self.arguments, sort_keys=True, default=str)) > 2_000:
            raise ValueError("serialized tool arguments exceed 2,000 characters")
        return self


class InvestigationPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    planId: str = Field(min_length=1, max_length=100)
    runId: str = Field(min_length=1, max_length=100)
    corpusId: str = Field(min_length=1, max_length=200)
    disposition: PlanDisposition
    normalizedQuestion: str = Field(min_length=1, max_length=500)
    questionType: QuestionType
    scope: list[ShortText] = Field(default_factory=list, max_length=8)
    requiredEvidenceTypes: list[RequiredEvidenceType] = Field(default_factory=list, max_length=8)
    plannedToolCalls: list[PlannedToolCall] = Field(default_factory=list, max_length=3)
    requiresCounterevidence: bool = False
    requiresTimeline: bool = False
    requiresKnowledgeState: bool = False
    planningLimitations: list[ShortText] = Field(default_factory=list, max_length=6)
    unsupportedReason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _validate_plan_shape(self) -> "InvestigationPlan":
        call_ids = [call.callId for call in self.plannedToolCalls]
        if len(call_ids) != len(set(call_ids)):
            raise ValueError("plannedToolCalls must use unique callId values")
        known_ids = set(call_ids)
        for call in self.plannedToolCalls:
            if "corpusId" in call.arguments:
                raise ValueError("corpusId is runner-owned and must not appear in tool arguments")
            dependencies = set(call.dependsOn) | {binding.sourceCallId for binding in call.bindings}
            if call.callId in dependencies or not dependencies.issubset(known_ids):
                raise ValueError("tool-call dependencies must reference other calls in this plan")
        if self.disposition is PlanDisposition.ABSTAIN:
            if self.plannedToolCalls:
                raise ValueError("an abstaining plan cannot contain tool calls")
            if not self.unsupportedReason:
                raise ValueError("an abstaining plan requires unsupportedReason")
        elif not self.plannedToolCalls:
            raise ValueError("a proceeding plan requires at least one tool call")
        return self
