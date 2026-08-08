"""Small deterministic budgets for bounding nested retrieval collections."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class CollectionBudget:
    limit: int
    used: int = 0

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.used)

    def take(self, values: list[T]) -> list[T]:
        returned = values[: self.remaining]
        self.used += len(returned)
        return returned
