"""ToolRegistry: registration, duplicate rejection, input/output
validation, corpus-capability/authorization checks, call-record
metadata. Uses a small dummy tool, not the real 10, to isolate the
registry's own mechanics from any one tool's behavior."""

from __future__ import annotations

import json

import pytest
from pydantic import BaseModel, ConfigDict, Field

from chronicle.ai.tools.contracts import (
    DEFAULT_TOOL_OUTPUT_CHARACTER_LIMIT,
    DEFAULT_TOOL_RESULT_LIMIT,
    MAX_TOOL_OUTPUT_CHARACTER_LIMIT,
    MAX_TOOL_RESULT_LIMIT,
    ToolCallStatus,
    ToolExecutionContext,
)
from chronicle.ai.tools.errors import (
    CorpusRetrievalError,
    CorpusMismatchError,
    DuplicateToolNameError,
    InternalRetrievalError,
    MalformedToolInputError,
    MalformedToolOutputError,
    ResultLimitExceededError,
    UnauthorizedToolError,
    UnknownToolError,
    UnsupportedCapabilityError,
)
from chronicle.corpus.errors import UnknownRecordError
from chronicle.ai.tools.registry import ToolDefinition, ToolRegistry


class _EchoInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpusId: str
    text: str = Field(min_length=1)
    maxResults: int | None = None


class _EchoOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    results: list[str]
    returnedCount: int | None = None


def _echo(tool_input: _EchoInput, context, corpus) -> _EchoOutput:
    return _EchoOutput(results=[tool_input.text])


def _make_definition(
    name="echo",
    required_capabilities=frozenset(),
    max_result_limit=None,
    execute=_echo,
) -> ToolDefinition:
    return ToolDefinition(
        name=name,
        version="test-v1",
        description="Echoes its input text back.",
        input_model=_EchoInput,
        output_model=_EchoOutput,
        required_capabilities=required_capabilities,
        max_result_limit=max_result_limit,
        execute=execute,
    )


def test_register_and_get():
    registry = ToolRegistry()
    definition = _make_definition()
    registry.register(definition)
    assert registry.get("echo") is definition


def test_duplicate_name_raises():
    registry = ToolRegistry()
    registry.register(_make_definition())
    with pytest.raises(DuplicateToolNameError):
        registry.register(_make_definition())


def test_get_unknown_tool_raises():
    registry = ToolRegistry()
    with pytest.raises(UnknownToolError):
        registry.get("no-such-tool")


def test_list_is_sorted_by_name():
    registry = ToolRegistry()
    registry.register(_make_definition(name="zzz"))
    registry.register(_make_definition(name="aaa"))
    assert [d.name for d in registry.list()] == ["aaa", "zzz"]


def test_list_specs_returns_compact_serializable_model_facing_contract():
    registry = ToolRegistry()
    registry.register(_make_definition())

    specs = registry.list_specs()

    assert [spec.name for spec in specs] == ["echo"]
    assert specs[0].deterministic is True
    assert specs[0].currentCorpusOnly is True
    assert specs[0].inputSchema["type"] == "object"
    assert specs[0].outputSummary == "_EchoOutput"
    json.dumps([spec.model_dump(mode="json") for spec in specs])


def test_list_specs_reports_the_effective_context_result_bound(corpus, corpus_id):
    registry = ToolRegistry()
    registry.register(_make_definition(max_result_limit=10))
    context = ToolExecutionContext(corpusId=corpus_id, maximumResults=3)

    spec = registry.list_specs(context, corpus)[0]

    assert spec.maxResultLimit == 3


def test_execution_context_has_conservative_bounded_default():
    context = ToolExecutionContext(corpusId="corpus-a")
    assert context.maximumResults == DEFAULT_TOOL_RESULT_LIMIT
    assert context.maximumOutputCharacters == DEFAULT_TOOL_OUTPUT_CHARACTER_LIMIT
    with pytest.raises(ValueError):
        ToolExecutionContext(corpusId="corpus-a", maximumResults=MAX_TOOL_RESULT_LIMIT + 1)
    with pytest.raises(ValueError):
        ToolExecutionContext(
            corpusId="corpus-a",
            maximumOutputCharacters=MAX_TOOL_OUTPUT_CHARACTER_LIMIT + 1,
        )


