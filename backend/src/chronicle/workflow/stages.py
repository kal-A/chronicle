"""The permanent domain-level stage taxonomy.

Names per chronicle_phase_c_adjusted_plan.md §4 — deliberately NOT
"mock"-prefixed, since these stay valid once Phase C2/D+ replace the C1 stub
providers with real ones. A run starts CREATED (before any stage has run),
moves through RUNNING while stages execute, and ends in exactly one of the
four RunStatus terminal states.
"""

from enum import Enum


class StageName(str, Enum):
    SCOPE_PROPOSED = "SCOPE_PROPOSED"
    DISCOVERY_QUERIES_PREPARED = "DISCOVERY_QUERIES_PREPARED"
    SOURCE_CANDIDATES_DISCOVERED = "SOURCE_CANDIDATES_DISCOVERED"
    SOURCES_ASSESSED = "SOURCES_ASSESSED"
    CORPUS_PREPARED = "CORPUS_PREPARED"
    HISTORICAL_MODEL_ASSEMBLED = "HISTORICAL_MODEL_ASSEMBLED"
    INVESTIGATION_COMPOSED = "INVESTIGATION_COMPOSED"
    VERIFIED = "VERIFIED"


STAGE_ORDER: list[StageName] = [
    StageName.SCOPE_PROPOSED,
    StageName.DISCOVERY_QUERIES_PREPARED,
    StageName.SOURCE_CANDIDATES_DISCOVERED,
    StageName.SOURCES_ASSESSED,
    StageName.CORPUS_PREPARED,
    StageName.HISTORICAL_MODEL_ASSEMBLED,
    StageName.INVESTIGATION_COMPOSED,
    StageName.VERIFIED,
]


class RunStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    READY = "ready"
    PARTIAL = "partial"
    ABSTAINED = "abstained"
    FAILED = "failed"


TERMINAL_RUN_STATUSES = {RunStatus.READY, RunStatus.PARTIAL, RunStatus.ABSTAINED, RunStatus.FAILED}


class StageRunStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    REUSED = "reused"
