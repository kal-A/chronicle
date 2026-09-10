"""FastAPI composition for queued, inspectable Chronicle agent runs."""

from __future__ import annotations

from contextlib import asynccontextmanager
import os
from pathlib import Path
from typing import Iterator
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from ..ai.agents import EvidenceAnalyst, HistoricalCritic, InvestigationGuide, InvestigationPlanner
from ..ai.agents.planner_prompt import ToolSpecRepresentation
from ..ai.contracts.run import AgentRunRecord, CorpusSnapshot, InvestigationRequest
from ..ai.models import OllamaModelProvider
from ..ai.orchestration.finalization import FinalizationRunner
from ..ai.orchestration.manager import (
    AgentRunAlreadyActiveError,
    AgentRunAlreadyExistsError,
    AgentRunEvent,
    AgentRunManager,
    AgentRunNotCancellableError,
    AgentRunNotResumableError,
)
from ..ai.orchestration.policies import AgentExecutionPolicy
from ..ai.orchestration.graph import LangGraphAgentWorkflow
from ..ai.orchestration.runner import InvestigationRunner
from ..ai.orchestration.statuses import AgentRunStatus
from ..ai.tools import build_default_registry
from ..acquisition.build_service import CorpusBuildService
from ..acquisition.defaults import default_pipeline
from ..acquisition.embeddings import OllamaEmbedder
from ..corpus import CorpusRegistry
from ..corpus.errors import UnknownCorpusError
from ..storage.agent_run_store import AgentRunNotFoundError, AgentRunStore
from ..acquisition.scope_resolver import ScopeResolver
from .contracts import (
    AgentRunAccepted,
    CorpusBuildAccepted,
    CorpusSummary,
    QuestionSubmission,
    RunIdFactory,
    ScopeResolutionRequest,
    ScopeResolutionResponse,
    TopicBuildSubmission,
)


_TERMINAL_STATUSES = {
    AgentRunStatus.ANSWER_READY,
    AgentRunStatus.ABSTAINED,
    AgentRunStatus.CANCELLED,
    AgentRunStatus.FAILED,
}


