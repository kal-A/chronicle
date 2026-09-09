"""Free/local source connectors.

Each connector wraps one free, keyless data source (Wikipedia, Wikidata,
Wikisource, Internet Archive, Project Gutenberg, and the in-repo doc-registry
seed) behind the same ``SourceConnector`` interface: ``discover`` returns
candidates, ``fetch`` returns full text. No connector requires an API key, and
none names or branches on a historical subject.
"""

from __future__ import annotations

from .base import ConnectorError, DEFAULT_USER_AGENT, SourceConnector

__all__ = ["ConnectorError", "DEFAULT_USER_AGENT", "SourceConnector"]
