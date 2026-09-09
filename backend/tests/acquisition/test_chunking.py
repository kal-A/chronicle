"""Chunking tests: deterministic, boundary-respecting, offset-accurate."""

from __future__ import annotations

from chronicle.acquisition.chunking import chunk_source, chunk_text
from chronicle.acquisition.contracts import AcquiredSource, SourceCandidate
from chronicle.contracts.enums import SourceType


def _candidate() -> SourceCandidate:
    return SourceCandidate(
        candidateId="wikipedia:en:42",
        connector="wikipedia",
        title="Alpha",
        sourceType=SourceType.TERTIARY_REFERENCE,
        fullTextAvailable=True,
    )


def test_short_text_is_a_single_passage():
    passages = chunk_text("A short note.", source_candidate_id="c1")
    assert len(passages) == 1
    p = passages[0]
    assert p.text == "A short note."
    assert p.charStart == 0
    assert p.ordinal == 0
    assert p.passageId == "c1#p0000"
    assert p.locator.startswith("chars 0-")


def test_empty_or_whitespace_text_yields_no_passages():
    assert chunk_text("", source_candidate_id="c1") == []
    assert chunk_text("   \n\n  ", source_candidate_id="c1") == []


def test_long_text_splits_into_multiple_ordered_passages():
    # ~30 paragraphs well over the target size
    text = "\n\n".join(f"Paragraph {i} " + ("word " * 40) for i in range(30))
    passages = chunk_text(text, source_candidate_id="c1", target_chars=1200)

    assert len(passages) > 1
    # ordinals are contiguous from zero
    assert [p.ordinal for p in passages] == list(range(len(passages)))
    # each chunk respects the target with a little boundary slack
    assert all(len(p.text) <= 1200 for p in passages)


def test_passages_partition_the_source_without_gaps_or_overlap():
    text = "\n\n".join(f"Section {i} " + ("token " * 50) for i in range(20))
    passages = chunk_text(text, source_candidate_id="c1", target_chars=1000)

    # offsets are a clean contiguous partition
    assert passages[0].charStart == 0
    for earlier, later in zip(passages, passages[1:]):
        assert later.charStart == earlier.charEnd
    assert passages[-1].charEnd == len(text)


def test_chunking_is_deterministic():
    text = "\n\n".join(f"Para {i} " + ("alpha " * 45) for i in range(25))
    first = chunk_text(text, source_candidate_id="c1", target_chars=900)
    second = chunk_text(text, source_candidate_id="c1", target_chars=900)
    assert [p.model_dump() for p in first] == [p.model_dump() for p in second]


def test_prefers_paragraph_boundaries():
    # two fat paragraphs; the first break should land at the paragraph gap
    para = "word " * 300  # ~1500 chars
    text = para.strip() + "\n\n" + para.strip()
    passages = chunk_text(text, source_candidate_id="c1", target_chars=1600)
    # first passage should end at or near the paragraph break, not mid-second-paragraph
    assert passages[0].charEnd <= len(para) + 2


def test_chunk_source_uses_candidate_id():
    source = AcquiredSource(
        candidate=_candidate(),
        text="Some acquired body text.",
        contentType="text/plain",
        contentSha256="deadbeef",
        charCount=24,
    )
    passages = chunk_source(source)
    assert passages[0].sourceCandidateId == "wikipedia:en:42"
    assert passages[0].passageId.startswith("wikipedia:en:42#p")