def test_invoke_succeeds_and_returns_a_call_record(corpus, corpus_id):
    registry = ToolRegistry()
    registry.register(_make_definition())
    context = ToolExecutionContext(corpusId=corpus_id)

    output, record = registry.invoke("echo", {"corpusId": corpus_id, "text": "hi"}, context, corpus)

    assert output.results == ["hi"]
    assert record.status == ToolCallStatus.SUCCEEDED
    assert record.toolName == "echo"
    assert record.corpusId == corpus_id
    assert record.attemptCount == 1
    assert record.latencyMs is not None and record.latencyMs >= 0
    assert record.resultCount == 1


def test_call_record_prefers_explicit_returned_count(corpus, corpus_id):
    def _explicit_count(tool_input, context, corpus):
        return _EchoOutput(results=[], returnedCount=3)

    registry = ToolRegistry()
    registry.register(_make_definition(execute=_explicit_count))
    _, record = registry.invoke(
        "echo",
        {"corpusId": corpus_id, "text": "hi"},
        ToolExecutionContext(corpusId=corpus_id),
        corpus,
    )

    assert record.resultCount == 3


def test_invoke_unknown_tool_raises(corpus, corpus_id):
    registry = ToolRegistry()
    context = ToolExecutionContext(corpusId=corpus_id)
    with pytest.raises(UnknownToolError):
        registry.invoke("no-such-tool", {"corpusId": corpus_id, "text": "hi"}, context, corpus)


def test_invoke_malformed_input_raises(corpus, corpus_id):
    registry = ToolRegistry()
    registry.register(_make_definition())
    context = ToolExecutionContext(corpusId=corpus_id)
    with pytest.raises(MalformedToolInputError):
        registry.invoke("echo", {"corpusId": corpus_id}, context, corpus)  # missing required "text"


def test_invoke_corpus_mismatch_raises(corpus, corpus_id, other_corpus_id):
    registry = ToolRegistry()
    registry.register(_make_definition())
    context = ToolExecutionContext(corpusId=corpus_id)
    with pytest.raises(CorpusMismatchError):
        registry.invoke("echo", {"corpusId": other_corpus_id, "text": "hi"}, context, corpus)


def test_invoke_rejects_a_different_actual_corpus(corpus_registry, corpus_id, other_corpus_id):
    registry = ToolRegistry()
    registry.register(_make_definition())
    context = ToolExecutionContext(corpusId=corpus_id)
    wrong_corpus = corpus_registry.get_corpus(other_corpus_id)

    with pytest.raises(CorpusMismatchError) as excinfo:
        registry.invoke("echo", {"corpusId": corpus_id, "text": "hi"}, context, wrong_corpus)

    assert excinfo.value.callRecord is not None
    assert excinfo.value.callRecord.status == ToolCallStatus.REJECTED
    assert excinfo.value.callRecord.corpusId == corpus_id


@pytest.mark.parametrize("forged_leg", ["actual", "manifest"])
def test_each_runtime_corpus_identity_leg_is_checked_before_execution(
    corpus,
    corpus_id,
    forged_leg,
):
    executed = False

    def _must_not_execute(tool_input, context, supplied_corpus):
        nonlocal executed
        executed = True
        return _EchoOutput(results=["unsafe"])

    class CorpusView:
        def __getattr__(self, name):
            return getattr(corpus, name)

        @property
        def corpus_id(self):
            return "forged-corpus" if forged_leg == "actual" else corpus.corpus_id

        def get_manifest(self):
            manifest = corpus.get_manifest()
            if forged_leg == "manifest":
                return manifest.model_copy(update={"corpusId": "forged-corpus"})
            return manifest

    registry = ToolRegistry()
    registry.register(_make_definition(execute=_must_not_execute))

    with pytest.raises(CorpusMismatchError) as excinfo:
        registry.invoke(
            "echo",
            {"corpusId": corpus_id, "text": "hi"},
            ToolExecutionContext(corpusId=corpus_id),
            CorpusView(),
        )

    assert executed is False
    assert excinfo.value.callRecord.status == ToolCallStatus.REJECTED


