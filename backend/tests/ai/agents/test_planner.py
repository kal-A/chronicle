from __future__ import annotations

import json

import pytest

from chronicle.ai.contracts.plan import (
    ArgumentBinding,
    InvestigationPlan,
    PlanDisposition,
    PlannedToolCall,
    QuestionType,
    RequiredEvidenceType,
    ToolPurpose,
)
from chronicle.ai.contracts.run import (
    CorpusSnapshot,
    InvestigationRequest,
    SelectedRecord,
    SelectedRecordType,
    WorkspaceContextSnapshot,
)
from chronicle.ai.models.deterministic import DeterministicModelProvider
from chronicle.ai.models.errors import RetryExhaustedError
from chronicle.ai.orchestration.policies import AgentExecutionPolicy
from chronicle.ai.tools import ToolSpec
from chronicle.ai.tools import build_default_registry
from chronicle.ai.agents.planner import (
    InvestigationPlanner,
    PlannerBudgetError,
    PlannerValidationError,
)
from chronicle.ai.agents.planner_prompt import (
    ToolSpecRepresentation,
    available_tool_specs,
    build_planner_prompt,
)


def _request(
    *,
    selected_id: str | None = "claim-1",
    selected_type: SelectedRecordType = SelectedRecordType.CLAIM,
) -> InvestigationRequest:
    context = None
    if selected_id is not None:
        context = WorkspaceContextSnapshot(
            selectedRecords=(
                SelectedRecord(recordType=selected_type, recordId=selected_id),
            )
        )
    return InvestigationRequest(
        runId="run-1",
        corpusId="corpus-1",
        userQuestion="What evidence bears on the selected claim?",
        workspaceContext=context,
    )


def _snapshot(*, capabilities: tuple[str, ...] = ("claims", "passages")) -> CorpusSnapshot:
    return CorpusSnapshot(
        corpusId="corpus-1",
        packageId="package-1",
        packageHash="abc123",
        packageRevision=1,
        schemaVersion="1.0",
        capabilities=capabilities,
    )


def _spec(
    name: str = "get_claim_evidence",
    *,
    capability: str = "claims",
) -> ToolSpec:
    return ToolSpec(
        name=name,
        version="test-v1",
        description="Return the evidence ledger for one selected claim.",
        inputSchema={
            "type": "object",
            "properties": {
                "corpusId": {"type": "string", "minLength": 1},
                "claimId": {"type": "string", "minLength": 1},
            },
            "required": ["corpusId", "claimId"],
            "additionalProperties": False,
        },
        outputSummary="Evidence ledger entries.",
        requiredCapabilities=[capability],
        maxResultLimit=4,
        maxOutputCharacters=6_000,
        useWhen="A trusted claim identifier is selected.",
        avoidWhen="No claim identifier is available.",
    )


def _plan(
    *,
    tool_name: str = "get_claim_evidence",
    claim_id: str = "claim-1",
    run_id: str = "run-1",
    corpus_id: str = "corpus-1",
) -> InvestigationPlan:
    return InvestigationPlan(
        planId="plan-1",
        runId=run_id,
        corpusId=corpus_id,
        disposition=PlanDisposition.PROCEED,
        normalizedQuestion="What evidence bears on the selected claim?",
        questionType=QuestionType.DIRECT_EVIDENCE,
        requiredEvidenceTypes=[RequiredEvidenceType.CLAIM_EVIDENCE],
        plannedToolCalls=[
            PlannedToolCall(
                callId="call-1",
                toolName=tool_name,
                purposeCode=ToolPurpose.FIND_SUPPORT,
                arguments={"claimId": claim_id},
            )
        ],
    )


def test_planner_schema_excludes_counterevidence_type_for_a_plain_question():
    # Over a passage-only corpus search_passages is available, but a factual
    # "when/where" question does not call for counterevidence. The COUNTEREVIDENCE
    # question type must not be offered, or the small model misclassifies the
    # question and emits an incoherent counterevidence plan that hard-abstains
    # (the live P3 walkthrough's Great Fire failure). Gate it on the question,
    # mirroring ACTOR_KNOWLEDGE / TIMELINE_ORDERING.
    from chronicle.ai.agents.planner_schema import build_planner_response_schema

    request = _request().model_copy(
        update={"userQuestion": "When and where did the event begin?"}
    )
    schema = build_planner_response_schema(
        request, [_spec("search_passages", capability="passages")]
    )
    assert "counterevidence" not in schema["$defs"]["QuestionType"]["enum"]


