"""Resumable, concurrency-1 execution of case x strategy x repeat (E7.4).

Each identity's normalized :class:`StrategyResult` is persisted atomically under
``output_dir/results/`` before the next identity begins, so an interrupted run
resumes by recomputing only the identities missing from disk (or whose stored
identity no longer matches the current benchmark version + case-file hash).

The runner is strategy-agnostic and provider-agnostic: strategies are supplied as
a mapping, and a fresh model provider is built per identity by a factory (a
deterministic run needs a fresh scripted queue each time; a live run wants a
clean call budget). Nothing here reads a case's gold rubric fields.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Callable, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field

from ...corpus.manifest import CorpusRegistry
from ..contracts.analysis import AnswerStatus
from ..models.protocol import ModelProvider
from .benchmark import BenchmarkRegistry
from .contracts import EvaluationCase, EvaluationProfile, StrategyId
from .strategies import EvaluationInput, EvaluationStrategy, StrategyResult

#: Builds the provider for one identity (case, strategy, repeat).
ProviderFactory = Callable[[EvaluationCase, StrategyId, int], ModelProvider]

_RESULTS_DIRNAME = "results"
_MANIFEST_FILENAME = "manifest.json"


class ResultIdentity(BaseModel):
    """The unique key of one unit of work."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    caseId: str = Field(min_length=1)
    strategyId: StrategyId
    repeat: int = Field(ge=0)

    def filename(self) -> str:
        return f"{self.caseId}__{self.strategyId.value}__r{self.repeat}.json"


class ResultRef(BaseModel):
    """A completed identity and where its result was written (path relative to
    the run's output directory, so the manifest is location-independent)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    caseId: str
    strategyId: StrategyId
    repeat: int = Field(ge=0)
    path: str


class RunManifest(BaseModel):
    """The byte-stable summary of a run: identity + progress, no wall-clock and
    no latency, so identical inputs produce identical manifest bytes."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    runId: str
    benchmarkVersion: str
    caseFileSha256: str
    profile: EvaluationProfile
    providerName: str
    providerVersion: str
    completed: tuple[ResultRef, ...] = ()
    remaining: tuple[ResultIdentity, ...] = ()


