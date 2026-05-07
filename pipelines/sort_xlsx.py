#!/usr/bin/env python3
"""Sort an Excel file by a treatment column using a specified order.

Usage example:
    python pipelines/sort_xlsx.py input.xlsx -o output.xlsx
    python pipelines/sort_xlsx.py input.xlsx -c Treatment --order Saline Ghrelin
"""
from pathlib import Path
import argparse
import sys
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description="Sort an Excel file by a treatment column.")
    parser.add_argument('input', help='Input .xlsx file')
    parser.add_argument('-o', '--output', help='Output .xlsx file (default: input_sorted.xlsx)')
    parser.add_argument('-c', '--column', default='group', help='Name of treatment column (default: group)')
    parser.add_argument('--order', nargs='+', default=['Saline', 'Ghrelin'], help='Desired ordering for treatment values')
    parser.add_argument('-s', '--sheet', default=0, help='Sheet name or index to read (default: first sheet)')
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    try:
        df = pd.read_excel(input_path, sheet_name=args.sheet, engine='openpyxl')
    except Exception:
        df = pd.read_excel(input_path, sheet_name=args.sheet)

    # Find the column case-insensitively if necessary
    col_name = None
    if args.column in df.columns:
        col_name = args.column
    else:
        lower_map = {c.lower(): c for c in df.columns}
        if args.column.lower() in lower_map:
            col_name = lower_map[args.column.lower()]

    if col_name is None:
        raise SystemExit(f"Column '{args.column}' not found in sheet. Available columns: {list(df.columns)}")

    # Create categorical with requested ordering; values not in categories will sort after
    df[col_name] = pd.Categorical(df[col_name], categories=args.order, ordered=True)

    # Sort by the treatment column first, then by the remaining columns (stable)
    other_cols = [c for c in df.columns if c != col_name]
    sort_cols = [col_name] + other_cols
    df_sorted = df.sort_values(sort_cols, na_position='last')

    out_path = Path(args.output) if args.output else input_path.with_name(input_path.stem + '_sorted' + input_path.suffix)
    df_sorted.to_excel(out_path, index=False, engine='openpyxl')
    print(f"Wrote sorted file to: {out_path}")

if __name__ == '__main__':
    main()
