"""Composes the Concert of Europe curated stage functions into the same
StageName -> StageFn shape providers/registry.py uses for MOCK_STAGE_FNS —
engine.py needs no changes to run this provider set."""

from ....workflow.stages import StageName
from ...verification import verify_investigation
from .claims import extract_claims
from .composition import compose_investigation
from .corpus import assemble_corpus
from .entities import extract_entities
from .events import extract_events
from .geography import assemble_geography
from .relationships import propose_relationships
from .sources import assess_sources, discover_source_candidates, prepare_discovery_queries, propose_scope
from .timeline import build_timeline

CONCERT_OF_EUROPE_PROVIDER_SET_VERSION = "c3-concert-of-europe-v1"


def _compose(*fns):
    def combined(data: dict) -> dict:
        for fn in fns:
            data = fn(data)
        return data

    return combined


CONCERT_OF_EUROPE_STAGE_FNS = {
    StageName.SCOPE_PROPOSED: propose_scope,
    StageName.DISCOVERY_QUERIES_PREPARED: prepare_discovery_queries,
    StageName.SOURCE_CANDIDATES_DISCOVERED: discover_source_candidates,
    StageName.SOURCES_ASSESSED: assess_sources,
    StageName.CORPUS_PREPARED: assemble_corpus,
    StageName.HISTORICAL_MODEL_ASSEMBLED: _compose(
        extract_entities, extract_events, extract_claims, propose_relationships, build_timeline, assemble_geography
    ),
    StageName.INVESTIGATION_COMPOSED: compose_investigation,
    StageName.VERIFIED: verify_investigation,
}
