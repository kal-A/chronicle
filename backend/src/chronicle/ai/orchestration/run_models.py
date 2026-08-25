"""Compatibility import path for the Phase E3 run contracts."""

from ..contracts.run import AgentRunRecord, InvestigationRequest, utcnow

AGENT_RUNTIME_VERSION = "e5-agent-runtime-v1"

__all__ = ["AGENT_RUNTIME_VERSION", "AgentRunRecord", "InvestigationRequest", "utcnow"]
