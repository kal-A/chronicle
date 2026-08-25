"""One-call Investigation Planner with deterministic post-generation gates."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping, Sequence

from ..contracts.plan import (
    InvestigationPlan,
    PlanDisposition,
    QuestionType,
    RequiredEvidenceType,
)
from ..contracts.run import (
    CorpusSnapshot,
    InvestigationRequest,
    PromptMeasurement,
    SelectedRecordType,
)
from ..models.metadata import ModelCallRecord, ModelGenerationSettings
from ..models.protocol import ModelProvider
from ..orchestration.policies import AgentExecutionPolicy
from ..tools.contracts import ToolSpec
from .planner_prompt import (
    PlannerPrompt,
    ToolSpecRepresentation,
    available_tool_specs,
    build_planner_prompt,
)
from .planner_schema import (
    ARGUMENT_RECORD_TYPES,
    build_planner_response_schema,
    trusted_record_ids,
)

PLANNER_PROMPT_VERSION = "e3-investigation-planner-v1"


class PlannerError(RuntimeError):
    """Base class for deterministic Planner boundary failures."""


class PlannerBudgetError(PlannerError):
    """The complete model input does not fit an approved E3 budget."""


class PlannerValidationError(PlannerError):
    """A schema-valid model proposal failed deterministic authorization."""

    modelCall: ModelCallRecord | None = None
    promptMeasurement: PromptMeasurement | None = None


@dataclass(frozen=True)
class PlannerExecution:
    """Auditable metadata kept outside the model-facing plan response."""

    modelCall: ModelCallRecord
    promptMeasurement: PromptMeasurement
    availableToolNames: tuple[str, ...]
    representation: ToolSpecRepresentation


class InvestigationPlanner:
    def __init__(
        self,
        provider: ModelProvider,
        policy: AgentExecutionPolicy | None = None,
        *,
        representation: ToolSpecRepresentation = ToolSpecRepresentation.CAPABILITY_FILTERED,
    ) -> None:
        self._provider = provider
        self._policy = policy or AgentExecutionPolicy()
        self._representation = representation
        self.last_prompt: PlannerPrompt | None = None
        self.last_execution: PlannerExecution | None = None

    def plan(
        self,
        request: InvestigationRequest,
        corpus_snapshot: CorpusSnapshot,
        tool_specs: Sequence[ToolSpec],
    ) -> InvestigationPlan:
        """Return only a validated InvestigationPlan.

        Provider retries are internal to one generate_structured invocation, so
        this method always consumes exactly one logical Planner call.
        """

        self.last_prompt = None
        self.last_execution = None
        if request.corpusId != corpus_snapshot.corpusId:
            raise PlannerValidationError("request and corpus snapshot identity do not match")

        specs = available_tool_specs(tool_specs, corpus_snapshot, request)
        response_schema = build_planner_response_schema(request, specs)
        try:
            prompt = build_planner_prompt(
                request,
                corpus_snapshot,
                specs,
                self._policy,
                representation=self._representation,
                response_schema=response_schema,
            )
        except ValueError as exc:
            raise PlannerBudgetError(str(exc)) from None
        self.last_prompt = prompt

        result = self._provider.generate_structured(
            system_prompt=prompt.systemPrompt,
            user_prompt=prompt.userPrompt,
            response_model=InvestigationPlan,
            response_schema=response_schema,
            prompt_version=PLANNER_PROMPT_VERSION,
            temperature=0.0,
            generation_settings=ModelGenerationSettings(
                temperature=0.0,
                contextTokens=self._policy.modelContextTokens,
                maxCompletionTokens=self._policy.plannerMaxCompletionTokens,
            ),
        )
        candidate = result.value
        try:
            self._validate_candidate(candidate, request, corpus_snapshot, specs)
        except PlannerValidationError as exc:
            # Preserve auditability for a successful provider call whose plan
            # Chronicle deterministically rejected. This is public metadata,
            # never chain-of-thought.
            exc.modelCall = result.modelCall
            exc.promptMeasurement = prompt.measurement
            raise
        self.last_execution = PlannerExecution(
            modelCall=result.modelCall,
            promptMeasurement=prompt.measurement,
            availableToolNames=tuple(spec.name for spec in specs),
            representation=self._representation,
        )
        return candidate

    def _validate_candidate(
        self,
        plan: InvestigationPlan,
        request: InvestigationRequest,
        corpus: CorpusSnapshot,
        specs: Sequence[ToolSpec],
    ) -> None:
        if plan.runId != request.runId or plan.corpusId != corpus.corpusId:
            raise PlannerValidationError("plan identity does not match the immutable request")
        if len(plan.plannedToolCalls) > self._policy.maxInitialToolCalls:
            raise PlannerValidationError("plan exceeds the initial tool-call budget")
        if plan.questionType in {QuestionType.OUT_OF_CORPUS, QuestionType.INVALID_PREMISE}:
            if plan.disposition is not PlanDisposition.ABSTAIN:
                raise PlannerValidationError(
                    f"a {plan.questionType.value} request must abstain"
                )
        if plan.disposition is PlanDisposition.PROCEED:
            _validate_question_coherence(plan)

        spec_by_name = {spec.name: spec for spec in specs}
        trusted_ids = trusted_record_ids(request)
        prior_call_ids: set[str] = set()
        for call in plan.plannedToolCalls:
            spec = spec_by_name.get(call.toolName)
            if spec is None:
                raise PlannerValidationError(
                    f'tool "{call.toolName}" is not authorized for this corpus or '
                    "selected record type"
                )
            if not set(spec.requiredCapabilities).issubset(corpus.capabilities):
                raise PlannerValidationError(
                    f'tool "{call.toolName}" requires unavailable corpus capabilities'
                )
            bound_arguments = {binding.argumentName for binding in call.bindings}
            if bound_arguments & set(call.arguments):
                raise PlannerValidationError(
                    "an argument binding cannot also contain a model-supplied literal"
                )
            binding_sources = {binding.sourceCallId for binding in call.bindings}
            if not (binding_sources | set(call.dependsOn)).issubset(prior_call_ids):
                raise PlannerValidationError(
                    "tool binding and dependency sources must be prior calls"
                )
            declared_arguments = set(spec.inputSchema.get("properties", {}))
            if not bound_arguments.issubset(declared_arguments):
                raise PlannerValidationError(
                    "tool binding names must exist in the advertised input schema"
                )
            _validate_input_schema(
                call.arguments,
                spec.inputSchema,
                bound_arguments=bound_arguments,
                corpus_id=corpus.corpusId,
            )
            for limit_name in ("maxResults", "maxPaths"):
                requested_limit = call.arguments.get(limit_name)
                if (
                    isinstance(requested_limit, int)
                    and not isinstance(requested_limit, bool)
                    and requested_limit > self._policy.maxResultsPerTool
                ):
                    raise PlannerValidationError(
                        f'tool "{call.toolName}" requested a result limit above '
                        f"{self._policy.maxResultsPerTool}"
                    )
            _validate_literal_record_ids(
                call.arguments,
                trusted_ids=trusted_ids,
                bound_arguments=bound_arguments,
            )
            prior_call_ids.add(call.callId)


def _validate_literal_record_ids(
    arguments: Mapping[str, Any],
    *,
    trusted_ids: dict[SelectedRecordType, set[str]],
    bound_arguments: set[str],
) -> None:
    for name, value in arguments.items():
        if name in bound_arguments or name == "corpusId":
            continue
        if re.search(r"(?:Id|Ids)$", name):
            allowed_types = ARGUMENT_RECORD_TYPES.get(name)
            if allowed_types is None:
                raise PlannerValidationError(
                    f'unknown record-id argument "{name}" cannot use workspace trust'
                )
            values = value if isinstance(value, list) else [value]
            for record_id in values:
                if isinstance(record_id, str) and not any(
                    record_id in trusted_ids.get(record_type, set())
                    for record_type in allowed_types
                ):
                    raise PlannerValidationError(
                        f'argument "{name}" uses untrusted record identifier '
                        f'"{record_id}" or an incompatible selected record type'
                    )
        if isinstance(value, dict):
            _validate_literal_record_ids(
                value,
                trusted_ids=trusted_ids,
                bound_arguments=set(),
            )


def _validate_question_coherence(plan: InvestigationPlan) -> None:
    tool_names = {call.toolName for call in plan.plannedToolCalls}
    evidence_types = set(plan.requiredEvidenceTypes)
    if plan.questionType is QuestionType.ACTOR_KNOWLEDGE and not (
        plan.requiresKnowledgeState
        and RequiredEvidenceType.KNOWLEDGE_STATE in evidence_types
        and "get_actor_knowledge_state" in tool_names
    ):
        raise PlannerValidationError(
            "actor-knowledge plans require the knowledge-state flag, evidence, and tool"
        )
    if plan.questionType is QuestionType.COUNTEREVIDENCE and not (
        plan.requiresCounterevidence
        and RequiredEvidenceType.COUNTEREVIDENCE in evidence_types
        and _has_role_preserving_counterevidence_call(plan)
    ):
        raise PlannerValidationError(
            "counterevidence plans require the counterevidence flag, evidence, and a "
            "role-preserving counterevidence tool"
        )
    if plan.questionType is QuestionType.TIMELINE_ORDERING and not (
        plan.requiresTimeline
        and RequiredEvidenceType.TIMELINE in evidence_types
        and "get_timeline_context" in tool_names
    ):
        raise PlannerValidationError(
            "timeline-ordering plans require the timeline flag, evidence, and tool"
        )


def _has_role_preserving_counterevidence_call(plan: InvestigationPlan) -> bool:
    for call in plan.plannedToolCalls:
        if call.toolName in {
            "find_counterevidence",
            "get_claim_evidence",
            "get_relationship_evidence",
        }:
            return True
        if call.toolName == "search_passages":
            evidence_roles = call.arguments.get("evidenceRoles", [])
            if isinstance(evidence_roles, list) and "counterevidence" in evidence_roles:
                return True
    return False


def _validate_input_schema(
    arguments: Mapping[str, Any],
    schema: Mapping[str, Any],
    *,
    bound_arguments: set[str],
    corpus_id: str,
) -> None:
    candidate = dict(arguments)
    candidate["corpusId"] = corpus_id
    root = schema
    try:
        _validate_schema_value(candidate, schema, root, "$", bound_arguments)
    except ValueError as exc:
        raise PlannerValidationError(f"tool arguments fail advertised input schema: {exc}") from None


def _validate_schema_value(
    value: Any,
    schema: Mapping[str, Any],
    root: Mapping[str, Any],
    path: str,
    bound_arguments: set[str],
) -> None:
    if "$ref" in schema:
        target: Any = root
        for part in str(schema["$ref"]).removeprefix("#/").split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        _validate_schema_value(value, target, root, path, bound_arguments)
        return
    if "anyOf" in schema:
        for option in schema["anyOf"]:
            try:
                _validate_schema_value(value, option, root, path, bound_arguments)
                return
            except (ValueError, KeyError):
                pass
        raise ValueError(f"{path} matches none of the allowed shapes")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{path} is not an allowed enum value")

    expected = schema.get("type")
    if expected == "object":
        if not isinstance(value, dict):
            raise ValueError(f"{path} must be an object")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extras = set(value) - set(properties)
            if extras:
                raise ValueError(f"{path} contains unknown fields {sorted(extras)}")
        missing = set(schema.get("required", [])) - set(value) - bound_arguments
        if missing:
            raise ValueError(f"{path} is missing required fields {sorted(missing)}")
        for name, item in value.items():
            if name in properties:
                _validate_schema_value(item, properties[name], root, f"{path}.{name}", set())
        return
    if expected == "array":
        if not isinstance(value, list):
            raise ValueError(f"{path} must be an array")
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise ValueError(f"{path} has too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ValueError(f"{path} has too many items")
        for index, item in enumerate(value):
            _validate_schema_value(item, schema.get("items", {}), root, f"{path}[{index}]", set())
        return
    if expected == "string":
        if not isinstance(value, str):
            raise ValueError(f"{path} must be a string")
        if "minLength" in schema and len(value) < schema["minLength"]:
            raise ValueError(f"{path} is too short")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise ValueError(f"{path} is too long")
    elif expected == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"{path} must be an integer")
    elif expected == "number":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"{path} must be a number")
    elif expected == "boolean" and not isinstance(value, bool):
        raise ValueError(f"{path} must be a boolean")
    elif expected == "null" and value is not None:
        raise ValueError(f"{path} must be null")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ValueError(f"{path} is below its minimum")
        if "maximum" in schema and value > schema["maximum"]:
            raise ValueError(f"{path} exceeds its maximum")
