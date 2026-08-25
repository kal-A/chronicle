"""Deterministic, bounded execution of E3 investigation plans over E2 tools."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from typing import Callable, Iterable

from pydantic import BaseModel, ValidationError

from ...corpus.contracts import EvidenceLinkProjection
from ...corpus.protocol import InvestigationCorpus
from ...storage.agent_run_store import AgentRunStore
from ...workflow.hashing import stable_json_hash
from ..contracts.plan import InvestigationPlan, PlannedToolCall, PlanDisposition
from ..contracts.retrieval import RetrievalBundle, RetrievedReferenceIndex, ToolResultEnvelope
from ..contracts.run import AgentStageName, AgentStageRecord, AgentStageStatus
from ..tools.contracts import ToolCallRecord, ToolCallStatus, ToolExecutionContext
from ..tools.errors import ToolError
from ..tools.registry import ToolDefinition, ToolRegistry
from .policies import AgentExecutionPolicy


@dataclass(frozen=True)
class RetrievalExecution:
    """One runner result, with the shared artifacts kept independently persistable."""

    bundle: RetrievalBundle
    stageRecord: AgentStageRecord


class PlanExecutionValidationError(ValueError):
    """The complete plan cannot be safely dispatched against this corpus."""


_RECORD_ID_FIELDS: dict[str, tuple[str, ...]] = {
    "passage": ("passageId", "passageIds"),
    "source": ("sourceId", "sourceIds"),
    "document": ("documentId", "documentIds"),
    "claim": ("claimId", "claimIds"),
    "relationship": ("relationshipId", "relationshipIds"),
    "event": ("eventId", "eventIds"),
    "entity": ("entityId", "entityIds", "fromId", "toId", "startNodeId"),
    "knowledge_state": ("knowledgeStateId", "knowledgeStateIds"),
    "place": ("placeId", "placeIds"),
    "map_scene": ("mapSceneId", "mapSceneIds", "sceneId", "sceneIds"),
}

_INDEX_FIELDS: dict[str, str] = {
    "passage": "passageIds",
    "source": "sourceIds",
    "document": "documentIds",
    "claim": "claimIds",
    "relationship": "relationshipIds",
    "event": "eventIds",
    "knowledge_state": "knowledgeStateIds",
    "place": "placeIds",
    "map_scene": "mapSceneIds",
}


class InvestigationRunner:
    def __init__(
        self,
        registry: ToolRegistry,
        *,
        store: AgentRunStore | None = None,
        policy: AgentExecutionPolicy | None = None,
        allowed_tool_names: Iterable[str] | None = None,
        utc_clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.registry = registry
        self.store = store
        self.policy = policy or AgentExecutionPolicy()
        registered = {definition.name for definition in registry.list()}
        self.allowed_tool_names = frozenset(
            registered if allowed_tool_names is None else allowed_tool_names
        )
        self.utc_clock = utc_clock or _utcnow
        self._default_deadlines_by_run: dict[str, datetime] = {}

    def execute_initial(
        self,
        plan: InvestigationPlan,
        corpus: InvestigationCorpus,
        *,
        run_deadline_at: datetime | None = None,
    ) -> RetrievalExecution:
        started_at = self._now()
        deadline_at = self._resolve_deadline(plan.runId, run_deadline_at, started_at)
        try:
            self._validate_identity(plan, corpus)
        except PlanExecutionValidationError as exc:
            return self._rejected(
                plan, corpus, started_at, deadline_at=deadline_at, round_number=0, error=str(exc)
            )
        if plan.disposition is PlanDisposition.ABSTAIN:
            bundle = _empty_bundle(plan, partial=False)
            return self._execution(
                plan,
                bundle,
                started_at,
                round_number=0,
                status=AgentStageStatus.ABSTAINED,
                errors=[plan.unsupportedReason] if plan.unsupportedReason else [],
                calls=[],
                existing=None,
                corpus=corpus,
                deadline_at=deadline_at,
            )
        try:
            self._validate_plan(plan, corpus, identity_validated=True)
        except PlanExecutionValidationError as exc:
            return self._rejected(
                plan, corpus, started_at, deadline_at=deadline_at, round_number=0, error=str(exc)
            )

        return self._execute_calls(
            plan,
            corpus,
            calls=plan.plannedToolCalls,
            existing=None,
            round_number=0,
            started_at=started_at,
            deadline_at=deadline_at,
        )

    def execute_follow_up(
        self,
        plan: InvestigationPlan,
        follow_up_call: PlannedToolCall,
        corpus: InvestigationCorpus,
        existing_bundle: RetrievalBundle,
        *,
        run_deadline_at: datetime | None = None,
    ) -> RetrievalExecution:
        started_at = self._now()
        deadline_at = self._resolve_deadline(plan.runId, run_deadline_at, started_at)
        try:
            self._validate_follow_up(plan, follow_up_call, corpus, existing_bundle)
        except PlanExecutionValidationError as exc:
            return self._execution(
                plan,
                existing_bundle,
                started_at,
                round_number=1,
                status=AgentStageStatus.REJECTED,
                errors=[_bounded_error(exc)],
                calls=[follow_up_call],
                existing=existing_bundle,
                corpus=corpus,
                deadline_at=deadline_at,
            )
        return self._execute_calls(
            plan,
            corpus,
            calls=[follow_up_call],
            existing=existing_bundle,
            round_number=1,
            started_at=started_at,
            deadline_at=deadline_at,
        )

    def _validate_plan(
        self,
        plan: InvestigationPlan,
        corpus: InvestigationCorpus,
        *,
        identity_validated: bool = False,
    ) -> None:
        if not identity_validated:
            self._validate_identity(plan, corpus)
        if len(plan.plannedToolCalls) > self.policy.maxInitialToolCalls:
            raise PlanExecutionValidationError("plan exceeds the initial tool-call budget")
        self._preflight_calls(plan.plannedToolCalls, corpus, prior_calls=[])

    def _validate_follow_up(
        self,
        plan: InvestigationPlan,
        call: PlannedToolCall,
        corpus: InvestigationCorpus,
        bundle: RetrievalBundle,
    ) -> None:
        self._validate_identity(plan, corpus)
        if plan.disposition is PlanDisposition.ABSTAIN:
            raise PlanExecutionValidationError("an abstaining plan cannot request follow-up retrieval")
        if bundle.runId != plan.runId or bundle.planId != plan.planId or bundle.corpusId != plan.corpusId:
            raise PlanExecutionValidationError("existing retrieval bundle does not match this plan")
        if self.policy.maxFollowUpRounds < 1 or self.policy.maxFollowUpToolCalls < 1:
            raise PlanExecutionValidationError("follow-up retrieval is disabled by execution policy")
        follow_up_count = sum(item.round == 1 for item in bundle.results)
        if follow_up_count >= self.policy.maxFollowUpToolCalls:
            raise PlanExecutionValidationError("the single follow-up round has already been used")
        if len(bundle.results) >= self.policy.maxTotalToolCalls:
            raise PlanExecutionValidationError("the total tool-call budget is exhausted")
        if call.callId in {item.plannedCallId for item in bundle.results}:
            raise PlanExecutionValidationError("follow-up callId must be unique")
        prior = [(item.plannedCallId, self.registry.get(item.callRecord.toolName)) for item in bundle.results]
        self._preflight_calls([call], corpus, prior_calls=prior)

    def _validate_identity(self, plan: InvestigationPlan, corpus: InvestigationCorpus) -> None:
        manifest = corpus.get_manifest()
        if corpus.corpus_id != plan.corpusId or manifest.corpusId != plan.corpusId:
            raise PlanExecutionValidationError("plan, corpus, and manifest corpus IDs must match")

    def _preflight_calls(
        self,
        calls: list[PlannedToolCall],
        corpus: InvestigationCorpus,
        *,
        prior_calls: list[tuple[str, ToolDefinition]],
    ) -> None:
        manifest = corpus.get_manifest()
        definitions: dict[str, ToolDefinition] = {call_id: definition for call_id, definition in prior_calls}
        seen_ids = set(definitions)
        for call in calls:
            if call.toolName not in self.allowed_tool_names:
                raise PlanExecutionValidationError(f'tool "{call.toolName}" is not allowed')
            try:
                definition = self.registry.get(call.toolName)
            except ToolError as exc:
                raise PlanExecutionValidationError(str(exc)) from None
            missing = definition.required_capabilities - manifest.supportedCapabilities
            if missing:
                raise PlanExecutionValidationError(
                    f'tool "{call.toolName}" requires unavailable capabilities {sorted(missing)}'
                )
            dependencies = set(call.dependsOn) | {binding.sourceCallId for binding in call.bindings}
            if not dependencies.issubset(seen_ids):
                raise PlanExecutionValidationError("tool-call dependencies must precede the dependent call")
            raw_input = dict(call.arguments)
            if "corpusId" in raw_input:
                raise PlanExecutionValidationError("corpusId is runner-owned")
            self._apply_static_caps(raw_input, definition)
            self._preview_bindings(raw_input, call, definition, definitions)
            raw_input["corpusId"] = corpus.corpus_id
            try:
                definition.input_model.model_validate(raw_input)
            except ValidationError as exc:
                raise PlanExecutionValidationError(
                    f'tool "{call.toolName}" input is invalid: {exc.errors(include_url=False)}'
                ) from None
            definitions[call.callId] = definition
            seen_ids.add(call.callId)

    def _apply_static_caps(self, raw_input: dict, definition: ToolDefinition) -> None:
        for field_name in ("maxResults", "maxPaths"):
            if field_name not in definition.input_model.model_fields:
                continue
            requested = raw_input.get(field_name)
            if isinstance(requested, int) and requested > self.policy.maxResultsPerTool:
                raise PlanExecutionValidationError(
                    f"{field_name} exceeds the per-tool result budget of {self.policy.maxResultsPerTool}"
                )
            if requested is None:
                raw_input[field_name] = self.policy.maxResultsPerTool

    def _preview_bindings(
        self,
        raw_input: dict,
        call: PlannedToolCall,
        definition: ToolDefinition,
        source_definitions: dict[str, ToolDefinition],
    ) -> None:
        grouped: dict[str, list[str]] = {}
        for binding in call.bindings:
            if binding.argumentName == "corpusId" or binding.argumentName not in definition.input_model.model_fields:
                raise PlanExecutionValidationError(f'unknown or runner-owned binding target "{binding.argumentName}"')
            if binding.argumentName in call.arguments:
                raise PlanExecutionValidationError("a bound argument cannot also have a literal value")
            if binding.recordType not in _RECORD_ID_FIELDS:
                raise PlanExecutionValidationError(f'unsupported binding record type "{binding.recordType}"')
            source = source_definitions[binding.sourceCallId]
            schema_text = json.dumps(source.output_model.model_json_schema())
            if not any(field in schema_text for field in _RECORD_ID_FIELDS[binding.recordType]):
                raise PlanExecutionValidationError(
                    f'call "{binding.sourceCallId}" cannot provide {binding.recordType} records'
                )
            grouped.setdefault(binding.argumentName, []).append("bound-record-id")
        for argument_name, values in grouped.items():
            raw_input[argument_name] = values[0] if len(values) == 1 else values

    def _execute_calls(
        self,
        plan: InvestigationPlan,
        corpus: InvestigationCorpus,
        *,
        calls: list[PlannedToolCall],
        existing: RetrievalBundle | None,
        round_number: int,
        started_at: datetime,
        deadline_at: datetime,
    ) -> RetrievalExecution:
        results = list(existing.results) if existing is not None else []
        output_by_call = {
            item.plannedCallId: item.output for item in results if item.output is not None
        }
        successful_ids = set(output_by_call)
        stage_records: list[ToolCallRecord] = []
        errors: list[str] = []
        interrupted = False
        partial = bool(existing.partial) if existing is not None else False
        truncated = bool(existing.truncated) if existing is not None else False
        for call in calls:
            if self._now() >= deadline_at:
                errors.append("retrieval deadline exhausted before the next tool call")
                interrupted = partial = truncated = True
                break
            if not set(call.dependsOn).issubset(successful_ids):
                errors.append(f'call "{call.callId}" skipped because a dependency did not succeed')
                partial = True
                break
            current_characters = sum(item.serializedCharacters for item in results)
            current_count = sum(item.returnedCount for item in results)
            remaining_characters = self.policy.maxAggregateRetrievalCharacters - current_characters
            remaining_count = self.policy.maxAggregateResults - current_count
            if (
                len(results) >= self.policy.maxTotalToolCalls
                or remaining_characters < 1_000
                or remaining_count < 1
            ):
                errors.append("aggregate retrieval budget exhausted before the next tool call")
                partial = truncated = True
                break

            definition = self.registry.get(call.toolName)
            try:
                raw_input = self._resolve_input(call, definition, output_by_call, corpus.corpus_id)
            except PlanExecutionValidationError as exc:
                errors.append(_bounded_error(exc))
                partial = True
                break
            effective_results = min(self.policy.maxResultsPerTool, remaining_count)
            for field_name in ("maxResults", "maxPaths"):
                if field_name in definition.input_model.model_fields:
                    raw_input[field_name] = min(raw_input.get(field_name, effective_results), effective_results)
            input_hash = stable_json_hash(raw_input)
            sequence = len(results)
            execution_identity_hash = _execution_identity_hash(
                plan,
                call,
                corpus,
                definition,
                sequence,
                results,
            )
            resumed = None
            if self.store is not None:
                resumed = self.store.load_successful_tool_result(
                    plan.runId,
                    sequence,
                    definition.output_model,
                    expected_input_hash=input_hash,
                    expected_tool_name=call.toolName,
                    expected_tool_version=definition.version,
                    expected_corpus_id=plan.corpusId,
                    expected_execution_identity_hash=execution_identity_hash,
                )
            if resumed is not None:
                resumed_record, resumed_output = resumed
                resumed_characters = len(resumed_output.model_dump_json())
                resumed_count = (
                    resumed_record.resultCount
                    if isinstance(resumed_record.resultCount, int)
                    else 0
                )
                if (
                    resumed_count > effective_results
                    or resumed_count > remaining_count
                    or resumed_characters > self.policy.maxCharactersPerToolOutput
                    or resumed_characters > remaining_characters
                ):
                    resumed = None
            if resumed is not None:
                record, output = resumed
            else:
                context = ToolExecutionContext(
                    corpusId=plan.corpusId,
                    agentRunId=plan.runId,
                    requestedByRole="planner",
                    allowedToolNames=set(self.allowed_tool_names),
                    maximumResults=effective_results,
                    maximumOutputCharacters=min(
                        self.policy.maxCharactersPerToolOutput,
                        remaining_characters,
                    ),
                )
                try:
                    output, record = self.registry.invoke(call.toolName, raw_input, context, corpus)
                except ToolError as exc:
                    if exc.callRecord is None:
                        errors.append(f'tool "{call.toolName}" failed without an audit record')
                        partial = True
                        break
                    record = exc.callRecord
                    stage_records.append(record)
                    results.append(
                        ToolResultEnvelope(
                            plannedCallId=call.callId,
                            round=round_number,
                            purposeCode=call.purposeCode,
                            resolvedInputHash=record.inputHash,
                            callRecord=record,
                            output=None,
                            serializedCharacters=0,
                            returnedCount=0,
                        )
                    )
                    errors.append(_bounded_error(exc))
                    partial = True
                    if self._now() >= deadline_at:
                        errors.append("retrieval deadline exhausted during the tool call")
                        interrupted = partial = truncated = True
                        break
                    continue
                if self.store is not None:
                    self.store.save_tool_result(
                        plan.runId,
                        sequence,
                        record,
                        output,
                        execution_identity_hash=execution_identity_hash,
                    )

            serialized_characters = len(output.model_dump_json())
            returned_count = record.resultCount if isinstance(record.resultCount, int) else 0
            output_truncated = bool(getattr(output, "truncated", False))
            envelope = ToolResultEnvelope(
                plannedCallId=call.callId,
                round=round_number,
                purposeCode=call.purposeCode,
                resolvedInputHash=input_hash,
                callRecord=record,
                output=output,
                serializedCharacters=serialized_characters,
                returnedCount=returned_count,
                truncated=output_truncated,
            )
            results.append(envelope)
            stage_records.append(record)
            output_by_call[call.callId] = output
            successful_ids.add(call.callId)
            truncated = truncated or output_truncated
            if self._now() >= deadline_at:
                errors.append("retrieval deadline exhausted during the tool call")
                interrupted = partial = truncated = True
                break

        bundle, index_truncated = self._build_bundle(plan, results, partial=partial, truncated=truncated)
        if index_truncated and not bundle.truncated:
            bundle = bundle.model_copy(update={"truncated": True})
        successful_count = sum(record.status is ToolCallStatus.SUCCEEDED for record in stage_records)
        failed_count = len(stage_records) - successful_count
        usable_result_count = sum(
            item.callRecord.status is ToolCallStatus.SUCCEEDED for item in bundle.results
        )
        if interrupted:
            status = AgentStageStatus.INTERRUPTED
        elif failed_count or errors:
            status = AgentStageStatus.PARTIAL if usable_result_count else AgentStageStatus.FAILED
        else:
            status = AgentStageStatus.SUCCEEDED
        return self._execution(
            plan,
            bundle,
            started_at,
            round_number=round_number,
            status=status,
            tool_calls=stage_records,
            errors=errors,
            calls=calls,
            existing=existing,
            corpus=corpus,
            deadline_at=deadline_at,
        )

    def _resolve_input(
        self,
        call: PlannedToolCall,
        definition: ToolDefinition,
        output_by_call: dict[str, BaseModel],
        corpus_id: str,
    ) -> dict:
        raw_input = dict(call.arguments)
        grouped: dict[str, list[str]] = {}
        for binding in call.bindings:
            output = output_by_call.get(binding.sourceCallId)
            if output is None:
                raise PlanExecutionValidationError(
                    f'call "{binding.sourceCallId}" has no successful output for binding'
                )
            values = _record_ids(output, binding.recordType)
            if binding.ordinal >= len(values):
                raise PlanExecutionValidationError(
                    f'binding ordinal {binding.ordinal} exceeds returned {binding.recordType} records'
                )
            grouped.setdefault(binding.argumentName, []).append(values[binding.ordinal])
        for argument_name, values in grouped.items():
            raw_input[argument_name] = values[0] if len(values) == 1 else values
        self._apply_static_caps(raw_input, definition)
        raw_input["corpusId"] = corpus_id
        return raw_input

    def _build_bundle(
        self,
        plan: InvestigationPlan,
        results: list[ToolResultEnvelope],
        *,
        partial: bool,
        truncated: bool,
    ) -> tuple[RetrievalBundle, bool]:
        index, index_truncated = _reference_index(
            [item.output for item in results if item.output is not None]
        )
        bundle = RetrievalBundle(
            runId=plan.runId,
            planId=plan.planId,
            corpusId=plan.corpusId,
            results=results,
            referenceIndex=index,
            totalResultCount=sum(item.returnedCount for item in results),
            serializedCharacters=sum(item.serializedCharacters for item in results),
            truncated=truncated or index_truncated,
            partial=partial,
            failedCallCount=sum(
                item.callRecord.status is not ToolCallStatus.SUCCEEDED for item in results
            ),
        )
        return bundle, index_truncated

    def _rejected(
        self,
        plan: InvestigationPlan,
        corpus: InvestigationCorpus,
        started_at: datetime,
        *,
        deadline_at: datetime,
        round_number: int,
        error: str,
    ) -> RetrievalExecution:
        return self._execution(
            plan,
            _empty_bundle(plan, partial=True),
            started_at,
            round_number=round_number,
            status=AgentStageStatus.REJECTED,
            errors=[_bounded_error(error)],
            calls=list(plan.plannedToolCalls),
            existing=None,
            corpus=corpus,
            deadline_at=deadline_at,
        )

    def _execution(
        self,
        plan: InvestigationPlan,
        bundle: RetrievalBundle,
        started_at: datetime,
        *,
        round_number: int,
        status: AgentStageStatus,
        tool_calls: list[ToolCallRecord] | None = None,
        errors: list[str] | None = None,
        calls: list[PlannedToolCall],
        existing: RetrievalBundle | None,
        corpus: InvestigationCorpus,
        deadline_at: datetime,
    ) -> RetrievalExecution:
        completed_at = self._now()
        stage = AgentStageRecord(
            runId=plan.runId,
            stageName=AgentStageName.RETRIEVAL,
            round=round_number,
            status=status,
            startedAt=started_at,
            completedAt=completed_at,
            latencyMs=max(0.0, (completed_at - started_at).total_seconds() * 1_000),
            inputHash=stable_json_hash(
                _stage_input_payload(
                    plan,
                    calls,
                    round_number,
                    existing,
                    corpus,
                    self.registry,
                    deadline_at,
                )
            ),
            outputHash=stable_json_hash(bundle.model_dump(mode="json")),
            toolCalls=tool_calls or [],
            errors=[_bounded_error(error) for error in (errors or [])],
        )
        return RetrievalExecution(bundle=bundle, stageRecord=stage)

    def _now(self) -> datetime:
        value = self.utc_clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("utc_clock must return a timezone-aware datetime")
        return value.astimezone(timezone.utc)

    def _resolve_deadline(
        self,
        run_id: str,
        explicit: datetime | None,
        started_at: datetime,
    ) -> datetime:
        policy_ceiling = started_at + timedelta(seconds=self.policy.deadlineSeconds)
        if explicit is not None:
            if explicit.tzinfo is None or explicit.utcoffset() is None:
                raise ValueError("run_deadline_at must be timezone-aware UTC")
            candidate = min(explicit.astimezone(timezone.utc), policy_ceiling)
        else:
            candidate = policy_ceiling
        existing = self._default_deadlines_by_run.get(run_id)
        resolved = min(existing, candidate) if existing is not None else candidate
        self._default_deadlines_by_run[run_id] = resolved
        return resolved


def _stage_input_payload(
    plan: InvestigationPlan,
    calls: list[PlannedToolCall],
    round_number: int,
    existing: RetrievalBundle | None,
    corpus: InvestigationCorpus,
    registry: ToolRegistry,
    deadline_at: datetime,
) -> dict:
    manifest = corpus.get_manifest()
    resolved_tools: list[dict[str, str | None]] = []
    for call in calls:
        try:
            definition = registry.get(call.toolName)
        except ToolError:
            resolved_tools.append({"name": call.toolName, "version": None})
        else:
            resolved_tools.append({"name": definition.name, "version": definition.version})
    return {
        "plan": plan.model_dump(mode="json"),
        "round": round_number,
        "calls": [call.model_dump(mode="json") for call in calls],
        "existingResultPrefix": _result_identity_prefix(existing.results if existing else []),
        "corpusPackageHash": manifest.packageHash,
        "corpusSchemaVersion": manifest.schemaVersion,
        "resolvedTools": resolved_tools,
        "runDeadlineAt": deadline_at.isoformat(),
    }


def _execution_identity_hash(
    plan: InvestigationPlan,
    call: PlannedToolCall,
    corpus: InvestigationCorpus,
    definition: ToolDefinition,
    sequence: int,
    prior_results: list[ToolResultEnvelope],
) -> str:
    manifest = corpus.get_manifest()
    return stable_json_hash(
        {
            "plan": plan.model_dump(mode="json"),
            "call": call.model_dump(mode="json"),
            "corpusPackageHash": manifest.packageHash,
            "corpusSchemaVersion": manifest.schemaVersion,
            "toolVersion": definition.version,
            "sequence": sequence,
            "priorResultOutputHashPrefix": [
                item.callRecord.outputHash for item in prior_results
            ],
        }
    )


def _result_identity_prefix(results: list[ToolResultEnvelope]) -> list[dict]:
    return [
        {
            "plannedCallId": item.plannedCallId,
            "round": item.round,
            "toolName": item.callRecord.toolName,
            "toolVersion": item.callRecord.toolVersion,
            "inputHash": item.callRecord.inputHash,
            "outputHash": item.callRecord.outputHash,
            "status": item.callRecord.status.value,
        }
        for item in results
    ]


def _empty_bundle(plan: InvestigationPlan, *, partial: bool) -> RetrievalBundle:
    return RetrievalBundle(
        runId=plan.runId,
        planId=plan.planId,
        corpusId=plan.corpusId,
        partial=partial,
    )


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _bounded_error(error: object) -> str:
    rendered = str(error).replace("\r", " ").replace("\n", " ")
    return rendered[:500] or type(error).__name__


def _walk(value):
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _walk(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk(nested)


def _record_ids(output: BaseModel, record_type: str) -> list[str]:
    fields = set(_RECORD_ID_FIELDS[record_type])
    found: list[str] = []
    for node in _walk(output.model_dump(mode="json")):
        target_type = node.get("targetType")
        target_id = node.get("targetId")
        if target_type == record_type and isinstance(target_id, str):
            found.append(target_id)
        for key in fields:
            value = node.get(key)
            if isinstance(value, str):
                found.append(value)
            elif isinstance(value, list):
                found.extend(item for item in value if isinstance(item, str))
    return list(dict.fromkeys(found))


def _reference_index(outputs: list[BaseModel]) -> tuple[RetrievedReferenceIndex, bool]:
    all_ids: dict[str, list[str]] = {field: [] for field in _INDEX_FIELDS.values()}
    evidence_links: dict[str, EvidenceLinkProjection] = {}
    for output in outputs:
        for record_type, index_field in _INDEX_FIELDS.items():
            all_ids[index_field].extend(_record_ids(output, record_type))
        for node in _walk(output.model_dump(mode="json")):
            required = {
                "evidenceLinkId", "targetType", "targetId", "role", "reviewStatus",
                "visibility", "passageId", "documentId", "sourceId",
            }
            if required.issubset(node):
                try:
                    link = EvidenceLinkProjection.model_validate(node)
                except ValidationError:
                    continue
                evidence_links.setdefault(link.evidenceLinkId, link)

    truncated = len(evidence_links) > 16
    index_values: dict[str, tuple[str, ...]] = {}
    for field, values in all_ids.items():
        canonical = sorted(set(values))
        truncated = truncated or len(canonical) > 16
        index_values[field] = tuple(canonical[:16])
    return (
        RetrievedReferenceIndex(
            evidenceLinks=list(evidence_links.values())[:16],
            **index_values,
        ),
        truncated,
    )


__all__ = ["InvestigationRunner", "PlanExecutionValidationError", "RetrievalExecution"]
