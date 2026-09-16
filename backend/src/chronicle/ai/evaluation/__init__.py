"""Public surface for the deterministic evaluation harness (E3 + E7 spine)."""

from .benchmark import (
    BenchmarkCase,
    BenchmarkReferenceIssue,
    BenchmarkReferenceValidationReport,
    BenchmarkValidationError,
    TemporalConstraint,
    TemporalConstraintKind,
    load_e3_benchmark,
    load_evaluation_benchmark,
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

__all__ = [
    "BenchmarkCase",
    "BenchmarkReferenceIssue",
    "BenchmarkReferenceValidationReport",
    "BenchmarkValidationError",
    "BudgetObservation",
    "EvaluationCase",
    "EvaluationProfile",
    "EvaluationResult",
    "ExecutionMeasurements",
    "ObservationAvailability",
    "SemanticCheck",
    "StrategyId",
    "TemporalConstraint",
    "TemporalConstraintKind",
    "evaluate_case",
    "load_e3_benchmark",
    "load_evaluation_benchmark",
    "observe_execution_budgets",
    "validate_benchmark_references",
    "validate_evaluation_references",
]
