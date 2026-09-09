"""DocRegistrySeedConnector: parse in-repo source registers as seeds.

Discovery runs against a synthetic register written into a temp repo tree, so it is
offline and stable. Fetch is served by httpx.MockTransport.
"""

from __future__ import annotations

import httpx

from chronicle.acquisition.connectors.doc_registry_seed import DocRegistrySeedConnector
from chronicle.acquisition.contracts import DiscoveryQuery
from chronicle.contracts.enums import RightsStatus, SourceType

_REGISTER = """# Test Register

## Primary and Documentary Sources

| ID | Source | Type | Rights / access | Covers | Status |
|---|---|---|---|---|---|
| `t-src-001` | Ambassador dispatch on the alpha crisis ([Archive](https://example.org/alpha)) | Primary — official/diplomatic | Public domain digitization | alpha crisis diplomacy | Acquired |
| `t-src-002` | Study of beta maritime law ([Book](https://example.org/beta)) | Secondary — specialist | Licensed; needs acquisition | beta maritime signalling | Identified |
"""


def _seed_repo(tmp_path):
    research = tmp_path / "docs" / "research"
    research.mkdir(parents=True)
    (research / "test-source-register.md").write_text(_REGISTER, encoding="utf-8")
    return tmp_path


def test_discover_returns_relevant_register_entries_only(tmp_path):
    repo = _seed_repo(tmp_path)
    connector = DocRegistrySeedConnector(repo)
    candidates = connector.discover(DiscoveryQuery(topic="alpha crisis"))

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.candidateId == "doc-registry:t-src-001"
    assert candidate.title == "Ambassador dispatch on the alpha crisis"
    assert candidate.url == "https://example.org/alpha"
    assert candidate.sourceType is SourceType.PRIMARY_OFFICIAL_DIPLOMATIC
    assert candidate.rightsStatus is RightsStatus.PUBLIC_DOMAIN
    assert candidate.fullTextAvailable is True
    assert candidate.identifiers["registerId"] == "t-src-001"


def test_discover_gates_out_unrelated_entries(tmp_path):
    repo = _seed_repo(tmp_path)
    connector = DocRegistrySeedConnector(repo)
    # a topic overlapping only the second row's vocabulary
    candidates = connector.discover(DiscoveryQuery(topic="maritime signalling"))
    assert [c.candidateId for c in candidates] == ["doc-registry:t-src-002"]


def test_fetch_downloads_and_extracts_the_linked_document(tmp_path):
    repo = _seed_repo(tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://example.org/alpha"
        return httpx.Response(
            200,
            text="<html><body><p>The dispatch text body.</p></body></html>",
            headers={"content-type": "text/html"},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    connector = DocRegistrySeedConnector(repo, client=client)
    candidate = connector.discover(DiscoveryQuery(topic="alpha crisis"))[0]
    acquired = connector.fetch(candidate)

    assert acquired is not None
    assert "The dispatch text body." in acquired.text
    assert acquired.candidate.candidateId == "doc-registry:t-src-001"
