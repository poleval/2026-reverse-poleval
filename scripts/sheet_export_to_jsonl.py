#!/usr/bin/env python3
"""Optional helper: convert a two-column CSV/TSV spreadsheet export to items.jsonl.

Input headers may be input/gold or pytanie/odpowiedź. Multiline cells are
preserved. Aliases may be added to the JSONL file after conversion.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
from typing import List, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from task_params import N_ITEMS_MAX, N_ITEMS_MIN  # noqa: E402

HEADER_ALIASES = {
    "input",
    "gold",
    "pytanie",
    "odpowiedz",
    "odpowiedź",
    "question",
    "answer",
}


def _sniff_dialect(sample: str) -> csv.Dialect:
    try:
        return csv.Sniffer().sniff(sample, delimiters="\t,;")
    except csv.Error:
        dialect = csv.excel_tab if sample.count("\t") >= sample.count(",") else csv.excel
        return dialect


def _is_header(row: Sequence[str]) -> bool:
    if len(row) < 2:
        return False
    cells = {c.strip().lower() for c in row[:2]}
    return bool(cells & HEADER_ALIASES)


def load_pairs(path: str) -> List[Tuple[str, str]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        raw = f.read()
    if not raw.strip():
        raise SystemExit(f"{path}: empty file")

    dialect = _sniff_dialect(raw[:4096])
    rows = list(csv.reader(io.StringIO(raw, newline=""), dialect))
    if rows and _is_header(rows[0]):
        rows = rows[1:]

    pairs: List[Tuple[str, str]] = []
    for row_no, row in enumerate(rows, start=1):
        if not row or all(not c.strip() for c in row):
            continue
        if len(row) != 2:
            raise SystemExit(
                f"{path}: row {row_no}: expected 2 columns, got {len(row)}. "
                "Download as TSV from Google Sheets if questions contain commas."
            )
        input_, gold = row[0], row[1]
        if not input_ and not gold:
            continue
        pairs.append((input_, gold))
    return pairs


def write_jsonl(path: str, pairs: List[Tuple[str, str]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for input_, gold in pairs:
            f.write(json.dumps({"input": input_, "gold": gold}, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--in", dest="inp", required=True, help="CSV or TSV export from Sheets")
    parser.add_argument("--out", required=True, help="Destination items.jsonl")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pairs = load_pairs(args.inp)
    n = len(pairs)
    if n < N_ITEMS_MIN:
        raise SystemExit(f"need at least {N_ITEMS_MIN} items, found {n}")
    if n > N_ITEMS_MAX:
        raise SystemExit(f"at most {N_ITEMS_MAX} items allowed, found {n}")

    out_dir = os.path.dirname(os.path.abspath(args.out))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    write_jsonl(args.out, pairs)
    print(f"[ok] {n} items -> {args.out}")


if __name__ == "__main__":
    main()
