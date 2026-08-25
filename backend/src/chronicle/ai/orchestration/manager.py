"""Single-worker execution and replayable public progress for Phase E5."""

from __future__ import annotations

from collections import defaultdict, deque
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Condition, Event, RLock
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from ...corpus.manifest import CorpusRegistry
from ...storage.agent_run_store import AgentRunStore
from ..contracts.run import AgentRunRecord, AgentStageName
from .sequential import WorkflowSignal, WorkflowSignalType
from .statuses import AgentRunStatus


class AgentRunManagerError(RuntimeError):
    pass


class AgentRunAlreadyExistsError(AgentRunManagerError):
    pass


class AgentRunAlreadyActiveError(AgentRunManagerError):
    pass


class AgentRunNotResumableError(AgentRunManagerError):
    pass


class AgentRunNotCancellableError(AgentRunManagerError):
    pass


class AgentRunEvent(BaseModel):
    """A bounded, user-safe event suitable for polling or SSE."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    sequence: int = Field(ge=1)
    runId: str = Field(min_length=1, max_length=100)
    type: WorkflowSignalType
    stage: AgentStageName | None = None
    round: int = Field(default=0, ge=0, le=1)
    message: str = Field(min_length=1, max_length=300)
    occurredAt: datetime


class AgentRunEventJournal:
    """Thread-safe, bounded event journals with reconnect replay support."""

    def __init__(self, *, maximum_events_per_run: int = 256) -> None:
        if maximum_events_per_run < 8:
            raise ValueError("maximum_events_per_run must be at least 8")
        self._maximum = maximum_events_per_run
        self._events: dict[str, deque[AgentRunEvent]] = defaultdict(
            lambda: deque(maxlen=self._maximum)
        )
        self._next_sequence: dict[str, int] = defaultdict(lambda: 1)
        self._condition = Condition(RLock())

    def append(self, run_id: str, signal: WorkflowSignal) -> AgentRunEvent:
        with self._condition:
            event = AgentRunEvent(
                sequence=self._next_sequence[run_id],
                runId=run_id,
                type=signal.type,
                stage=signal.stage,
                round=signal.round,
                message=signal.message,
                occurredAt=datetime.now(timezone.utc),
            )
            self._next_sequence[run_id] += 1
            self._events[run_id].append(event)
            self._condition.notify_all()
            return event

    def list_after(self, run_id: str, after_sequence: int = 0) -> list[AgentRunEvent]:
        if after_sequence < 0:
            raise ValueError("after_sequence cannot be negative")
        with self._condition:
            return [event for event in self._events.get(run_id, ()) if event.sequence > after_sequence]

    def wait_after(
        self,
        run_id: str,
        after_sequence: int,
        *,
        timeout: float,
    ) -> list[AgentRunEvent]:
        with self._condition:
            current = self.list_after(run_id, after_sequence)
            if current:
                return current
            self._condition.wait(timeout=timeout)
            return self.list_after(run_id, after_sequence)


class _SequentialWorkflow(Protocol):
    def run(self, record, corpus, *, emit, should_cancel) -> AgentRunRecord: ...


class AgentRunManager:
    """Own one project-wide worker so agent runs never overlap."""

    def __init__(
        self,
        *,
        workflow: _SequentialWorkflow,
        store: AgentRunStore,
        corpus_registry: CorpusRegistry,
        event_journal: AgentRunEventJournal | None = None,
    ) -> None:
        self.workflow = workflow
        self.store = store
        self.corpus_registry = corpus_registry
        self.event_journal = event_journal or AgentRunEventJournal()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="chronicle-agent")
        self._futures: dict[str, Future[AgentRunRecord]] = {}
        self._cancellations: dict[str, Event] = {}
        self._lock = RLock()

    def submit(self, record: AgentRunRecord) -> AgentRunRecord:
        with self._lock:
            if self.store.run_exists(record.runId):
                raise AgentRunAlreadyExistsError(f'Agent run "{record.runId}" already exists')
            self.store.save_run(record)
            self._enqueue(record.runId)
        return record

    def resume(self, run_id: str) -> AgentRunRecord:
        with self._lock:
            active = self._futures.get(run_id)
            if active is not None and not active.done():
                raise AgentRunAlreadyActiveError(f'Agent run "{run_id}" is already active')
            record = self.store.load_run(run_id)
            if record.status in {AgentRunStatus.ANSWER_READY, AgentRunStatus.ABSTAINED}:
                raise AgentRunNotResumableError(
                    f'Agent run "{run_id}" already reached a final answer state'
                )
            self._enqueue(run_id)
            return record

    def cancel(self, run_id: str) -> AgentRunRecord:
        with self._lock:
            record = self.store.load_run(run_id)
            active = self._futures.get(run_id)
            if active is None or active.done():
                if record.status is AgentRunStatus.CANCELLED:
                    return record
                raise AgentRunNotCancellableError(
                    f'Agent run "{run_id}" is not active and cannot be cancelled'
                )
            cancellation = self._cancellations.setdefault(run_id, Event())
            cancellation.set()
            return record

    def get(self, run_id: str) -> AgentRunRecord:
        return self.store.load_run(run_id)

    def events(self, run_id: str, *, after_sequence: int = 0) -> list[AgentRunEvent]:
        return self.event_journal.list_after(run_id, after_sequence)

    def wait_for_events(
        self,
        run_id: str,
        *,
        after_sequence: int,
        timeout: float,
    ) -> list[AgentRunEvent]:
        return self.event_journal.wait_after(run_id, after_sequence, timeout=timeout)

    def wait(self, run_id: str, *, timeout: float | None = None) -> AgentRunRecord:
        with self._lock:
            future = self._futures.get(run_id)
        if future is None:
            return self.store.load_run(run_id)
        return future.result(timeout=timeout)

    def shutdown(self, *, wait: bool = True) -> None:
        self._executor.shutdown(wait=wait, cancel_futures=False)

    def _enqueue(self, run_id: str) -> None:
        cancellation = Event()
        self._cancellations[run_id] = cancellation
        self._futures[run_id] = self._executor.submit(self._execute, run_id, cancellation)

    def _execute(self, run_id: str, cancellation: Event) -> AgentRunRecord:
        try:
            record = self.store.load_run(run_id)
            corpus = self.corpus_registry.get_corpus(record.request.corpusId)
            result = self.workflow.run(
                record,
                corpus,
                emit=lambda signal: self.event_journal.append(run_id, signal),
                should_cancel=cancellation.is_set,
            )
            self.store.save_run(result)
            return result
        finally:
            with self._lock:
                if self._cancellations.get(run_id) is cancellation:
                    self._cancellations.pop(run_id, None)


__all__ = [
    "AgentRunAlreadyActiveError",
    "AgentRunAlreadyExistsError",
    "AgentRunEvent",
    "AgentRunEventJournal",
    "AgentRunManager",
    "AgentRunManagerError",
    "AgentRunNotCancellableError",
    "AgentRunNotResumableError",
]
