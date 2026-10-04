#!/usr/bin/env python3
"""Validate items.json: an array of input/gold objects with optional aliases.

This checks format only, not linguistic qualification or the task score.
"""
from __future__ import annotations

import argparse
from common import load_items, normalise
from task_params import MAX_GOLD_CHARS, MAX_INPUT_CHARS, MAX_ALIASES_PER_ITEM, N_ITEMS_MAX, N_ITEMS_MIN


def validate_file(path: str, n_min: int = N_ITEMS_MIN, n_max: int = N_ITEMS_MAX,
                  max_input: int = MAX_INPUT_CHARS, max_gold: int = MAX_GOLD_CHARS):
    try:
        items = load_items(path)
    except (OSError, ValueError) as exc:
        return [str(exc)], 0
    errors = []
    n = len(items)
    if not n_min <= n <= n_max:
        errors.append(f"{path}: expected {n_min}–{n_max} items, found {n}")
    for item in items:
        location = f"{path}: item {item.idx + 1}"
        if len(item.input) > max_input:
            errors.append(f"{location}: input length {len(item.input)} > {max_input}")
        if len(item.gold) > max_gold:
            errors.append(f"{location}: gold length {len(item.gold)} > {max_gold}")
        if len(item.aliases) > MAX_ALIASES_PER_ITEM:
            errors.append(f"{location}: more than {MAX_ALIASES_PER_ITEM} aliases")
        seen = {normalise(item.gold)}
        for alias in item.aliases:
            if len(alias) > max_gold:
                errors.append(f"{location}: alias length {len(alias)} > {max_gold}")
            key = normalise(alias)
            if key in seen:
                errors.append(f"{location}: alias duplicates gold or another alias after normalisation")
            seen.add(key)
    return errors, n


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", required=True, help="Path to items.json")
    parser.add_argument("--min-n", type=int, default=N_ITEMS_MIN)
    parser.add_argument("--max-n", type=int, default=N_ITEMS_MAX)
    parser.add_argument("--max-input-chars", type=int, default=MAX_INPUT_CHARS)
    parser.add_argument("--max-gold-chars", type=int, default=MAX_GOLD_CHARS)
    return parser.parse_args()


def main():
    args = parse_args()
    errors, n = validate_file(args.items, args.min_n, args.max_n,
                              args.max_input_chars, args.max_gold_chars)
    print(f"format_ok\t{int(not errors)}")
    print(f"n\t{n}")
    if errors:
        for error in errors:
            print(f"error\t{error}")
        raise SystemExit(1)
    print(f"[ok] {args.items}: {n} items, unique inputs, length and alias limits held")


if __name__ == "__main__":
    main()