def test_planner_schema_keeps_counterevidence_type_for_a_counterevidence_question():
    from chronicle.ai.agents.planner_schema import build_planner_response_schema

    request = _request().model_copy(
        update={"userQuestion": "What counterevidence contradicts the reported claim?"}
    )
    schema = build_planner_response_schema(
        request, [_spec("search_passages", capability="passages")]
    )
    assert "counterevidence" in schema["$defs"]["QuestionType"]["enum"]


def test_planner_returns_only_a_validated_plan_and_records_bounded_call_metadata():
    provider = DeterministicModelProvider()
    provider.enqueue_value(_plan())
    planner = InvestigationPlanner(provider)

    result = planner.plan(_request(), _snapshot(), [_spec()])

    assert isinstance(result, InvestigationPlan)
    assert result.plannedToolCalls[0].toolName == "get_claim_evidence"
    assert planner.last_execution is not None
    assert planner.last_execution.modelCall.attemptCount == 1
    assert planner.last_execution.modelCall.generationSettings.contextTokens == 8_192
    assert planner.last_execution.modelCall.generationSettings.maxCompletionTokens == 900
    assert planner.last_execution.modelCall.generationSettings.temperature == 0
    assert planner.last_execution.promptMeasurement.promptCharacters <= 24_000
    assert planner.last_execution.promptMeasurement.toolSpecCharacters <= 18_000


def test_planner_rejects_unknown_tool_even_when_model_output_is_schema_valid():
    provider = DeterministicModelProvider()
    provider.enqueue_value(_plan(tool_name="invented_search"))

    with pytest.raises(PlannerValidationError, match="not authorized"):
        InvestigationPlanner(provider).plan(_request(), _snapshot(), [_spec()])


def test_planner_filters_unavailable_capabilities_and_rejects_use_of_filtered_tool():
    unavailable = _spec("requires_maps", capability="maps")
    provider = DeterministicModelProvider()
    provider.enqueue_value(_plan(tool_name="requires_maps"))
    planner = InvestigationPlanner(provider)

    with pytest.raises(PlannerValidationError, match="not authorized"):
        planner.plan(_request(), _snapshot(capabilities=("claims",)), [unavailable])

    assert planner.last_prompt is not None
    assert "requires_maps" not in planner.last_prompt.userPrompt


def test_planner_accepts_truthful_out_of_corpus_abstention_without_tool_calls():
    abstention = InvestigationPlan(
        planId="plan-2",
        runId="run-1",
        corpusId="corpus-1",
        disposition=PlanDisposition.ABSTAIN,
        normalizedQuestion="What occurred after this corpus ends?",
        questionType=QuestionType.OUT_OF_CORPUS,
        unsupportedReason="The requested period is listed as outside the corpus scope.",
    )
    provider = DeterministicModelProvider()
    provider.enqueue_value(abstention)

    assert InvestigationPlanner(provider).plan(_request(), _snapshot(), [_spec()]) == abstention


def test_planner_rejects_out_of_corpus_classification_that_still_proceeds():
    invalid = _plan().model_copy(update={"questionType": QuestionType.OUT_OF_CORPUS})
    provider = DeterministicModelProvider()
    provider.enqueue_value(invalid)

    with pytest.raises(PlannerValidationError, match="must abstain"):
        InvestigationPlanner(provider).plan(_request(), _snapshot(), [_spec()])


def test_planner_rejects_invented_record_identifier():
    provider = DeterministicModelProvider()
    provider.enqueue_value(_plan(claim_id="claim-not-selected"))

    with pytest.raises(PlannerValidationError, match="untrusted record identifier"):
        InvestigationPlanner(provider).plan(_request(), _snapshot(), [_spec()])


def test_planner_rejects_arguments_that_fail_advertised_input_schema():
    provider = DeterministicModelProvider()
    malformed = _plan().model_copy(
        update={
            "plannedToolCalls": [
                PlannedToolCall(
                    callId="call-1",
                    toolName="get_claim_evidence",
                    purposeCode=ToolPurpose.FIND_SUPPORT,
                    arguments={"claimId": "claim-1", "unexpected": True},
                )
            ]
        }
    )
    provider.enqueue_value(malformed)

    with pytest.raises(PlannerValidationError, match="input schema"):
        InvestigationPlanner(provider).plan(_request(), _snapshot(), [_spec()])


