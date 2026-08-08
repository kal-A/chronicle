"""Explicit failure taxonomy for the corpus layer (Phase E2).

Mirrors ai/models/errors.py's discipline exactly: a single base class, a
flat set of concrete subclasses (no nested exception trees), every failure
path in corpus/ raises one of these, never a bare Exception.
"""

from __future__ import annotations


class CorpusError(Exception):
    """Base class for every typed corpus-layer failure."""


class UnknownCorpusError(CorpusError):
    """A corpus_id was requested that no registered manifest describes."""


class DuplicateCorpusIdError(CorpusError):
    """Two manifests were registered under the same corpus_id."""


class InvalidPackageError(CorpusError):
    """A package failed GeneratedInvestigation schema/cross-reference
    validation and was therefore never indexed. Carries the underlying
    GeneratedInvestigationValidationError as __cause__."""


class UnknownRecordError(CorpusError):
    """A record ID was requested that does not exist in this corpus --
    including a record ID that is real, but belongs to a *different*
    corpus (corpus-boundary enforcement; see docs/ai/tool-registry.md)."""


class InvalidSearchRequestError(CorpusError):
    """A PassageSearchRequest failed constraint checks not already
    enforced by Pydantic validation on the request model itself (e.g. an
    id referenced in a filter that doesn't exist in this corpus)."""


class CorpusBoundaryError(CorpusError):
    """An operation attempted to cross corpus boundaries -- e.g. a filter
    referencing a record ID from a different corpus than the one being
    queried."""