class _PersistedResult(BaseModel):
    """On-disk envelope: the result plus the version metadata a resume matches."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    benchmarkVersion: str
    caseFileSha256: str
    identity: ResultIdentity
    result: StrategyResult


def _plan_identities(
    cases: Sequence[EvaluationCase],
    strategy_ids: Sequence[StrategyId],
    repeats: int,
) -> list[ResultIdentity]:
    """A deterministic, strategy-rotated order: rotating the strategy sequence by
    case index interleaves strategies instead of front-loading one of them."""

    order: list[ResultIdentity] = []
    width = len(strategy_ids)
    for repeat in range(repeats):
        for index, case in enumerate(cases):
            offset = index % width if width else 0
            rotated = list(strategy_ids[offset:]) + list(strategy_ids[:offset])
            for strategy_id in rotated:
                order.append(
                    ResultIdentity(caseId=case.caseId, strategyId=strategy_id, repeat=repeat)
                )
    return order


def _run_id(
    registry: BenchmarkRegistry,
    profile: EvaluationProfile,
    identities: Sequence[ResultIdentity],
) -> str:
    payload = {
        "benchmarkVersion": registry.benchmarkVersion,
        "caseFileSha256": registry.caseFileSha256,
        "profile": profile.value,
        "identities": [identity.model_dump(mode="json") for identity in identities],
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"eval-{profile.value}-{digest[:16]}"


def _result_path(results_dir: Path, identity: ResultIdentity) -> Path:
    """Resolve the result path and refuse anything escaping ``results_dir``.
    caseId is a validated slug and strategyId is an enum, so this is belt-and-
    suspenders — but the guard is cheap and the failure mode (writing outside the
    run directory) is severe."""

    candidate = (results_dir / identity.filename()).resolve()
    try:
        candidate.relative_to(results_dir.resolve())
    except ValueError as exc:  # pragma: no cover - unreachable with validated ids
        raise ValueError(f"result path escapes the output directory: {identity.filename()}") from exc
    return candidate


def _load_persisted(path: Path) -> _PersistedResult | None:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        return _PersistedResult.model_validate_json(raw)
    except ValueError:
        return None


def _write_atomic(path: Path, persisted: _PersistedResult) -> None:
    text = persisted.model_dump_json(indent=2)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _is_fresh(persisted: _PersistedResult | None, registry: BenchmarkRegistry, identity: ResultIdentity) -> bool:
    return (
        persisted is not None
        and persisted.identity == identity
        and persisted.benchmarkVersion == registry.benchmarkVersion
        and persisted.caseFileSha256 == registry.caseFileSha256
    )


def _captured_error_result(
    case: EvaluationCase,
    strategy_id: StrategyId,
    provider: ModelProvider,
    error: Exception,
) -> StrategyResult:
    """When a strategy raises (e.g. an unscripted deterministic provider), record
    a principled abstention rather than aborting the whole run."""

    identity = provider.provider_identity()
    metadata = provider.provider_metadata
    return StrategyResult(
        caseId=case.caseId,
        strategyId=strategy_id,
        corpusId=case.corpusId,
        answerStatus=AnswerStatus.ABSTAINED,
        answerText=f"runner-captured error: {error}"[:4000],
        statements=(),
        references=None,
        modelCallCount=0,
        latencyMs=0.0,
        benchmarkVersion=case.benchmarkVersion,
        providerName=metadata.providerName,
        providerVersion=metadata.providerVersion,
        modelName=identity.modelName,
        promptVersions=(),
    )


def run_benchmark(
    registry: BenchmarkRegistry,
    cases: Sequence[EvaluationCase],
    strategies: Mapping[StrategyId, EvaluationStrategy],
    provider_factory: ProviderFactory,
    corpus_registry: CorpusRegistry,
    *,
    profile: EvaluationProfile,
    output_dir: Path | str,
    cases_filter: Sequence[str] | None = None,
    strategies_filter: Sequence[StrategyId] | None = None,
    max_cases: int | None = None,
    repeats: int = 1,
) -> RunManifest:
    """Execute every selected case x strategy x repeat once, resuming any already
    persisted, and return the byte-stable :class:`RunManifest`."""

    output_dir = Path(output_dir)
    results_dir = output_dir / _RESULTS_DIRNAME
    results_dir.mkdir(parents=True, exist_ok=True)

    selected_cases = [case for case in cases if profile in case.profiles]
    if cases_filter is not None:
        wanted = set(cases_filter)
        selected_cases = [c for c in selected_cases if c.caseId in wanted or wanted & set(c.legacyAliases)]
    if max_cases is not None:
        selected_cases = selected_cases[:max_cases]

    strategy_ids = [sid for sid in strategies if strategies_filter is None or sid in strategies_filter]
    identities = _plan_identities(selected_cases, strategy_ids, repeats)
    cases_by_id = {case.caseId: case for case in selected_cases}
    corpus_cache: dict[str, object] = {}

    provider_name = ""
    provider_version = ""
    completed: list[ResultRef] = []
    remaining: list[ResultIdentity] = []

    for identity in identities:
        path = _result_path(results_dir, identity)
        persisted = _load_persisted(path)
        if _is_fresh(persisted, registry, identity):
            completed.append(ResultRef(**_ref_kwargs(identity, results_dir, output_dir)))
            if not provider_name:
                provider_name = persisted.result.providerName
                provider_version = persisted.result.providerVersion
            continue

        case = cases_by_id[identity.caseId]
        strategy = strategies[identity.strategyId]
        if case.corpusId not in corpus_cache:
            corpus_cache[case.corpusId] = corpus_registry.get_corpus(case.corpusId)
        corpus = corpus_cache[case.corpusId]
        provider = provider_factory(case, identity.strategyId, identity.repeat)
        if not provider_name:
            metadata = provider.provider_metadata
            provider_name, provider_version = metadata.providerName, metadata.providerVersion

        try:
            result = strategy.run(
                EvaluationInput(case=case, corpus=corpus, provider=provider, repeat=identity.repeat)
            )
        except Exception as error:  # noqa: BLE001 - one bad identity must not abort the run
            result = _captured_error_result(case, identity.strategyId, provider, error)

        _write_atomic(
            path,
            _PersistedResult(
                benchmarkVersion=registry.benchmarkVersion,
                caseFileSha256=registry.caseFileSha256,
                identity=identity,
                result=result,
            ),
        )
        completed.append(ResultRef(**_ref_kwargs(identity, results_dir, output_dir)))

    manifest = RunManifest(
        runId=_run_id(registry, profile, identities),
        benchmarkVersion=registry.benchmarkVersion,
        caseFileSha256=registry.caseFileSha256,
        profile=profile,
        providerName=provider_name,
        providerVersion=provider_version,
        completed=tuple(completed),
        remaining=tuple(remaining),
    )
    (output_dir / _MANIFEST_FILENAME).write_text(
        manifest.model_dump_json(indent=2), encoding="utf-8"
    )
    return manifest


def _ref_kwargs(identity: ResultIdentity, results_dir: Path, output_dir: Path) -> dict:
    rel = (results_dir / identity.filename()).relative_to(output_dir).as_posix()
    return {
        "caseId": identity.caseId,
        "strategyId": identity.strategyId,
        "repeat": identity.repeat,
        "path": rel,
    }


def load_results(output_dir: Path | str) -> list[tuple[ResultIdentity, StrategyResult]]:
    """Every persisted (identity, result) pair in a run, ordered by filename."""

    results_dir = Path(output_dir) / _RESULTS_DIRNAME
    pairs: list[tuple[ResultIdentity, StrategyResult]] = []
    if not results_dir.is_dir():
        return pairs
    for path in sorted(results_dir.glob("*.json")):
        persisted = _load_persisted(path)
        if persisted is not None:
            pairs.append((persisted.identity, persisted.result))
    return pairs


def load_manifest(output_dir: Path | str) -> RunManifest | None:
    """Read a run's manifest, or ``None`` when the directory has no run."""

    manifest_path = Path(output_dir) / _MANIFEST_FILENAME
    try:
        raw = manifest_path.read_text(encoding="utf-8")
    except OSError:
        return None
    return RunManifest.model_validate_json(raw)


__all__ = [
    "ProviderFactory",
    "ResultIdentity",
    "ResultRef",
    "RunManifest",
    "run_benchmark",
    "load_manifest",
    "load_results",
]
