"""docs/model.md is generated from the constraint registry and must not drift."""

from __future__ import annotations

from pathlib import Path
from typing import get_args

from reshelf.constraints import CONSTRAINTS
from reshelf.elimination import Reason
from reshelf.model_doc import DEFAULT_PATH, REASON_TEXT, main, render


def test_every_constraint_and_reason_is_documented() -> None:
    text = render()
    for spec in CONSTRAINTS:
        assert f"| `{spec.name}` |" in text
    assert set(REASON_TEXT) == set(get_args(Reason))


def test_every_constraint_names_where_its_bound_comes_from() -> None:
    links = {"link_xy", "link_yx", "link_yz", "link_zy"}
    assert {s.name for s in CONSTRAINTS if not s.reads} == links


def test_render_is_deterministic() -> None:
    assert render() == render()


def test_committed_file_matches_the_registry() -> None:
    assert DEFAULT_PATH.read_text(encoding="utf-8") == render()


def test_check_detects_drift_and_write_fixes_it(tmp_path: Path) -> None:
    out = tmp_path / "model.md"
    assert main(["--check", "--out", str(out)]) == 1  # missing file counts as drift
    assert main(["--out", str(out)]) == 0
    assert main(["--check", "--out", str(out)]) == 0
    out.write_text("edited", encoding="utf-8")
    assert main(["--check", "--out", str(out)]) == 1
