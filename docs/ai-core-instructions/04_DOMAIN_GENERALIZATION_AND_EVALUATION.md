<!-- See 00_START_HERE.md for the encoding-fix note that applies to this whole instruction set. -->

# Chronicle — Domain Generalization and AI Evaluation

[← Retrieval and MCP infrastructure](./03_RETRIEVAL_SOURCE_AND_MCP_INFRASTRUCTURE.md) · [Next: Phase E implementation →](./05_PHASE_E_AI_CORE_IMPLEMENTATION_PLAN.md)

## 1. Goal

Prevent Chronicle from becoming a Concert of Europe research paper with reusable components around it.

Historical topics are evaluation environments for the AI system. They must not become application architecture.

## 2. Rename the role of current content

Treat current investigations as benchmarks:

- **Benchmark A — Concert of Europe:** modern diplomatic and intervention history.
- **Benchmark B — Blank Cheque / July Crisis:** crisis escalation, communications, knowledge, and causation.

Topic-specific code and data belong under benchmark or fixture namespaces.

Good:

```text
providers/openalex.py
providers/internet_archive.py
benchmarks/concert_of_europe/
```

Bad:

```text
providers/concert_of_europe.py
```

An event is not a production provider.

## 3. Add diverse small benchmark corpora

Do not build several polished investigations. Build compact evaluation corpora.

### Benchmark C — Haitian Revolution

Tests:

- colonial and revolutionary perspectives;
- Atlantic geography;
- terminology and identity;
- multilingual or translated sources;
- unequal archival coverage;
- communication delay.

### Benchmark D — Caesar in Egypt

Tests:

- ancient primary narratives;
- later historiography;
- translation;
- uncertain chronology;
- ancient/modern place aliases;
- weak causal inference.

### Benchmark E — twentieth-century crisis

Choose a bounded case with accessible official records.

Tests:

- communications;
- rapid chronology;
- declassified records;
- knowledge-state reasoning;
- source abundance;
- conflicting retrospective accounts.

Each small corpus initially needs only:

- 3–5 sources;
- 8–15 passages;
- 5–10 claims;
- 1–3 relationships;
- 5–10 evaluation questions;
- at least one abstention case.

## 4. Holdout corpus

Keep one corpus out of:

- prompt examples;
- few-shot examples;
- development debugging;
- fine-tuning data.

Use it only for evaluation.

## 5. No-topic-branching rule

Prohibit:

```python
if topic == "Concert of Europe":
    ...
```

and:

```tsx
if (investigation.id === "concert-of-europe") {
    ...
}
```

Topic-specific behavior must arrive through validated data, experience plans, corpus records, prompt inputs, or benchmark configuration.

Add static searches or tests for known topic IDs in generic application and agent files.

## 6. Prompt diversity

Do not fill prompts only with Troppau, Laibach, Castlereagh, and Verona.

Use:

- abstract examples;
- rotating cross-domain few-shots;
- prompt templates without event-specific names;
- separate benchmark fixtures.

No single topic should supply more than roughly one-third of evaluation questions, few-shot examples, retrieval tests, map-action tests, or training examples.

## 7. Initial evaluation suite

Create 20–30 reviewed questions across at least two corpora, then expand.

Question classes:

- direct evidence;
- explanation;
- relationship trace;
- comparison;
- knowledge state;
- disagreement;
- temporal ordering;
- missing evidence;
- out-of-corpus;
- invalid premise.

## 8. Metrics

### Grounding

- citation validity;
- citation relevance;
- unsupported-claim rate;
- evidence coverage;
- counterevidence inclusion.

### Reasoning

- temporal consistency;
- relationship classification;
- knowledge-state accuracy;
- uncertainty preservation;
- correct abstention.

### Agent performance

- planner tool-selection accuracy;
- unnecessary tool-call count;
- critic correction rate;
- invalid structured-output rate;
- loop count;
- action validity.

### System performance

- latency;
- token use;
- cost;
- retry rate;
- failure recovery.

## 9. Baselines

Compare:

1. single-prompt answer;
2. basic RAG answer;
3. planner + retrieval + analyst;
4. planner + analyst + critic + guide;
5. later fine-tuned Chronicle task model.

The multi-agent design should be justified by measured improvements, not novelty.

## 10. Evaluation records

```python
class EvaluationCase(BaseModel):
    id: str
    corpus_id: str
    question: str
    question_type: QuestionType
    expected_claim_ids: list[str]
    expected_source_ids: list[str]
    required_counterevidence_ids: list[str]
    expected_action_types: list[str]
    should_abstain: bool
    notes: str
```

Create deterministic unit evals, human-reviewed gold cases, saved regression reports, and model-assisted scoring only where necessary.

## 11. Phase gate

No agent phase passes based on one historical event.

Required:

- at least two materially different corpora;
- one held-out corpus;
- unsupported questions abstain;
- no topic branching;
- cross-domain regression report;
- prompt changes evaluated across all benchmarks.
