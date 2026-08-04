"""Composes the 9 mock providers + verification into the stage-function set
`chronicle generate`/`resume` use by default, replacing C1's stubs without
any change to engine.py's stage-execution contract (StageFn is still just
Callable[[dict], dict])."""

from ..workflow.stages import StageName
from .mock.assessment import assess_sources
from .mock.composition import compose_investigation
from .mock.corpus import assemble_corpus
from .mock.discovery import prepare_discovery_queries
from .mock.extraction import extract_historical_model
from .mock.geography import assemble_geography
from .mock.relationships import propose_relationships
from .mock.scope import propose_scope
from .mock.source_candidates import discover_source_candidates
from .mock.timeline import build_timeline
from .verification import verify_investigation

MOCK_PROVIDER_SET_VERSION = "c2-mock-v1"


def _compose(*fns):
    def combined(data: dict) -> dict:
        for fn in fns:
            data = fn(data)
        return data

    return combined


MOCK_STAGE_FNS = {
    StageName.SCOPE_PROPOSED: propose_scope,
    StageName.DISCOVERY_QUERIES_PREPARED: prepare_discovery_queries,
    StageName.SOURCE_CANDIDATES_DISCOVERED: discover_source_candidates,
    StageName.SOURCES_ASSESSED: assess_sources,
    StageName.CORPUS_PREPARED: assemble_corpus,
    StageName.HISTORICAL_MODEL_ASSEMBLED: _compose(
        extract_historical_model, build_timeline, propose_relationships, assemble_geography
    ),
    StageName.INVESTIGATION_COMPOSED: compose_investigation,
    StageName.VERIFIED: verify_investigation,
}