def test_invoke_unauthorized_tool_raises(corpus, corpus_id):
    registry = ToolRegistry()
    registry.register(_make_definition())
    context = ToolExecutionContext(corpusId=corpus_id, allowedToolNames={"some-other-tool"})
    with pytest.raises(UnauthorizedToolError):
        registry.invoke("echo", {"corpusId": corpus_id, "text": "hi"}, context, corpus)


def test_invoke_unsupported_capability_raises(corpus, corpus_id):
    registry = ToolRegistry()
    registry.register(_make_definition(required_capabilities=frozenset({"does-not-exist"})))
    context = ToolExecutionContext(corpusId=corpus_id)
    with pytest.raises(UnsupportedCapabilityError):
        registry.invoke("echo", {"corpusId": corpus_id, "text": "hi"}, context, corpus)


def test_invoke_result_limit_exceeded_raises(corpus, corpus_id):
    registry = ToolRegistry()
    registry.register(_make_definition(max_result_limit=1))
    context = ToolExecutionContext(corpusId=corpus_id)
    with pytest.raises(ResultLimitExceededError):
        registry.invoke("echo", {"corpusId": corpus_id, "text": "hi", "maxResults": 5}, context, corpus)


def test_context_result_limit_is_enforced_even_when_tool_limit_is_higher(corpus, corpus_id):
    registry = ToolRegistry()
    registry.register(_make_definition(max_result_limit=10))
    context = ToolExecutionContext(corpusId=corpus_id, maximumResults=1)
    with pytest.raises(ResultLimitExceededError):
        registry.invoke("echo", {"corpusId": corpus_id, "text": "hi", "maxResults": 2}, context, corpus)


def test_context_result_limit_rejects_an_oversized_tool_output(corpus, corpus_id):
    def _too_many(tool_input, context, corpus):
        return _EchoOutput(results=["one", "two"])

    registry = ToolRegistry()
    registry.register(_make_definition(execute=_too_many))
    context = ToolExecutionContext(corpusId=corpus_id, maximumResults=1)

    with pytest.raises(MalformedToolOutputError) as excinfo:
        registry.invoke("echo", {"corpusId": corpus_id, "text": "hi"}, context, corpus)

    assert excinfo.value.callRecord is not None
    assert excinfo.value.callRecord.status == ToolCallStatus.FAILED


def test_context_character_limit_rejects_an_oversized_tool_output(corpus, corpus_id):
    registry = ToolRegistry()
    registry.register(_make_definition())
    context = ToolExecutionContext(corpusId=corpus_id, maximumOutputCharacters=1_000)

    with pytest.raises(MalformedToolOutputError) as excinfo:
        registry.invoke(
            "echo",
            {"corpusId": corpus_id, "text": "x" * 1_100},
            context,
            corpus,
        )

    assert excinfo.value.callRecord is not None
    assert excinfo.value.callRecord.status == ToolCallStatus.FAILED


def test_invoke_wraps_unexpected_exceptions(corpus, corpus_id):
    def _boom(tool_input, context, corpus):
        raise RuntimeError("boom")

    registry = ToolRegistry()
    registry.register(_make_definition(execute=_boom))
    context = ToolExecutionContext(corpusId=corpus_id)
    with pytest.raises(InternalRetrievalError) as excinfo:
        registry.invoke("echo", {"corpusId": corpus_id, "text": "hi"}, context, corpus)
    assert excinfo.value.callRecord is not None
    assert excinfo.value.callRecord.status == ToolCallStatus.FAILED
    assert excinfo.value.callRecord.errorType == "InternalRetrievalError"
    assert excinfo.value.callRecord.errorMessage == 'Tool "echo" failed unexpectedly'
    assert excinfo.value.__cause__ is None