def test_planner_enforces_prompt_budget_before_calling_provider():
    provider = DeterministicModelProvider()
    provider.enqueue_value(_plan())
    bloated = _spec().model_copy(update={"description": "x" * 19_000})

    with pytest.raises(PlannerBudgetError, match="ToolSpec catalog"):
        InvestigationPlanner(provider).plan(_request(), _snapshot(), [bloated])

    assert planner_queue_size(provider) == 1


def test_planner_delegates_malformed_output_recovery_to_two_bounded_provider_attempts():
    provider = DeterministicModelProvider()
    provider.enqueue_malformed()
    provider.enqueue_malformed()

    with pytest.raises(RetryExhaustedError) as exc_info:
        InvestigationPlanner(provider).plan(_request(), _snapshot(), [_spec()])

    assert exc_info.value.callRecord is not None
    assert exc_info.value.callRecord.attemptCount == 2


def test_prompt_is_topic_neutral_and_explicitly_forbids_answering_or_inventing_ids():
    prompt = build_planner_prompt(
        _request(),
        _snapshot(),
        [_spec()],
        AgentExecutionPolicy(),
        representation=ToolSpecRepresentation.CAPABILITY_FILTERED,
    )

    combined = f"{prompt.systemPrompt}\n{prompt.userPrompt}".lower()
    assert "do not answer" in combined
    assert "do not invent" in combined
    assert "proceed requires exactly one plannedtoolcall" in combined
    assert "abstain requires zero plannedtoolcalls" in combined
    assert "blank cheque" not in combined
    assert "concert of europe" not in combined
    assert prompt.toolSpecCharacters == len(json.dumps(prompt.serializedToolSpecs, sort_keys=True))


def test_prompt_caps_advertised_tool_limits_to_execution_policy():
    specs = build_default_registry().list_specs()
    prompt = build_planner_prompt(
        _request(selected_id=None),
        _snapshot(capabilities=("passages",)),
        specs,
        AgentExecutionPolicy(),
    )
    search = next(item for item in prompt.serializedToolSpecs if item["name"] == "search_passages")

    max_results = search["inputSchema"]["properties"]["maxResults"]
    assert max_results["maximum"] == 4
    assert max_results["default"] == 4
    assert search["maxResultLimit"] == 4
    assert search["maxOutputCharacters"] == 6_000


def test_planner_rejects_run_or_corpus_identity_substitution():
    provider = DeterministicModelProvider()
    provider.enqueue_value(_plan(run_id="invented-run"))

    with pytest.raises(PlannerValidationError, match="identity"):
        InvestigationPlanner(provider).plan(_request(), _snapshot(), [_spec()])


def test_planner_can_make_a_topic_neutral_discovery_plan_without_selected_ids():
    search_plan = InvestigationPlan(
        planId="plan-search",
        runId="run-1",
        corpusId="corpus-1",
        disposition=PlanDisposition.PROCEED,
        normalizedQuestion="What evidence bears on this question?",
        questionType=QuestionType.DIRECT_EVIDENCE,
        requiredEvidenceTypes=[RequiredEvidenceType.PASSAGE],
        plannedToolCalls=[
            PlannedToolCall(
                callId="search-1",
                toolName="search_passages",
                purposeCode=ToolPurpose.SEARCH_CONTEXT,
                arguments={"query": "evidence bearing on the question", "maxResults": 4},
            )
        ],
    )
    provider = DeterministicModelProvider()
    provider.enqueue_value(search_plan)
    specs = build_default_registry().list_specs()

    result = InvestigationPlanner(provider).plan(
        _request(selected_id=None),
        _snapshot(capabilities=("passages",)),
        specs,
    )

    assert result == search_plan


