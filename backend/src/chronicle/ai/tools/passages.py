"""search_passages tool (Phase E2). Thin wrapper over
corpus.search_passages -- the corpus layer already returns the typed,
bounded, explainable-scored result this tool needs, so this file only
declares the ToolDefinition."""

from __future__ import annotations

from ...corpus.contracts import MAX_RESULT_COUNT, PassageSearchRequest, PassageSearchResult
from ...corpus.protocol import InvestigationCorpus
from .contracts import ToolExecutionContext
from .registry import ToolDefinition

TOOL_VERSION = "e2-search-passages-v2"

DESCRIPTION = (
    "Search stored passage-level evidence within one Chronicle corpus, preserving "
    "document visibility, source curation, and target review metadata. "
    "Use this tool when a question requires source passages, exact wording, "
    "or evidence linked to claims, relationships, and events, or passages "
    "mentioning selected entity names or aliases. "
    "This tool does not search the public internet and does not generate "
    "historical conclusions."
)


def _execute(
    tool_input: PassageSearchRequest,
    context: ToolExecutionContext,
    corpus: InvestigationCorpus,
) -> PassageSearchResult:
    effective_limit = min(tool_input.maxResults, context.maximumResults)
    return corpus.search_passages(tool_input.model_copy(update={"maxResults": effective_limit}))


SEARCH_PASSAGES_TOOL = ToolDefinition(
    name="search_passages",
    version=TOOL_VERSION,
    description=DESCRIPTION,
    input_model=PassageSearchRequest,
    output_model=PassageSearchResult,
    required_capabilities=frozenset({"passages"}),
    max_result_limit=MAX_RESULT_COUNT,
    use_when="A question needs exact source wording or passage-level evidence from this corpus.",
    avoid_when="The question requires public-web discovery or a historical conclusion rather than retrieval.",
    output_summary=(
        "Bounded ranked passages with field-specific score factors, scoped evidence links, "
        "and time-role matches."
    ),
    execute=_execute,
)
