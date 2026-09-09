"""Corpus acquisition pipeline: turn an arbitrary topic into a source-backed corpus.

This package is the missing bridge between "a user's topic" and the existing
four-agent investigation core. Given a topic and a resolved scope, it discovers
candidate sources from free/local connectors, acquires their full text, extracts
passages, embeds them locally, and assembles a package the existing corpus layer
can serve — so the four agents investigate a freshly built corpus exactly as they
investigate a pre-built fixture today.

Generalization contract (enforced by
``tests/ai/tools/test_no_topic_branching_guard.py``): nothing in this package may
recognize a specific historical subject. Every stage is parameterized by ``topic``
and ``scope``; there are no benchmark names, package ids, or per-topic branches in
this code. The sole place topic strings are allowed to appear as data is
``corpus/manifest.py`` (registration data), never here.
"""

from __future__ import annotations