def test_planner_excludes_tools_that_cannot_use_the_selected_record_type():
    incompatible = InvestigationPlan(
        planId="plan-incompatible-tool",
        runId="run-1",
        corpusId="corpus-1",
        disposition=PlanDisposition.PROCEED,
        normalizedQuestion="What did the selected claim establish?",
        questionType=QuestionType.ACTOR_KNOWLEDGE,
        requiredEvidenceTypes=[RequiredEvidenceType.KNOWLEDGE_STATE],
        plannedToolCalls=[
            PlannedToolCall(
                callId="knowledge-1",
                toolName="get_actor_knowledge_state",
                purposeCode=ToolPurpose.CHECK_KNOWLEDGE,
                arguments={"entityId": "claim-1"},
            )
        ],
        requiresKnowledgeState=True,
    )
    provider = DeterministicModelProvider()
    provider.enqueue_value(incompatible)
    planner = InvestigationPlanner(provider)

    with pytest.raises(PlannerValidationError, match="not authorized"):
        planner.plan(
            _request(selected_type=SelectedRecordType.CLAIM),
            _snapshot(capabilities=("claims", "passages")),
            build_default_registry().list_specs(),
        )

    assert planner.last_prompt is not None
    assert '"name": "get_actor_knowledge_state"' not in planner.last_prompt.userPrompt


def test_direct_selected_record_question_does_not_advertise_counterevidence_only_tool():
    request = _request().model_copy(
        update={"userQuestion": "What does the selected report say about support?"}
    )

    names = {
        spec.name
        for spec in available_tool_specs(
            build_default_registry().list_specs(),
            _snapshot(),
            request,
        )
    }

    assert "get_claim_evidence" in names
    assert "find_counterevidence" not in names


def test_explicit_challenge_question_advertises_counterevidence_tool():
    request = _request().model_copy(
        update={"userQuestion": "What evidence contradicts the selected claim?"}
    )

    names = {
        spec.name
        for spec in available_tool_specs(
            build_default_registry().list_specs(),
            _snapshot(),
            request,
        )
    }

    assert "find_counterevidence" in names


def test_date_mention_alone_does_not_advertise_timeline_ordering():
    request = _request(selected_id=None).model_copy(
        update={"userQuestion": "What does the July 5 report say about support?"}
    )
    provider = DeterministicModelProvider()
    provider.enqueue_value(_plan(tool_name="search_passages"))
    planner = InvestigationPlanner(provider)

    with pytest.raises(PlannerValidationError):
        planner.plan(
            request,
            _snapshot(capabilities=("claims", "passages", "timeline")),
            build_default_registry().list_specs(),
        )

    assert planner.last_prompt is not None
    assert '"name": "get_timeline_context"' not in planner.last_prompt.userPrompt
    response_schema = json.loads(planner.last_prompt.responseSchema)
    assert "timeline_ordering" not in response_schema["$defs"]["QuestionType"]["enum"]


def test_explicit_sequence_question_advertises_timeline_ordering():
    request = _request(selected_id=None).model_copy(
        update={"userQuestion": "What happened before and after the July 5 report?"}
    )
    specs = available_tool_specs(
        build_default_registry().list_specs(),
        _snapshot(capabilities=("claims", "passages", "timeline")),
        request,
    )

    assert "get_timeline_context" in {spec.name for spec in specs}


class _SchemaCapturingProvider:
    def __init__(self, value: InvestigationPlan) -> None:
        self.inner = DeterministicModelProvider()
        self.inner.enqueue_value(value)
        self.response_schema = None

    def generate_structured(self, *, response_schema, **kwargs):
        self.response_schema = response_schema
        return self.inner.generate_structured(response_schema=response_schema, **kwargs)


def test_planner_supplies_a_strict_tool_specific_schema_to_the_model():
    plan = _plan()
    provider = _SchemaCapturingProvider(plan)

    result = InvestigationPlanner(provider).plan(_request(), _snapshot(), [_spec()])

    assert result == plan
    schema = provider.response_schema
    assert schema is not None
    assert set(schema["required"]) == set(schema["properties"])
    variants = schema["properties"]["plannedToolCalls"]["items"]["oneOf"]
    assert len(variants) == 1
    claim_call = variants[0]
    assert claim_call["properties"]["toolName"] == {
        "const": "get_claim_evidence",
        "type": "string",
    }
    assert claim_call["properties"]["arguments"]["properties"]["claimId"]["enum"] == [
        "claim-1"
    ]
    assert set(claim_call["required"]) == {
        "callId",
        "toolName",
        "purposeCode",
        "arguments",
        "bindings",
        "dependsOn",
    }
    assert schema["properties"]["plannedToolCalls"]["maxItems"] == 1
    assert claim_call["properties"]["bindings"]["maxItems"] == 0
    assert claim_call["properties"]["dependsOn"]["maxItems"] == 0


