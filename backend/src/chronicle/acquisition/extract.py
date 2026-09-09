"""Text extraction helpers shared by connectors that fetch arbitrary web docs.

Stdlib-only HTML-to-text (no new dependency): strips script/style, turns block
elements into line breaks, and collapses whitespace to readable paragraphs. This
is intentionally simple and can be upgraded to a readability library later without
changing callers. PDF extraction is not handled here yet (a later step) — a PDF
fetch returns empty text, which callers treat as "full text unavailable".
"""

from __future__ import annotations

import re
from html.parser import HTMLParser

import httpx

_SKIP_TAGS = {"script", "style", "noscript", "head", "template"}
_BLOCK_TAGS = {
    "p", "br", "div", "li", "tr", "section", "article", "header", "footer",
    "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre", "ul", "ol", "table",
}
_BLANKS_RE = re.compile(r"\n{3,}")
_SPACES_RE = re.compile(r"[ \t]{2,}")


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        elif tag in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        elif tag in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0 and data.strip():
            self._parts.append(data)

    def text(self) -> str:
        raw = "".join(self._parts)
        lines = [_SPACES_RE.sub(" ", line).strip() for line in raw.splitlines()]
        joined = "\n".join(line for line in lines if line != "" or True)
        return _BLANKS_RE.sub("\n\n", joined).strip()


def html_to_text(html_str: str) -> str:
    parser = _TextExtractor()
    parser.feed(html_str)
    return parser.text()


def fetch_url_text(client: httpx.Client, url: str) -> tuple[str, str]:
    """Fetch a URL and return (extracted_text, content_type).

    HTML is reduced to text; ``text/*`` is returned as-is; other types (e.g. PDF)
    return empty text for now. Raises httpx.HTTPError on transport failure — the
    caller decides whether that is fatal.
    """
    response = client.get(url)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
    if "html" in content_type or content_type == "":
        return html_to_text(response.text), content_type or "text/html"
    if content_type.startswith("text/"):
        return response.text.strip(), content_type
    return "", content_type  # unsupported (e.g. application/pdf) for now
