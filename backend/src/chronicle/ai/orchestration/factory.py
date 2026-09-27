"""Shared construction of the production investigation workflow.

One builder so the deployed API (``api/app.py: create_default_app``) and the E7
``full_workflow`` evaluation strategy exercise the *same* configuration --
execution policy/budgets, the guaranteed passage-retrieval floor, and the
planner tool-spec representation -- instead of drifting. Evaluation must not copy
these settings into a parallel path; it calls this builder.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..agents import (
    EvidenceAnalyst,
    HistoricalCritic,
    InvestigationGuide,
    InvestigationPlanner,
)
from ..agents.planner_prompt import ToolSpecRepresentation
from ..tools import build_default_registry
from .finalization import FinalizationRunner
from .graph import LangGraphAgentWorkflow
from .policies import AgentExecutionPolicy
from .runner import InvestigationRunner

if TYPE_CHECKING:  # only a parameter annotation -- keep the import lazy
    from ..models.protocol import ModelProvider
    from ...storage.agent_run_store import AgentRunStore


def default_execution_policy() -> AgentExecutionPolicy:
    """The deployed execution policy.

    Evidence-window budgets are tuned for local-model prompt-processing speed:
    on a CPU-only host the analyst re-reads its whole retrieval bundle, so the
    aggregate window is capped at 8k characters (the schema ceiling is 14k) and
    per-tool results at 2. The runner truncates gracefully rather than rejecting.
    """

    return AgentExecutionPolicy(
        maxResultsPerTool=2,
        maxAggregateRetrievalCharacters=8_000,
    )


def build_default_workflow(
    provider: "ModelProvider",
    store: "AgentRunStore",
    *,
    policy: AgentExecutionPolicy | None = None,
) -> LangGraphAgentWorkflow:
    """Build the production four-agent workflow shared by the API and E7.

    Encodes the deployed configuration in one place: the default execution
    policy, the guaranteed passage-retrieval floor (so an auto-acquired,
    passages-only corpus still gets one bounded ``search_passages`` even when the
    planner picks a tool that retrieves nothing), and the COMPACT planner
    tool-spec representation. All agents share one provider and one policy.
    """

    policy = policy or default_execution_policy()
    analyst = EvidenceAnalyst(provider, policy)
    retrieval = InvestigationRunner(
        build_default_registry(), store=store, policy=policy, retrieval_floor=True
    )
    return LangGraphAgentWorkflow(
        planner=InvestigationPlanner(
            provider, policy, representation=ToolSpecRepresentation.COMPACT
        ),
        retrieval_runner=retrieval,
        analyst=analyst,
        finalization_runner=FinalizationRunner(
            retrieval_runner=retrieval,
            analyst=analyst,
            critic=HistoricalCritic(provider, policy),
            guide=InvestigationGuide(provider, policy),
            store=store,
        ),
        store=store,
    )