def test_planner_rejects_model_requested_result_limit_above_policy():
    oversized = _plan().model_copy(
        update={
            "plannedToolCalls": [
                PlannedToolCall(
                    callId="call-1",
                    toolName="get_claim_evidence",
                    purposeCode=ToolPurpose.FIND_SUPPORT,
                    arguments={"claimId": "claim-1", "maxResults": 5},
                )
            ]
        }
    )
    extended_spec = _spec().model_copy(
        update={
            "inputSchema": {
                "type": "object",
                "properties": {
                    "corpusId": {"type": "string"},
                    "claimId": {"type": "string"},
                    "maxResults": {"type": "integer", "minimum": 1, "maximum": 20},
                },
                "required": ["corpusId", "claimId"],
                "additionalProperties": False,
            },
            "maxResultLimit": 20,
        }
    )
    provider = DeterministicModelProvider()
    provider.enqueue_value(oversized)

    with pytest.raises(PlannerValidationError, match="result limit"):
        InvestigationPlanner(provider).plan(_request(), _snapshot(), [extended_spec])


def test_planner_rejects_forward_or_duplicate_argument_bindings():
    invalid = InvestigationPlan(
        planId="plan-binding",
        runId="run-1",
        corpusId="corpus-1",
        disposition=PlanDisposition.PROCEED,
        normalizedQuestion="Find and inspect evidence.",
        questionType=QuestionType.DIRECT_EVIDENCE,
        plannedToolCalls=[
            PlannedToolCall(
                callId="inspect",
                toolName="get_claim_evidence",
                purposeCode=ToolPurpose.FIND_SUPPORT,
                arguments={"claimId": "claim-1"},
                bindings=[
                    ArgumentBinding(
                        argumentName="claimId",
                        sourceCallId="discover",
                        recordType="claim",
                    )
                ],
                dependsOn=["discover"],
            ),
            PlannedToolCall(
                callId="discover",
                toolName="get_claim_evidence",
                purposeCode=ToolPurpose.SEARCH_CONTEXT,
                arguments={"claimId": "claim-1"},
            ),
        ],
    )
    provider = DeterministicModelProvider()
    provider.enqueue_value(invalid)

    with pytest.raises(PlannerValidationError, match="binding"):
        InvestigationPlanner(provider).plan(_request(), _snapshot(), [_spec()])


@pytest.mark.parametrize(
    ("argument_name", "selected_type", "allowed"),
    [
        ("actorId", SelectedRecordType.ENTITY, True),
        ("actorId", SelectedRecordType.CLAIM, False),
        ("startNodeId", SelectedRecordType.CLAIM, True),
        ("startNodeId", SelectedRecordType.RELATIONSHIP, True),
        ("startNodeId", SelectedRecordType.KNOWLEDGE_STATE, True),
        ("startNodeId", SelectedRecordType.EVENT, False),
        ("mysteryId", SelectedRecordType.CLAIM, False),
    ],
)
def test_literal_record_id_authorization_preserves_selected_record_type(
    argument_name,
    selected_type,
    allowed,
):
    spec = _spec("typed_tool").model_copy(
        update={
            "inputSchema": {
                "type": "object",
                "properties": {
                    "corpusId": {"type": "string"},
                    argument_name: {"type": "string"},
                },
                "required": ["corpusId", argument_name],
                "additionalProperties": False,
            }
        }
    )
    plan = _plan(tool_name="typed_tool").model_copy(
        update={
            "plannedToolCalls": [
                PlannedToolCall(
                    callId="typed-1",
                    toolName="typed_tool",
                    purposeCode=ToolPurpose.SEARCH_CONTEXT,
                    arguments={argument_name: "selected-1"},
                )
            ]
        }
    )
    provider = DeterministicModelProvider()
    provider.enqueue_value(plan)
    planner = InvestigationPlanner(provider)
    request = _request(selected_id="selected-1", selected_type=selected_type)

    if allowed:
        assert planner.plan(request, _snapshot(), [spec]) == plan
    else:
        with pytest.raises(PlannerValidationError, match="record type|record-id argument"):
            planner.plan(request, _snapshot(), [spec])


