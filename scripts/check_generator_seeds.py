#!/usr/bin/env python3
"""Track 2 seed-dependence check: compare materialised item sets and fail
if any two share too many `input` strings.

Example:
    python scripts/check_generator_seeds.py \\
        --sets seed0.jsonl seed1.jsonl seed2.jsonl \\
        --max-jaccard 0.5

A generator that ignores `seed` (a static Track 1 set with an unused
argument) is disqualified from Track 2, per README.md.
"""
from __future__ import annotations

import argparse
import itertools
import os
import sys
from typing import List, Set, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_items  # noqa: E402
from task_params import MAX_SEED_JACCARD  # noqa: E402


def input_set(items_path: str) -> Set[str]:
    return {item.input for item in load_items(items_path)}


def jaccard(a: Set[str], b: Set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def pairwise_jaccard(paths: List[str]) -> List[Tuple[str, str, float]]:
    sets = [(path, input_set(path)) for path in paths]
    out = []
    for (p, a), (q, b) in itertools.combinations(sets, 2):
        out.append((p, q, jaccard(a, b)))
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sets", nargs="+", required=True,
                        help="Two or more Track 2 materialisations (JSONL: input, gold, optional aliases)")
    parser.add_argument("--max-jaccard", type=float, default=MAX_SEED_JACCARD,
                        help="Disqualify if any pair of materialisations has Jaccard "
                             f"overlap on `input` above this value (default {MAX_SEED_JACCARD}, frozen at Test A)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if len(args.sets) < 2:
        raise SystemExit("need at least two materialisations")
    if not 0 <= args.max_jaccard <= 1:
        raise SystemExit("--max-jaccard must be in [0, 1]")

    overlaps = pairwise_jaccard(args.sets)
    worst_p, worst_q, worst = max(overlaps, key=lambda row: row[2])
    for p, q, value in sorted(overlaps, key=lambda row: row[2], reverse=True):
        flag = " FAIL" if value > args.max_jaccard else ""
        print(f"Jaccard({p}, {q}) = {value:.3f}{flag}")

    print(f"worst overlap: {worst:.3f}  ({worst_p} vs {worst_q})")
    print(f"threshold:     {args.max_jaccard:.3f}")
    if worst > args.max_jaccard:
        raise SystemExit("seed-independent generator (Track 2 disqualified)")
    print("seed-dependence: ok")


if __name__ == "__main__":
    main()
