"""Public surface for the deterministic evaluation harness (E3 + E7 spine)."""

from .benchmark import (
    BenchmarkCase,
    BenchmarkReferenceIssue,
    BenchmarkReferenceValidationReport,
    BenchmarkRegistry,
    BenchmarkValidationError,
    TemporalConstraint,
    TemporalConstraintKind,
    load_e3_benchmark,
    load_evaluation_benchmark,
    load_registry,
    validate_benchmark_references,
    validate_evaluation_references,
)
from .contracts import (
    EvaluationCase,
    EvaluationProfile,
    SemanticCheck,
    StrategyId,
)
from .metrics import (
    BudgetObservation,
    EvaluationResult,
    ExecutionMeasurements,
    ObservationAvailability,
    evaluate_case,
    observe_execution_budgets,
)
from .runner import (
    ProviderFactory,
    ResultIdentity,
    ResultRef,
    RunManifest,
    load_manifest,
    run_benchmark,
)

__all__ = [
    "BenchmarkCase",
    "BenchmarkReferenceIssue",
    "BenchmarkReferenceValidationReport",
    "BenchmarkRegistry",
    "BenchmarkValidationError",
    "BudgetObservation",
    "EvaluationCase",
    "EvaluationProfile",
    "EvaluationResult",
    "ExecutionMeasurements",
    "ObservationAvailability",
    "ProviderFactory",
    "ResultIdentity",
    "ResultRef",
    "RunManifest",
    "SemanticCheck",
    "StrategyId",
    "TemporalConstraint",
    "TemporalConstraintKind",
    "evaluate_case",
    "load_e3_benchmark",
    "load_evaluation_benchmark",
    "load_manifest",
    "load_registry",
    "observe_execution_budgets",
    "run_benchmark",
    "validate_benchmark_references",
    "validate_evaluation_references",
]
