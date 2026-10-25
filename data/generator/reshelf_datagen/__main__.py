"""Command line entry: python -m reshelf_datagen --scenario <yaml> --out <dir>."""

from __future__ import annotations

import argparse
from pathlib import Path

from reshelf_datagen import generate, load_scenario, write_tables


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the synthetic source tables.")
    parser.add_argument("--scenario", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    cfg = load_scenario(args.scenario)
    manifest = write_tables(generate(cfg), cfg, args.out)
    rows = sum(manifest["rows"].values())
    print(f"{cfg['name']}: {len(manifest['rows'])} tables, {rows} rows -> {args.out}")


if __name__ == "__main__":
    main()
