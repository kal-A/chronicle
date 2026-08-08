"""Typed, bounded, auditable tool discovery and invocation for one corpus."""

from __future__ import annotations

import time
import uuid
import warnings
from copy import deepcopy
from dataclasses import dataclass
from typing import Callable

from pydantic import BaseModel, ValidationError

from ...corpus.errors import CorpusError
from ...corpus.protocol import InvestigationCorpus
from ...workflow.hashing import stable_json_hash
from .contracts import (
    DEFAULT_TOOL_OUTPUT_CHARACTER_LIMIT,
    ToolCallRecord,
    ToolCallStatus,
    ToolExecutionContext,
    ToolSpec,
    utcnow,
)
from .errors import (
    CorpusMismatchError,
    CorpusRetrievalError,
    DuplicateToolNameError,
    InternalRetrievalError,
    MalformedToolInputError,
    MalformedToolOutputError,
    ResultLimitExceededError,
    ToolError,
    UnauthorizedToolError,
    UnknownToolError,
    UnsupportedCapabilityError,
)


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    version: str
    description: str
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    required_capabilities: frozenset[str]
    max_result_limit: int | None
    execute: Callable[[BaseModel, ToolExecutionContext, InvestigationCorpus], BaseModel]
    use_when: str = "Use when the tool description matches the current question."
    avoid_when: str = "Avoid when required IDs or corpus capabilities are unavailable."
    output_summary: str | None = None
    deterministic: bool = True
    current_corpus_only: bool = True


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        if definition.name in self._tools:
            raise DuplicateToolNameError(f'Tool "{definition.name}" is already registered')
        self._tools[definition.name] = definition

    def get(self, name: str) -> ToolDefinition:
        try:
            return self._tools[name]
        except KeyError:
            raise UnknownToolError(f'No tool registered with name "{name}"') from None

    def list(self) -> list[ToolDefinition]:
        """Planner-inspectable: name/version/description/schemas, without
        importing any tool's implementation module."""
        return [self._tools[name] for name in sorted(self._tools)]

    def list_specs(
        self,
        context: ToolExecutionContext | None = None,
        corpus: InvestigationCorpus | None = None,
    ) -> list[ToolSpec]:
        manifest = corpus.get_manifest() if corpus is not None else None
        if context is not None and corpus is not None:
            assert manifest is not None
            if corpus.corpus_id != context.corpusId or manifest.corpusId != context.corpusId:
                raise CorpusMismatchError("Tool specification context does not match the supplied corpus")

        specs: list[ToolSpec] = []
        for definition in self.list():
            if context is not None and context.allowedToolNames is not None:
                if definition.name not in context.allowedToolNames:
                    continue
            if manifest is not None and definition.required_capabilities - manifest.supportedCapabilities:
                continue
            advertised_limit = definition.max_result_limit
            if context is not None:
                advertised_limit = (
                    min(context.maximumResults, advertised_limit)
                    if advertised_limit is not None
                    else context.maximumResults
                )
            input_schema = deepcopy(definition.input_model.model_json_schema())
            if advertised_limit is not None:
                for limit_field in ("maxResults", "maxPaths"):
                    property_schema = input_schema.get("properties", {}).get(limit_field)
                    if property_schema is None:
                        continue
                    declared_maximum = property_schema.get("maximum")
                    property_schema["maximum"] = (
                        min(advertised_limit, declared_maximum)
                        if declared_maximum is not None
                        else advertised_limit
                    )
                    declared_default = property_schema.get("default")
                    if isinstance(declared_default, int):
                        property_schema["default"] = min(declared_default, advertised_limit)
            specs.append(
                ToolSpec(
                    name=definition.name,
                    version=definition.version,
                    description=definition.description,
                    inputSchema=input_schema,
                    outputSummary=definition.output_summary or definition.output_model.__name__,
                    requiredCapabilities=sorted(definition.required_capabilities),
                    maxResultLimit=advertised_limit,
                    maxOutputCharacters=(
                        context.maximumOutputCharacters
                        if context is not None
                        else DEFAULT_TOOL_OUTPUT_CHARACTER_LIMIT
                    ),
                    useWhen=definition.use_when,
                    avoidWhen=definition.avoid_when,
                    deterministic=definition.deterministic,
                    currentCorpusOnly=definition.current_corpus_only,
                )
            )
        return specs

    def invoke(
        self,
        name: str,
        raw_input: dict,
        context: ToolExecutionContext,
        corpus: InvestigationCorpus,
    ) -> tuple[BaseModel, ToolCallRecord]:
        started_at = utcnow()
        start_perf = time.perf_counter()
        input_hash = stable_json_hash(raw_input)
        call_id = uuid.uuid4().hex
        try:
            definition = self.get(name)

            if context.allowedToolNames is not None and name not in context.allowedToolNames:
                raise UnauthorizedToolError(f'Tool "{name}" is not in this context\'s allowed_tool_names')

            tool_input = definition.input_model.model_validate(raw_input)
            input_corpus_id = getattr(tool_input, "corpusId", None)
            manifest = corpus.get_manifest()
            corpus_ids = {
                "input": input_corpus_id,
                "context": context.corpusId,
                "corpus": corpus.corpus_id,
                "manifest": manifest.corpusId,
            }
            if len(set(corpus_ids.values())) != 1:
                rendered = ", ".join(f'{owner}="{value}"' for owner, value in corpus_ids.items())
                raise CorpusMismatchError(f'Tool "{name}" corpus binding mismatch: {rendered}')

            missing_capabilities = definition.required_capabilities - manifest.supportedCapabilities
            if missing_capabilities:
                raise UnsupportedCapabilityError(
                    f'Tool "{name}" requires capabilities {sorted(missing_capabilities)} '
                    f'not supported by corpus "{corpus.corpus_id}"'
                )

            requested_max = getattr(tool_input, "maxResults", None)
            requested_max_is_explicit = "maxResults" in tool_input.model_fields_set
            limits = [context.maximumResults]
            if definition.max_result_limit is not None:
                limits.append(definition.max_result_limit)
            effective_limit = min(limits)
            if (
                requested_max is not None
                and requested_max_is_explicit
                and requested_max > effective_limit
            ):
                raise ResultLimitExceededError(
                    f'Tool "{name}" requested {requested_max} results, '
                    f"exceeding the effective maximum of {effective_limit}"
                )

            output = definition.execute(tool_input, context, corpus)
            if not isinstance(output, definition.output_model):
                raise MalformedToolOutputError(
                    f'Tool "{name}" returned {type(output).__name__}, expected {definition.output_model.__name__}'
                )
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    raw_output = output.model_dump(mode="python")
                output = definition.output_model.model_validate(raw_output)
            except ValidationError:
                raise MalformedToolOutputError(
                    f'Tool "{name}" returned an invalid {definition.output_model.__name__}'
                ) from None
            output_count = _infer_result_count(output)
            output_limit = min(effective_limit, requested_max) if requested_max is not None else effective_limit
            if output_count is not None and output_count > output_limit:
                raise MalformedToolOutputError(
                    f'Tool "{name}" returned {output_count} results, '
                    f"exceeding the effective maximum of {output_limit}"
                )
            output_characters = len(output.model_dump_json())
            if output_characters > context.maximumOutputCharacters:
                raise MalformedToolOutputError(
                    f'Tool "{name}" returned {output_characters} characters, exceeding '
                    f"the context maximum of {context.maximumOutputCharacters}"
                )
        except ValidationError as exc:
            error = MalformedToolInputError(f'Tool "{name}" input failed validation: {exc}')
            raise _attach_failure_record(
                error,
                status=ToolCallStatus.REJECTED,
                name=name,
                version=locals().get("definition").version if "definition" in locals() else "unknown",
                context=context,
                input_hash=input_hash,
                call_id=call_id,
                started_at=started_at,
                start_perf=start_perf,
            ) from None
        except ToolError as error:
            status = _failure_status(error)
            raise _attach_failure_record(
                error,
                status=status,
                name=name,
                version=locals().get("definition").version if "definition" in locals() else "unknown",
                context=context,
                input_hash=input_hash,
                call_id=call_id,
                started_at=started_at,
                start_perf=start_perf,
            )
        except CorpusError as exc:
            error = CorpusRetrievalError(
                f'Tool "{name}" corpus retrieval failed: {exc}',
                corpus_error_type=type(exc).__name__,
            )
            raise _attach_failure_record(
                error,
                status=ToolCallStatus.REJECTED,
                name=name,
                version=locals().get("definition").version if "definition" in locals() else "unknown",
                context=context,
                input_hash=input_hash,
                call_id=call_id,
                started_at=started_at,
                start_perf=start_perf,
            ) from None
        except Exception:  # noqa: BLE001 -- deliberately broad: never leak raw details
            error = InternalRetrievalError(f'Tool "{name}" failed unexpectedly')
            raise _attach_failure_record(
                error,
                status=ToolCallStatus.FAILED,
                name=name,
                version=locals().get("definition").version if "definition" in locals() else "unknown",
                context=context,
                input_hash=input_hash,
                call_id=call_id,
                started_at=started_at,
                start_perf=start_perf,
            ) from None

        completed_at = utcnow()
        output_hash = stable_json_hash(output.model_dump(mode="json"))

        record = ToolCallRecord(
            toolCallId=call_id,
            agentRunId=context.agentRunId,
            toolName=definition.name,
            toolVersion=definition.version,
            corpusId=context.corpusId,
            inputHash=input_hash,
            outputHash=output_hash,
            status=ToolCallStatus.SUCCEEDED,
            attemptCount=1,
            startedAt=started_at,
            completedAt=completed_at,
            latencyMs=(time.perf_counter() - start_perf) * 1000,
            resultCount=_infer_result_count(output),
        )
        return output, record


