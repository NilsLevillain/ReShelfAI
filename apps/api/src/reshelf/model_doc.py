"""Generate `docs/model.md` from the named constraint registry.

Run from `apps/api`:
    uv run python -m reshelf.model_doc            write ../../docs/model.md
    uv run python -m reshelf.model_doc --check    exit 1 when the committed file differs (CI)

Constraint names, formulas and the parameters they read come from `constraints.CONSTRAINTS`, so the
solver, the checker, the rule trace, the tests and this file cannot drift apart.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from reshelf.constraints import CONSTRAINTS, ConstraintSpec
from reshelf.elimination import Reason

DEFAULT_PATH = Path(__file__).resolve().parents[4] / "docs" / "model.md"

REASON_TEXT: dict[Reason, str] = {
    "RSL": "Remaining shelf life at delivery is below the channel minimum, or the lot expires first",
    "TIER": "The brand tier of the material is not allowed in the channel",
    "NO_PUSH": "The material is new in the channel and its category has no push quantity",
}


def _cell(text: str) -> str:
    return text.replace("|", "\\|")


def _row(spec: ConstraintSpec) -> str:
    cells = [
        f"`{spec.name}`",
        f"`{spec.index}`",
        f"`{spec.formula}`",
        f"`{spec.sense}`",
        spec.description,
        f"`{spec.reads}`" if spec.reads else "none",
        f"`{spec.planner_rule}`" if spec.planner_rule else "none",
    ]
    return "| " + " | ".join(_cell(c) for c in cells) + " |"


def render() -> str:
    lines = [
        "# Model",
        "",
        "Generated from the constraint registry (`apps/api/src/reshelf/constraints.py`).",
        "Do not edit by hand. Run `make model-doc`. CI fails when this file drifts.",
        "",
        "All rule values are invented illustrative defaults. They live in `ZPARAM` and in",
        "the scenario yaml, never in code.",
        "",
        "## Variables",
        "",
        "| Symbol | Meaning |",
        "|---|---|",
        "| `x[l,c]` | Units of lot l sent to channel c (integer, at least 0) |",
        "| `y[l,c]` | Lot l is used in channel c (binary) |",
        "| `z[m,c]` | Material m is selected in channel c (binary) |",
        "",
        "Variables exist only for admissible pairs, those that survive elimination.",
        "",
        "## Elimination reason codes",
        "",
        "Dropped before modeling. Each dropped pair keeps its code for the Why panel.",
        "",
        "| Code | Meaning |",
        "|---|---|",
        *(f"| `{code}` | {text} |" for code, text in REASON_TEXT.items()),
        "",
        "## Named constraints",
        "",
        "| Name | Index | Formula | Sense | Meaning | Reads | Planner rule |",
        "|---|---|---|---|---|---|---|",
        *(_row(spec) for spec in CONSTRAINTS),
        "",
        "Coverage and push rows use the tight form: the binary multiplies the smallest valid",
        "bound (ADR 004). The rule trace reads the slack of each instance, so names stay stable.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate docs/model.md")
    parser.add_argument("--check", action="store_true", help="fail when the file differs")
    parser.add_argument("--out", type=Path, default=DEFAULT_PATH)
    args = parser.parse_args(argv)

    text = render()
    if args.check:
        current = args.out.read_text(encoding="utf-8") if args.out.exists() else ""
        if current != text:
            print(f"{args.out} differs from the registry. Run `make model-doc`.", file=sys.stderr)
            return 1
        return 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