@pytest.mark.parametrize(
    ("question_type", "expected_message"),
    [
        (QuestionType.ACTOR_KNOWLEDGE, "knowledge-state"),
        (QuestionType.COUNTEREVIDENCE, "counterevidence"),
        (QuestionType.TIMELINE_ORDERING, "timeline"),
    ],
)
def test_specialized_question_types_require_coherent_flags_evidence_and_tools(
    question_type,
    expected_message,
):
    incoherent = _plan().model_copy(update={"questionType": question_type})
    provider = DeterministicModelProvider()
    provider.enqueue_value(incoherent)

    with pytest.raises(PlannerValidationError, match=expected_message):
        InvestigationPlanner(provider).plan(_request(), _snapshot(), [_spec()])


def test_counterevidence_selected_claim_accepts_one_role_preserving_claim_ledger_call():
    coherent = _plan().model_copy(
        update={
            "questionType": QuestionType.COUNTEREVIDENCE,
            "requiredEvidenceTypes": [RequiredEvidenceType.COUNTEREVIDENCE],
            "requiresCounterevidence": True,
        }
    )
    provider = DeterministicModelProvider()
    provider.enqueue_value(coherent)

    result = InvestigationPlanner(provider).plan(_request(), _snapshot(), [_spec()])

    assert result == coherent
    assert [call.toolName for call in result.plannedToolCalls] == ["get_claim_evidence"]


def test_counterevidence_rejects_unrelated_tool_even_with_flag_and_evidence_type():
    unrelated = _plan(tool_name="unrelated_tool").model_copy(
        update={
            "questionType": QuestionType.COUNTEREVIDENCE,
            "requiredEvidenceTypes": [RequiredEvidenceType.COUNTEREVIDENCE],
            "requiresCounterevidence": True,
        }
    )
    provider = DeterministicModelProvider()
    provider.enqueue_value(unrelated)

    with pytest.raises(PlannerValidationError, match="role-preserving"):
        InvestigationPlanner(provider).plan(
            _request(),
            _snapshot(),
            [_spec("unrelated_tool")],
        )


@pytest.mark.parametrize("evidence_roles", [["counterevidence"], ["supporting"]])
def test_counterevidence_search_requires_explicit_counterevidence_role(evidence_roles):
    search_call = PlannedToolCall(
        callId="search-counter",
        toolName="search_passages",
        purposeCode=ToolPurpose.FIND_COUNTEREVIDENCE,
        arguments={
            "query": "material challenging the proposition",
            "evidenceRoles": evidence_roles,
            "maxResults": 4,
        },
    )
    plan = _plan().model_copy(
        update={
            "questionType": QuestionType.COUNTEREVIDENCE,
            "requiredEvidenceTypes": [RequiredEvidenceType.COUNTEREVIDENCE],
            "requiresCounterevidence": True,
            "plannedToolCalls": [search_call],
        }
    )
    provider = DeterministicModelProvider()
    provider.enqueue_value(plan)
    specs = build_default_registry().list_specs()
    planner = InvestigationPlanner(provider)

    if "counterevidence" in evidence_roles:
        assert planner.plan(
            _request(selected_id=None),
            _snapshot(capabilities=("passages",)),
            specs,
        ) == plan
    else:
        with pytest.raises(PlannerValidationError, match="role-preserving"):
            planner.plan(
                _request(selected_id=None),
                _snapshot(capabilities=("passages",)),
                specs,
            )


@pytest.mark.parametrize("unsafe_field", ["deterministic", "currentCorpusOnly"])
def test_planner_excludes_tool_specs_that_are_not_deterministic_current_corpus_only(unsafe_field):
    unsafe = _spec("unsafe_tool").model_copy(update={unsafe_field: False})
    provider = DeterministicModelProvider()
    provider.enqueue_value(_plan(tool_name="unsafe_tool"))
    planner = InvestigationPlanner(provider)

    with pytest.raises(PlannerValidationError, match="not authorized"):
        planner.plan(_request(), _snapshot(), [unsafe])

    assert planner.last_prompt is not None
    assert "unsafe_tool" not in planner.last_prompt.userPrompt


def planner_queue_size(provider: DeterministicModelProvider) -> int:
    """Test-only observation: no queued output means no provider call was made."""

    return len(provider._queue)  # noqa: SLF001
