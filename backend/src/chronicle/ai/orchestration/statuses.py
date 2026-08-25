"""Agent-run status taxonomy (Phase E1 scaffolding) -- same shape as
workflow/stages.py's RunStatus, deliberately not reused directly: an agent
run's terminal states have different meaning (e.g. ABSTAINED is a routine,
expected Critic outcome here, not a rare package-generation edge case) even
though the state names overlap.
"""

from __future__ import annotations

from enum import Enum


class AgentRunStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    ANALYSIS_READY = "analysis_ready"
    ANSWER_READY = "answer_ready"
    PARTIAL = "partial"
    ABSTAINED = "abstained"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"
    FAILED = "failed"
