"""Deterministic passage chunking: AcquiredSource full text -> ExtractedPassage list.

Non-overlapping, boundary-respecting chunks with exact character-offset locators.
Boundaries are preferred at paragraph breaks, then sentence ends, then whitespace,
so passages don't split mid-word; when no boundary is available a hard cut is used.
No overlap (keeps passages distinct and offsets a clean partition); overlap can be
added later if retrieval quality requires it.

Deterministic: identical text always yields identical passages, so a re-run over a
cached source reproduces the same corpus.
"""

from __future__ import annotations

from .contracts import AcquiredSource, ExtractedPassage

DEFAULT_TARGET_CHARS = 1200
DEFAULT_MIN_CHUNK_CHARS = 400  # earliest point a "clean" boundary is accepted


def _boundary(text: str, start: int, end: int, min_end: int) -> int:
    """Pick a clean break at/just before ``end`` within ``text``, no earlier than
    ``min_end``. Returns an absolute offset in ``text``."""
    window = text[start:end]
    for marker in ("\n\n", ". ", ".\n", "\n", " "):
        idx = window.rfind(marker)
        if idx != -1 and start + idx + len(marker) >= min_end:
            return start + idx + len(marker)
    return end  # no acceptable boundary: hard cut


def chunk_text(
    text: str,
    *,
    source_candidate_id: str,
    target_chars: int = DEFAULT_TARGET_CHARS,
) -> list[ExtractedPassage]:
    if target_chars <= 0:
        raise ValueError("target_chars must be positive")

    passages: list[ExtractedPassage] = []
    length = len(text)
    start = 0
    ordinal = 0
    while start < length:
        hard_end = min(start + target_chars, length)
        if hard_end < length:
            min_end = min(start + DEFAULT_MIN_CHUNK_CHARS, length)
            end = _boundary(text, start, hard_end, min_end)
        else:
            end = hard_end
        if end <= start:  # defensive: always make progress
            end = hard_end

        chunk = text[start:end].strip()
        if chunk:
            passages.append(
                ExtractedPassage(
                    passageId=f"{source_candidate_id}#p{ordinal:04d}",
                    sourceCandidateId=source_candidate_id,
                    ordinal=ordinal,
                    text=chunk,
                    charStart=start,
                    charEnd=end,
                    locator=f"chars {start}-{end}",
                )
            )
            ordinal += 1
        start = end
    return passages


def chunk_source(
    source: AcquiredSource,
    *,
    target_chars: int = DEFAULT_TARGET_CHARS,
) -> list[ExtractedPassage]:
    """Chunk an acquired source's text, tagging passages with its candidate id."""
    return chunk_text(
        source.text,
        source_candidate_id=source.candidate.candidateId,
        target_chars=target_chars,
    )
