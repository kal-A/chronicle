"""SourceConnector base: the shared interface and HTTP plumbing every connector uses.

Mirrors the injected-``httpx.Client`` pattern from ``ai/models/ollama.py`` so that
unit tests drive connectors with ``httpx.MockTransport`` and make zero real network
requests. A connector sets a class-level ``name`` and ``base_url`` and implements
``discover`` and ``fetch``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from ..contracts import AcquiredSource, DiscoveryQuery, SourceCandidate

DEFAULT_TIMEOUT_SECONDS = 30.0
# A descriptive User-Agent is required by Wikimedia's API etiquette and is polite
# to every other free host. No contact secret here — just an honest identifier.
DEFAULT_USER_AGENT = "ChronicleResearchBot/0.1 (local historical-investigation; +https://github.com/chronicle)"


class ConnectorError(RuntimeError):
    """A connector could not complete a discover/fetch against its source.

    Raised for transport/HTTP/parse failures the caller should treat as "this
    source is unavailable right now", never as evidence of absence of sources.
    """


class SourceConnector(ABC):
    """One free source, behind a uniform discover/fetch interface."""

    #: Stable connector identifier, e.g. ``"wikipedia"``. Set by each subclass.
    name: str = ""
    #: Default origin for the injected client. May be overridden per instance.
    base_url: str = ""

    def __init__(
        self,
        client: httpx.Client | None = None,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        if not self.name:
            raise ValueError(f"{type(self).__name__} must define a non-empty class-level name")
        self._timeout = timeout
        self._client = client or httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={"User-Agent": DEFAULT_USER_AGENT},
            follow_redirects=True,
        )

    @abstractmethod
    def discover(self, query: DiscoveryQuery) -> list[SourceCandidate]:
        """Return candidate sources for the query. Never raises on "no results";
        returns an empty list. Raises ConnectorError only on transport failure."""
        raise NotImplementedError

    @abstractmethod
    def fetch(self, candidate: SourceCandidate) -> AcquiredSource | None:
        """Retrieve and extract full text for a candidate this connector produced.

        Returns ``None`` when the full text turns out to be unavailable or empty
        (the candidate stays metadata-only and is dropped as non-evidence),
        rather than fabricating content. Raises ConnectorError on transport
        failure."""
        raise NotImplementedError
