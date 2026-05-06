from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

import pandas as pd


def find_files(inputs: Iterable[str], pattern: str = "*.csv", recursive: bool = False) -> List[Path]:
    paths: List[Path] = []
    for p in inputs:
        ppath = Path(p)
        if ppath.is_dir():
            paths.extend(sorted(ppath.rglob(pattern) if recursive else ppath.glob(pattern)))
        else:
            # allow glob patterns or file paths
            matched = list(Path('.').glob(p))
            if matched:
                paths.extend(sorted(matched))
            elif ppath.exists():
                paths.append(ppath)
    # remove duplicates while preserving order
    seen = set()
    uniq: List[Path] = []
    for p in paths:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            uniq.append(p)
    return uniq


def concat_csvs(files: Iterable[Path], check_columns: bool = True) -> pd.DataFrame:
    files = list(files)
    if not files:
        raise ValueError("No input files provided")

    dfs: List[pd.DataFrame] = []
    for f in files:
        dfs.append(pd.read_csv(f))

    if check_columns:
        first_cols = list(dfs[0].columns)
        for i, df in enumerate(dfs[1:], start=1):
            if list(df.columns) != first_cols:
                raise ValueError(f"Column mismatch in file {files[i]}\nExpected: {first_cols}\nFound: {list(df.columns)}")

    return pd.concat(dfs, ignore_index=True)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Concatenate multiple CSV files (same columns) into one CSV file."
    )
    p.add_argument(
        "inputs",
        nargs="+",
        help=(
            "Input files, directories, or glob patterns. Directories are searched for '*.csv' by default."
        ),
    )
    p.add_argument(
        "--pattern",
        default="*.csv",
        help="Glob pattern to use when an input is a directory (default: '*.csv').",
    )
    p.add_argument("--recursive", action="store_true", help="Recurse into directories when searching.")
    p.add_argument("--output", required=True, help="Output CSV file path to write combined data.")
    p.add_argument(
        "--no-check-columns",
        dest="check_columns",
        action="store_false",
        help="Do not verify that all input files have identical column headers.",
    )
    p.add_argument("--force", action="store_true", help="Overwrite output file if it exists.")
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    files = find_files(args.inputs, pattern=args.pattern, recursive=args.recursive)
    if not files:
        parser.error("No input CSV files found for the given inputs/pattern.")

    out_path = Path(args.output)
    if out_path.exists() and not args.force:
        parser.error(f"Output file {out_path} already exists. Use --force to overwrite.")

    df = concat_csvs(files, check_columns=args.check_columns)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"[✓] Wrote {len(df)} rows from {len(files)} files to {out_path}")


if __name__ == "__main__":
    main()
