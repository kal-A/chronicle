"""Prompts and the evaluation-only answer contract for the two baselines.

These are used ONLY by the evaluation harness to give the single-prompt and
basic-RAG strategies a comparable structured answer; they are not a production
answer path. No benchmark rubric field (semantic checks, usefulness criteria,
expected abstention, expected evidence) is ever referenced here, so a gold label
can never reach a model prompt.
"""

from __future__ import annotations

import hashlib

from pydantic import BaseModel, ConfigDict, Field

from ..contracts.analysis import AnalysisCitation, AnswerStatus

SINGLE_PROMPT_PROMPT_VERSION = "eval-single-prompt-v1"
BASIC_RAG_PROMPT_VERSION = "eval-basic-rag-v1"

#: Sentinel toolCallId for baseline citations (baselines make no typed tool
#: call). Deterministic-scoring only checks record ids, not this field.
_BASELINE_CALL = "baseline"


class EvaluationAnswerStatement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=1_200)
    citations: list[AnalysisCitation] = Field(default_factory=list, max_length=6)


class EvaluationAnswer(BaseModel):
    """The structured answer a baseline strategy returns. Same answer/citation/
    status shape the agent path produces, minus the agent-only machinery."""

    model_config = ConfigDict(extra="forbid")

    status: AnswerStatus
    directAnswer: str = Field(min_length=1, max_length=4_000)
    statements: list[EvaluationAnswerStatement] = Field(default_factory=list, max_length=8)


_ANSWER_INSTRUCTIONS = (
    "You are a careful historical research assistant. Answer the question using "
    "ONLY the provided corpus records. Cite the passage or source records you "
    "rely on by their exact ids. If the records do not support an answer, set "
    "status to \"abstained\" and explain the evidence gap. Never assert anything "
    "the records do not support."
)


def single_prompt_system() -> str:
    return _ANSWER_INSTRUCTIONS


def single_prompt_user(question: str, context: str) -> str:
    return f"Question:\n{question}\n\nCorpus records:\n{context}"


def basic_rag_system() -> str:
    return _ANSWER_INSTRUCTIONS


def basic_rag_user(question: str, retrieved: str) -> str:
    return f"Question:\n{question}\n\nRetrieved passages:\n{retrieved}"


def _passage_order_key(benchmark_version: str, passage_id: str) -> str:
    return hashlib.sha256(f"{benchmark_version}:{passage_id}".encode("utf-8")).hexdigest()


def build_single_prompt_context(
    corpus, aggregate_character_budget: int, benchmark_version: str
) -> tuple[str, tuple[str, ...]]:
    """Assemble a corpus-independent, retrieval-free context for the single
    prompt baseline. Passages are ordered by a stable hash of
    ``benchmark_version + passage id`` (never the question), and whole excerpts
    are added until the aggregate character budget would be exceeded -- no
    truncation, no question-driven selection. Returns the serialized context and
    the ids of the passages included, so the caller can report what was offered.
    """
    investigation = corpus.get_investigation()
    passages = sorted(
        investigation.passages,
        key=lambda passage: _passage_order_key(benchmark_version, passage.id),
    )
    lines: list[str] = []
    included: list[str] = []
    used = 0
    for passage in passages:
        record = f"[passage {passage.id} | document {passage.documentId}] {passage.excerpt}"
        if used + len(record) > aggregate_character_budget:
            continue
        lines.append(record)
        included.append(passage.id)
        used += len(record)
    return "\n".join(lines), tuple(included)


__all__ = [
    "SINGLE_PROMPT_PROMPT_VERSION",
    "BASIC_RAG_PROMPT_VERSION",
    "EvaluationAnswer",
    "EvaluationAnswerStatement",
    "single_prompt_system",
    "single_prompt_user",
    "basic_rag_system",
    "basic_rag_user",
    "build_single_prompt_context",
]
