"""Every string-enum used by the GeneratedInvestigation contract.

Mirrors the enums scattered across
src/features/investigation/model/schema.ts and
src/features/investigation/model/generatedInvestigation.ts, one section
each, in the same order they appear there. Keep values and membership in
exact sync with those two files — that's the entire point of Phase C0.
"""

from enum import Enum


class DatePrecision(str, Enum):
    EXACT = "exact"
    APPROXIMATE = "approximate"
    RANGE = "range"
    DISPUTED = "disputed"


class LocationPrecision(str, Enum):
    BUILDING = "building"
    CITY = "city"
    REGION = "region"
    APPROXIMATE = "approximate"


class ReviewStatus(str, Enum):
    PROPOSED = "proposed"
    REVIEWED = "reviewed"
    DISPUTED = "disputed"
    REJECTED = "rejected"


class CurationStatus(str, Enum):
    IDENTIFIED = "identified"
    ACQUIRED = "acquired"
    PASSAGES_EXTRACTED = "passages-extracted"
    PROTOTYPE_CURATED = "prototype-curated"
    REVIEWED = "reviewed"


class Visibility(str, Enum):
    PUBLIC = "public"
    PRIVATE_WORKSPACE = "private-workspace"


class DirectOrInferred(str, Enum):
    DIRECT = "direct"
    INFERRED = "inferred"


class EvidenceClassification(str, Enum):
    DIRECTLY_SUPPORTED = "directly_supported"
    INDIRECTLY_SUPPORTED = "indirectly_supported"
    CONTEXTUAL = "contextual"
    CORRELATIONAL = "correlational"
    DISPUTED = "disputed"
    SPECULATIVE = "speculative"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class EvidenceLinkRole(str, Enum):
    SUPPORTING = "supporting"
    COUNTEREVIDENCE = "counterevidence"
    CONTEXT = "context"


class SourceType(str, Enum):
    PRIMARY_OFFICIAL_DIPLOMATIC = "primary-official-diplomatic"
    PRIMARY_PERSONAL = "primary-personal"
    PRIMARY_PRESS = "primary-press"
    SECONDARY_SPECIALIST = "secondary-specialist"
    SECONDARY_GENERAL = "secondary-general"
    TERTIARY_REFERENCE = "tertiary-reference"


class RightsStatus(str, Enum):
    PUBLIC_DOMAIN = "public-domain"
    LICENSED = "licensed"
    NEEDS_PERMISSION = "needs-permission"
    UNKNOWN = "unknown"


# --- generatedInvestigation.ts-only enums ------------------------------

class PackageStatus(str, Enum):
    DRAFT = "draft"
    PARTIAL = "partial"
    VERIFIED = "verified"
    REVIEWED = "reviewed"
    PUBLISHED = "published"


class RequestType(str, Enum):
    CAUSAL_INVESTIGATION = "causal-investigation"
    COMPARATIVE_INVESTIGATION = "comparative-investigation"
    EVENT_RECONSTRUCTION = "event-reconstruction"
    ACTOR_INVESTIGATION = "actor-investigation"


class RequestedDepth(str, Enum):
    FOCUSED = "focused"
    STANDARD = "standard"
    DEEP = "deep"


class ApprovalStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REVISED = "revised"


class EvidenceTargetType(str, Enum):
    CLAIM = "claim"
    RELATIONSHIP = "relationship"
    KNOWN_AT_TIME = "knownAtTime"
    EVENT = "event"
    CONTROL_STATE = "controlState"


class Awareness(str, Enum):
    KNOWN = "known"
    NOT_YET_KNOWN = "not-yet-known"


class FindingRecordType(str, Enum):
    CLAIM = "claim"
    RELATIONSHIP = "relationship"
    KNOWLEDGE_STATE = "knowledge-state"


class FindingImportance(str, Enum):
    MAJOR = "major"
    SUPPORTING = "supporting"


class LedgerConclusion(str, Enum):
    SUPPORTED = "supported"
    QUALIFIED = "qualified"
    DISPUTED = "disputed"
    INSUFFICIENT_EVIDENCE = "insufficient-evidence"


class MapAssetPeriodFitDecision(str, Enum):
    APPROVED = "approved"
    CONDITIONAL = "conditional"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


class GeoreferencingPrecision(str, Enum):
    REGION = "region"
    APPROXIMATE = "approximate"


class FocusKind(str, Enum):
    SCENE = "scene"
    EVENT = "event"
    ENTITY = "entity"
    CLAIM = "claim"
    RELATIONSHIP = "relationship"
    SOURCE = "source"
    PASSAGE = "passage"
    TIME_RANGE = "timeRange"


class Facet(str, Enum):
    NARRATIVE = "narrative"
    TIMELINE = "timeline"
    MAP = "map"
    GRAPH = "graph"
    EVIDENCE = "evidence"
    TERRITORY = "territory"


class ControlStateKind(str, Enum):
    CONTROLLED = "controlled"
    INFLUENCE = "influence"
    CONTESTED = "contested"


class ControlBasis(str, Enum):
    """The de jure ↔ de facto nature of `controlled` territory: a polity's own
    recognized homeland (sovereign), another polity's land held by force
    (occupied), or land governed without homeland sovereignty — colony,
    protectorate, mandate, client/puppet (administered)."""

    SOVEREIGN = "sovereign"
    OCCUPIED = "occupied"
    ADMINISTERED = "administered"


class GeometryType(str, Enum):
    POLYGON = "Polygon"
    MULTI_POLYGON = "MultiPolygon"


class GenerationOutcome(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"
    ABSTAINED = "abstained"


class StageStatus(str, Enum):
    PASSED = "passed"
    PARTIAL = "partial"
    FAILED = "failed"
    ABSTAINED = "abstained"
    SKIPPED = "skipped"


class VerificationCheckStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    ABSTAINED = "abstained"


# --- experiencePlan.ts-only enums (Phase D, ADR-002) --------------------

class PanelTab(str, Enum):
    ASK = "ask"
    EXPLORE = "explore"
    EVIDENCE = "evidence"
    SOURCES = "sources"


class EvidenceDepth(str, Enum):
    SHALLOW = "shallow"
    STANDARD = "standard"
    DEEP = "deep"


class LensVisualization(str, Enum):
    MAP = "map"
    GRAPH = "graph"
