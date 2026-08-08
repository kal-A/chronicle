"""The Phase E2 typed tool set: 10 deterministic tools over an existing
GeneratedInvestigation corpus, registered into one shared ToolRegistry so
a future Planner (E3) can discover them without importing any tool's
implementation module.

Deferred (not built in E2, documented per the approved plan's decision 2):
compare_perspectives, find_conflicts, get_research_gaps -- the three
extra tools docs/ai-core-instructions/02_AGENT_ARCHITECTURE.md §3 lists
beyond the 10 in docs/ai-core-instructions/05_PHASE_E_AI_CORE_IMPLEMENTATION_PLAN.md's
E2 section. Both fixtures have zero perspectives/conflicts/researchGaps
records (all typed as ExtensionRecord, Chronicle's own contract doesn't
give them dedicated shapes yet) -- there is nothing real for these three
tools to operate on today.
"""

from __future__ import annotations

from .contracts import (
    DEFAULT_TOOL_OUTPUT_CHARACTER_LIMIT,
    DEFAULT_TOOL_RESULT_LIMIT,
    MAX_TOOL_OUTPUT_CHARACTER_LIMIT,
    MAX_TOOL_RESULT_LIMIT,
    EvidenceLinkProjection,
    ToolCallRecord,
    ToolCallStatus,
    ToolExecutionContext,
    ToolSpec,
)
from .errors import (
    CorpusMismatchError,
    CorpusRetrievalError,
    DuplicateToolNameError,
    InternalRetrievalError,
    MalformedToolInputError,
    MalformedToolOutputError,
    PathDepthExceededError,
    ResultLimitExceededError,
    ToolError,
    UnauthorizedToolError,
    UnknownToolError,
    UnsupportedCapabilityError,
)
from .evidence import FIND_COUNTEREVIDENCE_TOOL, GET_CLAIM_EVIDENCE_TOOL
from .knowledge import GET_ACTOR_KNOWLEDGE_STATE_TOOL
from .map_context import GET_MAP_CONTEXT_TOOL
from .passages import SEARCH_PASSAGES_TOOL
from .registry import ToolDefinition, ToolRegistry
from .relationships import GET_RELATIONSHIP_EVIDENCE_TOOL, TRACE_RELATIONSHIPS_TOOL
from .sources import COMPARE_SOURCES_TOOL, GET_SOURCE_METADATA_TOOL
from .timeline import GET_TIMELINE_CONTEXT_TOOL

BUILT_IN_TOOL_DEFINITIONS: list[ToolDefinition] = [
    SEARCH_PASSAGES_TOOL,
    GET_SOURCE_METADATA_TOOL,
    COMPARE_SOURCES_TOOL,
    GET_CLAIM_EVIDENCE_TOOL,
    FIND_COUNTEREVIDENCE_TOOL,
    GET_RELATIONSHIP_EVIDENCE_TOOL,
    TRACE_RELATIONSHIPS_TOOL,
    GET_TIMELINE_CONTEXT_TOOL,
    GET_ACTOR_KNOWLEDGE_STATE_TOOL,
    GET_MAP_CONTEXT_TOOL,
]


def build_default_registry() -> ToolRegistry:
    """A fresh ToolRegistry with all 10 built-in tools registered --
    fresh per call, never a shared mutable module-level singleton, so
    tests (and a future runner) can register/unregister freely without
    cross-test leakage."""
    registry = ToolRegistry()
    for definition in BUILT_IN_TOOL_DEFINITIONS:
        registry.register(definition)
    return registry


__all__ = [
    "ToolCallRecord",
    "ToolCallStatus",
    "ToolExecutionContext",
    "ToolSpec",
    "EvidenceLinkProjection",
    "DEFAULT_TOOL_RESULT_LIMIT",
    "MAX_TOOL_RESULT_LIMIT",
    "DEFAULT_TOOL_OUTPUT_CHARACTER_LIMIT",
    "MAX_TOOL_OUTPUT_CHARACTER_LIMIT",
    "ToolError",
    "UnknownToolError",
    "DuplicateToolNameError",
    "MalformedToolInputError",
    "MalformedToolOutputError",
    "UnauthorizedToolError",
    "UnsupportedCapabilityError",
    "CorpusMismatchError",
    "CorpusRetrievalError",
    "ResultLimitExceededError",
    "PathDepthExceededError",
    "InternalRetrievalError",
    "ToolDefinition",
    "ToolRegistry",
    "BUILT_IN_TOOL_DEFINITIONS",
    "build_default_registry",
]