def create_app(
    *,
    manager: AgentRunManager,
    corpus_registry: CorpusRegistry,
    run_id_factory: RunIdFactory | None = None,
    build_service: CorpusBuildService | None = None,
    scope_resolver: ScopeResolver | None = None,
) -> FastAPI:
    """Create the HTTP app around injected runtime dependencies.

    ``build_service`` is optional: when present, the topic-build endpoint can
    acquire sources for an arbitrary topic and register a corpus on demand; when
    absent, that endpoint reports the capability is not configured. ``scope_resolver``
    is likewise optional and backs the scope-proposal endpoint.
    """

    make_run_id = run_id_factory or (lambda: f"run-{uuid4().hex}")

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield
        manager.shutdown()

    app = FastAPI(
        title="Chronicle Agent API",
        version="e5-agent-runtime-v1",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Accept", "Content-Type", "Last-Event-ID"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/corpora", response_model=list[CorpusSummary])
    def list_corpora() -> list[CorpusSummary]:
        return [CorpusSummary.from_manifest(item) for item in corpus_registry.list_manifests()]

    @app.post(
        "/api/investigations/{investigation_id}/questions",
        response_model=AgentRunAccepted,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def submit_question(
        investigation_id: str,
        submission: QuestionSubmission,
    ) -> AgentRunAccepted:
        try:
            corpus = corpus_registry.get_corpus(investigation_id)
        except UnknownCorpusError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        run_id = make_run_id()
        record = _make_run_record(
            corpus,
            run_id=run_id,
            question=submission.question,
            conversation_summary=submission.conversationSummary,
            workspace_context=submission.workspaceContext,
        )
        try:
            manager.submit(record)
        except AgentRunAlreadyExistsError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return AgentRunAccepted.from_run(run_id, record.status)

    @app.post(
        "/api/investigations/resolve-scope",
        response_model=ScopeResolutionResponse,
    )
    def resolve_scope(request: ScopeResolutionRequest) -> ScopeResolutionResponse:
        """Propose an acquisition scope (geography + date window + terms) from a
        bare question, for the caller to review and edit before building.

        Fallback-safe: when the local model cannot propose a valid scope this
        returns ``resolved=false`` with a note, so the frontend collects the
        scope manually. Nothing is acquired here.
        """
        if scope_resolver is None:
            raise HTTPException(
                status_code=501,
                detail="Scope resolution is not configured on this deployment.",
            )
        result = scope_resolver.resolve(request.question)
        if not result.resolved or result.proposal is None:
            return ScopeResolutionResponse(resolved=False, message=result.message)
        proposal = result.proposal
        return ScopeResolutionResponse(
            resolved=True,
            topic=proposal.topic,
            interpretedQuestion=proposal.interpretedQuestion,
            geographicScope=proposal.geographicScope,
            dateEarliest=proposal.dateEarliest,
            dateLatest=proposal.dateLatest,
            terms=proposal.terms,
        )

    @app.post(
        "/api/investigations/build",
        response_model=CorpusBuildAccepted,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def build_and_investigate(submission: TopicBuildSubmission) -> CorpusBuildAccepted:
        """Acquire free/local sources for an arbitrary topic, build + register a
        corpus, and start an investigation over it.

        The build runs synchronously within this request (FastAPI runs sync
        routes in a threadpool, so the event loop is not blocked). On CPU-only
        hardware acquisition + embedding is minutes-scale, so the caller waits
        for the build before the run is accepted; streaming build stages via a
        dedicated async build job is the next increment.
        """
        if build_service is None:
            raise HTTPException(
                status_code=501,
                detail="Topic acquisition is not configured on this deployment.",
            )
        outcome = build_service.build(
            topic=submission.topic,
            interpreted_question=submission.question,
            geographic_scope=submission.geographicScope,
            date_earliest=submission.dateEarliest,
            date_latest=submission.dateLatest,
            terms=submission.terms,
            max_sources=submission.maxSources,
        )
        try:
            corpus = corpus_registry.get_corpus(outcome.corpusId)
        except UnknownCorpusError as exc:  # pragma: no cover - registration just happened
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        run_id = make_run_id()
        record = _make_run_record(corpus, run_id=run_id, question=submission.question)
        try:
            manager.submit(record)
        except AgentRunAlreadyExistsError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return CorpusBuildAccepted.from_build(
            corpus_id=outcome.corpusId,
            already_built=outcome.alreadyRegistered,
            discovered=outcome.acquisition.discovered,
            acquired=outcome.acquisition.acquired,
            passages=outcome.acquisition.passages,
            run=AgentRunAccepted.from_run(run_id, record.status),
        )

    @app.get("/api/agent-runs/{run_id}", response_model=AgentRunRecord)
    def get_run(run_id: str) -> AgentRunRecord:
        return _load_run_or_404(manager, run_id)

    @app.get(
        "/api/agent-runs/{run_id}/events",
        response_model=list[AgentRunEvent],
        response_model_exclude_none=True,
    )
    def get_events(
        run_id: str,
        request: Request,
        after: int = Query(default=0, ge=0),
        last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    ):
        _load_run_or_404(manager, run_id)
        cursor = _event_cursor(after, last_event_id)
        if "text/event-stream" not in request.headers.get("accept", ""):
            return manager.events(run_id, after_sequence=cursor)
        return StreamingResponse(
            _event_stream(manager, run_id, cursor),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    @app.post(
        "/api/agent-runs/{run_id}/resume",
        response_model=AgentRunAccepted,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def resume_run(run_id: str) -> AgentRunAccepted:
        try:
            record = manager.resume(run_id)
        except AgentRunNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (AgentRunAlreadyActiveError, AgentRunNotResumableError) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return AgentRunAccepted.from_run(run_id, record.status)

    @app.post(
        "/api/agent-runs/{run_id}/cancel",
        response_model=AgentRunAccepted,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def cancel_run(run_id: str) -> AgentRunAccepted:
        try:
            record = manager.cancel(run_id)
        except AgentRunNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except AgentRunNotCancellableError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return AgentRunAccepted.from_run(run_id, record.status)

    return app


def create_default_app() -> FastAPI:
    """Compose the local Ollama runtime used by Uvicorn and Phase E6."""

    corpus_registry = CorpusRegistry()
    run_root = Path(
        os.environ.get(
            "CHRONICLE_AGENT_RUNS_DIR",
            str(Path(__file__).resolve().parents[3] / "runs" / "agents"),
        )
    )
    store = AgentRunStore(run_root)
    # Qwen 7B structured calls on a local CPU/GPU routinely exceed one minute;
    # the UI streams bounded progress while the request remains synchronous.
    provider = OllamaModelProvider(timeout=180.0)
    # Two passage-sized records stay within the downstream 6k evidence window
    # for the current verbose, provenance-rich search projection.
    policy = AgentExecutionPolicy(maxResultsPerTool=2)
    analyst = EvidenceAnalyst(provider, policy)
    retrieval = InvestigationRunner(build_default_registry(), store=store, policy=policy)
    workflow = LangGraphAgentWorkflow(
        planner=InvestigationPlanner(
            provider,
            policy,
            representation=ToolSpecRepresentation.COMPACT,
        ),
        retrieval_runner=retrieval,
        analyst=analyst,
        finalization_runner=FinalizationRunner(
            retrieval_runner=retrieval,
            analyst=analyst,
            critic=HistoricalCritic(provider, policy),
            guide=InvestigationGuide(provider, policy),
            store=store,
        ),
        store=store,
    )
    manager = AgentRunManager(
        workflow=workflow,
        store=store,
        corpus_registry=corpus_registry,
    )
    repo_root = Path(__file__).resolve().parents[3]
    runs_root = Path(
        os.environ.get("CHRONICLE_ACQUISITION_DIR", str(repo_root / "runs" / "acquisition"))
    )
    # Semantic re-ranking is opt-in: it needs a local embedding model
    # (nomic-embed-text) pulled into Ollama. Off by default so the lexical build
    # path always works; set CHRONICLE_ENABLE_SEMANTIC=1 once the model is present.
    embedder = OllamaEmbedder() if _env_flag("CHRONICLE_ENABLE_SEMANTIC") else None
    build_service = CorpusBuildService(
        pipeline=default_pipeline(
            repo_root=repo_root,
            cache_dir=runs_root / "cache",
        ),
        registry=corpus_registry,
        build_dir=runs_root / "built-corpora",
        embedder=embedder,
    )
    return create_app(
        manager=manager,
        corpus_registry=corpus_registry,
        build_service=build_service,
        scope_resolver=ScopeResolver(provider, policy),
    )


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _make_run_record(
    corpus,
    *,
    run_id: str,
    question: str,
    conversation_summary: str | None = None,
    workspace_context=None,
) -> AgentRunRecord:
    """Assemble the run record + corpus snapshot for a question over a corpus.

    Shared by the corpus-question and topic-build endpoints so both capture the
    same immutable corpus provenance in the audit trail."""

    manifest = corpus.get_manifest()
    investigation = corpus.get_investigation()
    return AgentRunRecord(
        runId=run_id,
        request=InvestigationRequest(
            runId=run_id,
            corpusId=corpus.corpus_id,
            userQuestion=question,
            conversationSummary=conversation_summary,
            workspaceContext=workspace_context,
        ),
        corpusSnapshot=CorpusSnapshot(
            corpusId=corpus.corpus_id,
            packageId=investigation.packageId,
            packageHash=manifest.packageHash,
            packageRevision=investigation.packageRevision,
            schemaVersion=investigation.schemaVersion,
            capabilities=tuple(manifest.supportedCapabilities),
            knownOmissions=tuple(manifest.knownOmissions),
        ),
    )


def _load_run_or_404(manager: AgentRunManager, run_id: str) -> AgentRunRecord:
    try:
        return manager.get(run_id)
    except AgentRunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _event_cursor(after: int, last_event_id: str | None) -> int:
    if last_event_id is None:
        return after
    try:
        parsed = int(last_event_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Last-Event-ID must be an integer") from exc
    if parsed < 0:
        raise HTTPException(status_code=400, detail="Last-Event-ID cannot be negative")
    return max(after, parsed)


def _event_stream(manager: AgentRunManager, run_id: str, cursor: int) -> Iterator[str]:
    while True:
        events = manager.events(run_id, after_sequence=cursor)
        for event in events:
            cursor = event.sequence
            yield (
                f"id: {event.sequence}\n"
                f"event: {event.type.value}\n"
                f"data: {event.model_dump_json(exclude_none=True)}\n\n"
            )
        record = manager.get(run_id)
        if record.status in _TERMINAL_STATUSES and not manager.events(
            run_id, after_sequence=cursor
        ):
            return
        if not events:
            waiting = manager.wait_for_events(
                run_id,
                after_sequence=cursor,
                timeout=15.0,
            )
            if not waiting:
                yield ": keep-alive\n\n"


__all__ = ["create_app", "create_default_app"]
