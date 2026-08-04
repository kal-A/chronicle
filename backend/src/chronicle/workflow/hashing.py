"""Deterministic content hashing for stage inputs/outputs.

Same input dict -> same hash, regardless of key insertion order (sort_keys)
or process (no reliance on Python's randomized hash seed). This is what
makes reuse-on-resume and cross-run determinism checks possible.
"""

import hashlib
import json
from typing import Any


def stable_json_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