def test_corpus_failures_are_tool_errors_with_audit_records(corpus, corpus_id):
    def _missing(tool_input, context, corpus):
        raise UnknownRecordError("missing scoped record")

    registry = ToolRegistry()
    registry.register(_make_definition(execute=_missing))

    with pytest.raises(CorpusRetrievalError) as excinfo:
        registry.invoke(
            "echo",
            {"corpusId": corpus_id, "text": "hi"},
            ToolExecutionContext(corpusId=corpus_id),
            corpus,
        )

    assert excinfo.value.corpusErrorType == "UnknownRecordError"
    assert excinfo.value.callRecord.status == ToolCallStatus.REJECTED
    assert excinfo.value.__cause__ is None


@pytest.mark.parametrize(
    ("raw_input", "error_type", "expected_status"),
    [
        ({"corpusId": "{corpus_id}"}, MalformedToolInputError, ToolCallStatus.REJECTED),
        (
            {"corpusId": "{corpus_id}", "text": "hi", "maxResults": 5},
            ResultLimitExceededError,
            ToolCallStatus.REJECTED,
        ),
    ],
)
def test_rejected_calls_carry_complete_audit_records(
    corpus,
    corpus_id,
    raw_input,
    error_type,
    expected_status,
):
    registry = ToolRegistry()
    registry.register(_make_definition(max_result_limit=1))
    context = ToolExecutionContext(corpusId=corpus_id)
    resolved_input = {
        key: (corpus_id if value == "{corpus_id}" else value)
        for key, value in raw_input.items()
    }

    with pytest.raises(error_type) as excinfo:
        registry.invoke("echo", resolved_input, context, corpus)

    record = excinfo.value.callRecord
    assert record is not None
    assert record.status == expected_status
    assert record.toolName == "echo"
    assert record.toolVersion == "test-v1"
    assert record.inputHash
    assert record.completedAt is not None
    assert record.latencyMs is not None and record.latencyMs >= 0
    assert record.errorType == error_type.__name__
    assert record.errorMessage


def test_invoke_malformed_output_raises(corpus, corpus_id):
    def _wrong_type(tool_input, context, corpus):
        return {"not": "the right model"}

    registry = ToolRegistry()
    registry.register(_make_definition(execute=_wrong_type))
    context = ToolExecutionContext(corpusId=corpus_id)
    with pytest.raises(MalformedToolOutputError):
        registry.invoke("echo", {"corpusId": corpus_id, "text": "hi"}, context, corpus)


def test_invoke_revalidates_a_constructed_same_class_output(corpus, corpus_id):
    def _invalid_constructed_output(tool_input, context, corpus):
        return _EchoOutput.model_construct(results="not-a-list")

    registry = ToolRegistry()
    registry.register(_make_definition(execute=_invalid_constructed_output))

    with pytest.raises(MalformedToolOutputError) as excinfo:
        registry.invoke(
            "echo",
            {"corpusId": corpus_id, "text": "hi"},
            ToolExecutionContext(corpusId=corpus_id),
            corpus,
        )

    assert excinfo.value.callRecord.status == ToolCallStatus.FAILED


def test_hashes_are_deterministic_and_call_ids_are_unique(corpus, corpus_id):
    registry = ToolRegistry()
    registry.register(_make_definition())
    context = ToolExecutionContext(corpusId=corpus_id)

    _, record1 = registry.invoke("echo", {"corpusId": corpus_id, "text": "hi"}, context, corpus)
    _, record2 = registry.invoke("echo", {"corpusId": corpus_id, "text": "hi"}, context, corpus)

    assert record1.inputHash == record2.inputHash
    assert record1.outputHash == record2.outputHash
    assert record1.toolCallId != record2.toolCallId
