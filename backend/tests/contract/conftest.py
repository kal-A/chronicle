import json
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "fixtures"
INVALID_FIXTURES_DIR = FIXTURES_DIR / "contracts" / "invalid"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def golden_investigation() -> Any:
    return load_json(FIXTURES_DIR / "blank-cheque.golden-investigation.json")
