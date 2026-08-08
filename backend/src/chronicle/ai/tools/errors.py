"""Explicit failure taxonomy for the typed tool layer (Phase E2). Same
flat-hierarchy discipline as ai/models/errors.py -- one base class, a flat
set of concrete subclasses, every failure path raises one of these, never
a bare Exception, and InternalRetrievalError never leaks a raw traceback
to a caller (the spec's explicit "do not expose raw stack traces to
future agents or users").
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .contracts import ToolCallRecord


class ToolError(Exception):
    """Base class for every typed tool-layer failure."""

    def __init__(self, message: str, *, call_record: "ToolCallRecord | None" = None) -> None:
        super().__init__(message)
        self.callRecord = call_record

    def with_call_record(self, record: "ToolCallRecord") -> "ToolError":
        self.callRecord = record
        return self


class UnknownToolError(ToolError):
    """A tool name was requested that no registration exists for."""


class DuplicateToolNameError(ToolError):
    """Two tools were registered under the same name."""


class MalformedToolInputError(ToolError):
    """The raw input dict failed validation against the tool's input
    model. The validation detail is summarized without exposing an
    exception chain or traceback."""


class MalformedToolOutputError(ToolError):
    """A tool's execute() function returned a value that failed
    validation against its own declared output model -- a bug in the
    tool implementation, not caller error."""


class UnauthorizedToolError(ToolError):
    """The calling context's allowed_tool_names does not include this
    tool."""


class UnsupportedCapabilityError(ToolError):
    """The target corpus's manifest does not declare a capability this
    tool requires. This is an honest rejection path, not a tool bug."""


class CorpusMismatchError(ToolError):
    """The tool input's own corpus_id does not match the calling
    ToolExecutionContext's corpus_id -- a belt-and-suspenders check
    against cross-corpus leakage."""


class CorpusRetrievalError(ToolError):
    """A typed corpus-layer failure observed while invoking a tool."""

    def __init__(
        self,
        message: str,
        *,
        corpus_error_type: str,
        call_record: "ToolCallRecord | None" = None,
    ) -> None:
        super().__init__(message, call_record=call_record)
        self.corpusErrorType = corpus_error_type


class ResultLimitExceededError(ToolError):
    """A requested result count exceeds the tool's declared maximum."""


class PathDepthExceededError(ToolError):
    """A relationship-traversal request exceeded its bounded maximum
    depth or maximum path count."""


class InternalRetrievalError(ToolError):
    """A tool's execution raised an unexpected exception. The registry
    wraps it here rather than letting a raw traceback (or an
    implementation-internal exception type) reach the caller."""
