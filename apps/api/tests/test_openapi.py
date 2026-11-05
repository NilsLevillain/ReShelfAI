"""The checked in `openapi.json` matches the live schema (drift check)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from dump_openapi import OUT, render


def test_openapi_json_is_current() -> None:
    assert OUT.read_text(encoding="utf-8") == render(), (
        "openapi.json is out of date. Run: uv run python scripts/dump_openapi.py"
    )
