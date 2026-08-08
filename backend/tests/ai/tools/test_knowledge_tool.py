"""get_actor_knowledge_state -- E2's clearest cross-corpus test of honest
abstention: blank-cheque has one real KnownAtTime record, concert-of-
europe has zero. Both must be handled without inventing data."""

from __future__ import annotations

import pytest

from chronicle.ai.tools import ToolExecutionContext
from chronicle.contracts.enums import Awareness, ReviewStatus, Visibility
from chronicle.ai.tools.errors import CorpusRetrievalError


def test_entity_with_no_knowledge_states_returns_unsupported(tool_registry, corpus, corpus_id, context):
    investigation = corpus.get_investigation()
    entities_with_states = {ks.personOrInstitutionId for ks in investigation.knowledgeStates}
    entity = next((e for e in investigation.entities if e.id not in entities_with_states), None)
    if entity is None:
        pytest.skip("every entity in this corpus has a knowledge state")

    output, _record = tool_registry.invoke(
        "get_actor_knowledge_state", {"corpusId": corpus_id, "entityId": entity.id}, context, corpus
    )
    assert output.dataAvailable is False
    assert output.availability == "insufficient-data"
    assert output.knowledgeStates == []
    assert output.insufficientDataReason is not None


def test_entity_with_a_real_knowledge_state_returns_it(tool_registry, corpus, corpus_id, context):
    investigation = corpus.get_investigation()
    if not investigation.knowledgeStates:
        pytest.skip("this corpus has no knowledge states at all")
    state = investigation.knowledgeStates[0]

    output, _record = tool_registry.invoke(
        "get_actor_knowledge_state",
        {"corpusId": corpus_id, "entityId": state.personOrInstitutionId},
        context,
        corpus,
    )
    assert output.dataAvailable is True
    assert output.availability == "records-available"
    assert output.insufficientDataReason is None
    assert any(ks.knowledgeStateId == state.id for ks in output.knowledgeStates)
    matching = next(ks for ks in output.knowledgeStates if ks.knowledgeStateId == state.id)
    assert matching.fact == state.fact
    assert matching.awareness == state.awareness.value
    assert matching.reviewStatus == state.reviewStatus.value
    assert matching.visibility == state.visibility.value
    assert matching.directOrInferred is None
    assert matching.directOrInferredAvailability == "not-recorded"
    assert matching.evidenceTotalCount == len(state.evidenceLinkIds)
    assert all(link.targetType == "knownAtTime" for link in matching.evidenceLinks)
    assert all(link.targetId == state.id for link in matching.evidenceLinks)


def test_concert_of_europe_has_zero_knowledge_states_at_all(tool_registry, corpus_registry):
    """Ground-truth check backing the two tests above: confirms the
    honest-abstention path is actually exercised, not accidentally
    skipped on both corpora."""
    concert = corpus_registry.get_corpus("concert-of-europe-1814-1822")
    assert concert.get_investigation().knowledgeStates == []


def test_blank_cheque_has_at_least_one_knowledge_state(corpus_registry):
    blank_cheque = corpus_registry.get_corpus("blank-cheque-golden")
    assert len(blank_cheque.get_investigation().knowledgeStates) >= 1


def test_no_capability_requirement_gates_this_tool(tool_registry):
    """Deliberately not gated by a corpus capability check -- both
    corpora must reach execute() so the honest-abstention path (not an
    UnsupportedCapabilityError) is what a caller actually sees."""
    definition = tool_registry.get("get_actor_knowledge_state")
    assert definition.required_capabilities == frozenset()


def test_unknown_entity_raises(tool_registry, corpus, corpus_id, context):
    with pytest.raises(CorpusRetrievalError):
        tool_registry.invoke(
            "get_actor_knowledge_state", {"corpusId": corpus_id, "entityId": "no-such-entity"}, context, corpus
        )


def test_knowledge_state_lists_and_evidence_are_bounded(tool_registry, corpus_registry):
    corpus = corpus_registry.get_corpus("blank-cheque-golden")
    state = corpus.get_investigation().knowledgeStates[0]
    context = ToolExecutionContext(corpusId=corpus.corpus_id, maximumResults=1)
    output, _ = tool_registry.invoke(
        "get_actor_knowledge_state",
        {"corpusId": corpus.corpus_id, "entityId": state.personOrInstitutionId},
        context,
        corpus,
    )

    assert len(output.knowledgeStates) <= 1
    assert output.returnedCount == len(output.knowledgeStates)
    assert output.truncated == (output.totalCount > output.returnedCount)
    assert all(len(entry.evidenceLinks) <= 1 for entry in output.knowledgeStates)
    assert all(
        entry.evidenceTruncated == (entry.evidenceTotalCount > entry.evidenceReturnedCount)
        for entry in output.knowledgeStates
    )


def test_knowledge_states_share_one_global_nested_evidence_budget(tool_registry, corpus_registry):
    base = corpus_registry.get_corpus("blank-cheque-golden")
    original = base.get_investigation().knowledgeStates[0]
    repeated = original.model_copy(update={"evidenceLinkIds": original.evidenceLinkIds * 2})

    class CorpusView:
        def __getattr__(self, name):
            return getattr(base, name)

        @property
        def corpus_id(self):
            return base.corpus_id

        def get_knowledge_states_for(self, entity_id):
            return [repeated, repeated]

        def get_knowledge_state(self, knowledge_state_id):
            return repeated

    output, _ = tool_registry.invoke(
        "get_actor_knowledge_state",
        {"corpusId": base.corpus_id, "entityId": repeated.personOrInstitutionId},
        ToolExecutionContext(corpusId=base.corpus_id, maximumResults=2),
        CorpusView(),
    )

    assert sum(len(entry.evidenceLinks) for entry in output.knowledgeStates) <= 2
    assert all(entry.evidenceTotalCount == 1 for entry in output.knowledgeStates)


def test_rejected_private_not_yet_known_state_is_returned_without_reinterpretation(
    tool_registry, corpus_registry
):
    base = corpus_registry.get_corpus("blank-cheque-golden")
    original = base.get_investigation().knowledgeStates[0]
    altered = original.model_copy(
        update={
            "awareness": Awareness.NOT_YET_KNOWN,
            "reviewStatus": ReviewStatus.REJECTED,
            "visibility": Visibility.PRIVATE_WORKSPACE,
        }
    )

    class CorpusView:
        def __getattr__(self, name):
            return getattr(base, name)

        @property
        def corpus_id(self):
            return base.corpus_id

        def get_knowledge_states_for(self, entity_id):
            assert entity_id == altered.personOrInstitutionId
            return [altered]

        def get_knowledge_state(self, knowledge_state_id):
            assert knowledge_state_id == altered.id
            return altered

    corpus = CorpusView()
    output, _ = tool_registry.invoke(
        "get_actor_knowledge_state",
        {"corpusId": base.corpus_id, "entityId": altered.personOrInstitutionId},
        ToolExecutionContext(corpusId=base.corpus_id),
        corpus,
    )
    entry = output.knowledgeStates[0]
    assert output.dataAvailable is True
    assert entry.awareness == "not-yet-known"
    assert entry.reviewStatus == "rejected"
    assert entry.visibility == "private-workspace"
    assert all(link.reviewStatus == "rejected" for link in entry.evidenceLinks)
    assert all(link.visibility == "private-workspace" for link in entry.evidenceLinks)
