#!/usr/bin/env python3
"""Example Track 2 generator: integer multiplication.

Smoke-test submission. The gold survives translation, so this set fails
the Polish-necessity gate on purpose.

    generate(seed) -> n items, n = 200
"""
from __future__ import annotations

import argparse
import json
import random
from typing import List, Tuple

N_MIN = 50
N_MAX = 200

Item = Tuple[str, str]


def generate(seed: int, n: int = N_MAX, lo: int = 10, hi: int = 99) -> List[Item]:
    if not N_MIN <= n <= N_MAX:
        raise ValueError(f"n must be in [{N_MIN}, {N_MAX}]")
    rng = random.Random(seed)
    seen = set()
    items: List[Item] = []
    while len(items) < n:
        a = rng.randint(lo, hi)
        b = rng.randint(lo, hi)
        if (a, b) in seen:
            continue
        seen.add((a, b))
        items.append((f"Ile wynosi {a} razy {b}?", str(a * b)))
    return items


def write_json(path: str, items: List[Item]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([{"input": input_, "gold": gold} for input_, gold in items],
                  f, ensure_ascii=False, indent=2)
        f.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--n", type=int, default=N_MAX)
    parser.add_argument("--out", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    items = generate(args.seed, args.n)
    write_json(args.out, items)
    print(f"[ok] seed={args.seed} n={len(items)} -> {args.out}")


if __name__ == "__main__":
    main()
