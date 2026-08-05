<!-- See 00_START_HERE.md for the encoding-fix note that applies to this whole instruction set. -->

# Chronicle — Multi-Agent Architecture

[← Product reset](./01_PRODUCT_AND_ROADMAP_RESET.md) · [Next: Retrieval and MCP infrastructure →](./03_RETRIEVAL_SOURCE_AND_MCP_INFRASTRUCTURE.md)

## 1. Goal

Build a small number of real, understandable agents for both product efficiency and hands-on learning.

Do not build a theatrical swarm. Begin with four bounded roles and deterministic retrieval tools.

```text
User question
→ Investigation Planner
→ Tool execution and retrieval
→ Evidence Analyst
→ Historical Critic
→ Investigation Guide
→ deterministic answer/action validation
→ user
```

## 2. Agent 1 — Investigation Planner

### Responsibility

Convert the user question and workspace context into a typed research plan.

### Inputs

- question;
- investigation ID;
- scene ID;
- selected lens;
- selected date range;
- selected records;
- conversation summary;
- available tools;
- corpus capabilities.

### Output

```python
class InvestigationPlan(BaseModel):
    question_type: QuestionType
    normalized_question: str
    target_entity_ids: list[str]
    target_event_ids: list[str]
    time_range: TimeRange | None
    required_tool_calls: list[PlannedToolCall]
    required_sections: list[AnswerSection]
    expected_evidence_types: list[EvidenceType]
    needs_counterevidence: bool
    allow_abstention: bool = True
```

Initial question classes:

- direct evidence;
- explanation;
- relationship trace;
- source comparison;
- perspective comparison;
- knowledge state;
- disagreement;
- missing evidence;
- unsupported/out-of-corpus.

The Planner cannot write the final answer, cite arbitrary IDs, call unregistered tools, or exceed a bounded tool budget.

## 3. Deterministic tool layer

Retrieval is initially software, not another agent.

Initial tools:

```text
search_passages
get_source_metadata
get_claim_evidence
get_relationship_evidence
get_timeline_context
get_actor_knowledge_state
compare_sources
compare_perspectives
find_counterevidence
find_conflicts
trace_reviewed_relationships
get_map_context
get_research_gaps
```

Every tool must have:

- typed input and output;
- authorization and scope checks;
- corpus boundaries;
- deterministic tests;
- latency recording;
- error taxonomy;
- result-size limits;
- provenance.

## 4. Agent 2 — Evidence Analyst

### Responsibility

Build a structured answer candidate from retrieved evidence.

```python
class AnalysisDraft(BaseModel):
    direct_answer_claim_ids: list[str]
    proposed_statements: list[ProposedStatement]
    sequence: list[SequenceStep]
    relationship_trace: list[RelationshipStep]
    disagreements: list[Disagreement]
    counterevidence: list[EvidenceReference]
    limitations: list[str]
    unanswered_subquestions: list[str]
    requested_followup_tools: list[PlannedToolCall]
```

Each proposed statement must include:

- statement text;
- claim type;
- supporting evidence IDs;
- qualifying evidence IDs;
- contradicting evidence IDs;
- confidence class;
- direct or inferred status;
- temporal scope.

The Analyst cannot introduce an uncited material statement.

## 5. Agent 3 — Historical Critic

### Responsibility

Challenge the analysis before it reaches the user.

Checks include:

- chronology mistaken for causation;
- later knowledge projected backward;
- source dependence;
- missing counterevidence;
- disputed interpretation presented as settled;
- source-role confusion;
- primary/secondary confusion;
- unsupported location precision;
- incomplete date qualification;
- overbroad generalization;
- claim absent from retrieved evidence;
- failure to abstain.

```python
class CriticDecision(BaseModel):
    verdict: Literal[
        "approve",
        "approve_with_downgrades",
        "retrieve_more",
        "reject",
        "abstain",
    ]
    accepted_statement_ids: list[str]
    downgraded_statements: list[Downgrade]
    rejected_statements: list[Rejection]
    additional_tool_calls: list[PlannedToolCall]
    limitations_to_surface: list[str]
    rationale_summary: str
```

Expose only a concise rationale summary, not private chain-of-thought.

Allow only a small bounded number of retrieval/critique loops. If the answer remains unsupported, abstain.

## 6. Agent 4 — Investigation Guide

### Responsibility

Turn only critic-approved material into a user-facing answer and typed workspace actions.

```python
class AgentAnswer(BaseModel):
    direct_answer: str
    key_points: list[AnswerPoint]
    disagreements: list[AnswerPoint]
    limitations: list[str]
    citations: list[Citation]
    suggested_questions: list[str]
    actions: list[AssistantAction]
```

The Guide cannot add new factual content, cite absent records, issue arbitrary frontend code, or hide uncertainty.

## 7. Typed workspace actions

Initial actions:

```text
FOCUS_LOCATION
FOCUS_EVENT
SET_TIME
SET_TIME_RANGE
ACTIVATE_LENS
HIGHLIGHT_EVENTS
HIGHLIGHT_RELATIONSHIP
SHOW_SYSTEM_PATH
COMPARE_ACTORS
OPEN_EVIDENCE
OPEN_SOURCE
RESET_VIEW
```

Validation must ensure every referenced ID exists and every action is supported by the current investigation.

## 8. Agent run records

Persist:

- run ID;
- user question;
- context snapshot;
- model provider, name, and version;
- prompt versions;
- tool calls;
- tool outputs or hashes;
- planner result;
- analysis result;
- critic result;
- final answer;
- validation results;
- token use;
- latency;
- retries;
- error states;
- abstention reason.

Do not persist private chain-of-thought.

## 9. Model-provider abstraction

Support:

- deterministic test provider;
- one real development provider;
- future local/open-weight provider;
- future fine-tuned Chronicle task model.

Initial capabilities:

```text
generate_structured
generate_text_from_verified_records
health_check
model_metadata
```

Embeddings can be introduced separately.

## 10. Learning objectives

Create `docs/ai/learning-log.md` and record:

- where agents improved performance;
- where deterministic code was better;
- how tool descriptions affected selection;
- structured-output failures;
- critic effects on unsupported claims;
- latency and cost changes;
- what should later be fine-tuned.