def _infer_result_count(output: BaseModel) -> int | None:
    returned_count = getattr(output, "returnedCount", None)
    if isinstance(returned_count, int):
        return returned_count
    for field_name in (
        "hits",
        "results",
        "paths",
        "items",
        "evidenceLinks",
        "events",
        "entries",
        "knowledgeStates",
        "places",
        "mapScenes",
    ):
        value = getattr(output, field_name, None)
        if isinstance(value, list):
            return len(value)
    return None


def _failure_status(error: ToolError) -> ToolCallStatus:
    if isinstance(error, UnsupportedCapabilityError):
        return ToolCallStatus.UNSUPPORTED
    if isinstance(error, (InternalRetrievalError, MalformedToolOutputError)):
        return ToolCallStatus.FAILED
    return ToolCallStatus.REJECTED


def _attach_failure_record(
    error: ToolError,
    *,
    status: ToolCallStatus,
    name: str,
    version: str,
    context: ToolExecutionContext,
    input_hash: str,
    call_id: str,
    started_at,
    start_perf: float,
) -> ToolError:
    return error.with_call_record(
        _build_failure_record(
            error=error,
            status=status,
            name=name,
            version=version,
            context=context,
            input_hash=input_hash,
            call_id=call_id,
            started_at=started_at,
            start_perf=start_perf,
        )
    )


def _build_failure_record(
    *,
    error: Exception,
    status: ToolCallStatus,
    name: str,
    version: str,
    context: ToolExecutionContext,
    input_hash: str,
    call_id: str,
    started_at,
    start_perf: float,
) -> ToolCallRecord:
    completed_at = utcnow()
    return ToolCallRecord(
        toolCallId=call_id,
        agentRunId=context.agentRunId,
        toolName=name,
        toolVersion=version,
        corpusId=context.corpusId,
        inputHash=input_hash,
        status=status,
        attemptCount=1,
        startedAt=started_at,
        completedAt=completed_at,
        latencyMs=(time.perf_counter() - start_perf) * 1000,
        errorType=type(error).__name__,
        errorMessage=str(error),
    )
