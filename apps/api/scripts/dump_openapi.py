"""Write the OpenAPI schema to `openapi.json`. Run from `apps/api`: `uv run python scripts/dump_openapi.py`.

A test compares the file with the live schema, so a changed endpoint or model fails CI until this
is rerun and committed. Week 4 generates the TypeScript types from this file.
"""

import json
import sys
from pathlib import Path

from reshelf.api import create_app

OUT = Path(__file__).resolve().parent.parent / "openapi.json"


def render() -> str:
    return json.dumps(create_app().openapi(), indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    OUT.write_text(render(), encoding="utf-8", newline="\n")
    print(f"wrote {OUT}")
    sys.exit(0)
