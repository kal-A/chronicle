"""HTML-to-text extraction and fetch_url_text content-type handling."""

from __future__ import annotations

import httpx

from chronicle.acquisition.extract import fetch_url_text, html_to_text


def test_html_to_text_strips_tags_and_scripts():
    html = """
    <html><head><title>t</title><style>.x{}</style></head>
    <body>
      <script>var a = 1;</script>
      <h1>Heading</h1>
      <p>First paragraph with <b>bold</b> text.</p>
      <p>Second paragraph.</p>
    </body></html>
    """
    text = html_to_text(html)
    assert "Heading" in text
    assert "First paragraph with bold text." in text
    assert "Second paragraph." in text
    assert "var a" not in text  # script dropped
    assert ".x{}" not in text  # style dropped


def test_fetch_url_text_extracts_html():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<p>Hello world.</p>", headers={"content-type": "text/html; charset=utf-8"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    text, content_type = fetch_url_text(client, "https://example.org/a")
    assert "Hello world." in text
    assert content_type == "text/html"


def test_fetch_url_text_returns_plain_text_as_is():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="raw text body", headers={"content-type": "text/plain"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    text, content_type = fetch_url_text(client, "https://example.org/a")
    assert text == "raw text body"
    assert content_type == "text/plain"


def test_fetch_url_text_returns_empty_for_unsupported_types():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"%PDF-1.4 ...", headers={"content-type": "application/pdf"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    text, content_type = fetch_url_text(client, "https://example.org/a.pdf")
    assert text == ""
    assert content_type == "application/pdf"
