"""Public surface for the deterministic Phase E3 evaluation harness."""

from .benchmark import (
    BenchmarkCase,
    BenchmarkReferenceIssue,
    BenchmarkReferenceValidationReport,
    BenchmarkValidationError,
    TemporalConstraint,
    TemporalConstraintKind,
    load_e3_benchmark,
    validate_benchmark_references,
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
    "EvaluationResult",
    "ExecutionMeasurements",
    "ObservationAvailability",
    "TemporalConstraint",
    "TemporalConstraintKind",
    "evaluate_case",
    "load_e3_benchmark",
    "observe_execution_budgets",
    "validate_benchmark_references",
]
