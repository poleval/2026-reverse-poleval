#!/usr/bin/env python3
"""Step 3 of 3: compute the official Reverse PolEval score (discrimination
x normalised diversity x harmonic pairwise separation) from the
correctness matrix produced by evaluate_responses.py.

Example:
    python scripts/compute_metric.py --matrix correctness_matrix.json --per-item --per-pair

Implements the formulas from ../README.md, "Ranking metrics":

  - discrimination_i = 4 * p_i * (1 - p_i), where p_i is the fraction of
    the panel correct on item i (max 1 when the panel is split 50/50, 0
    when unanimous). Submission discrimination = mean over items.
  - diversity: normalised Simpson diversity of complete item correctness
    bitvectors. Repeated outcome cuts reduce the score even when every
    individual model has 50% accuracy.
  - harmonic pairwise separation: for every pair of models (k, l), the
    separation rate is the fraction of items on which they disagree.
    With saturation threshold t (default 5%), each pair earns
    s = min(rate / t, 1). Pairwise separation is the harmonic mean of
    these credits, with each credit floored at epsilon (default 0.01)
    so a single r=0 pair does not send the term to 0. Weakly separated
    pairs therefore pull the component down more than they would under
    an arithmetic mean.
  - score = discrimination * diversity * pairwise_separation.
    Submitting fewer than N_max = 200 items is allowed; a short set is
    not scaled down by n/N_max. Separating all model pairs and covering
    distinct bitvectors is already harder with fewer items.
"""
from __future__ import annotations

import argparse
from collections import Counter
import itertools
import json
import os
import sys
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from task_params import PAIRWISE_FLOOR, PAIRWISE_THRESHOLD  # noqa: E402


def load_matrix(path: str) -> Tuple[List[str], List[dict]]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    models = data["models"]
    items = data["items"]
    if not models:
        raise ValueError("no models in correctness matrix")
    if not items:
        raise ValueError("no items in correctness matrix")
    return models, items


def bitvector(item: dict, models: List[str]) -> Tuple[int, ...]:
    return tuple(1 if item["correct"][m] else 0 for m in models)


def discrimination_score(items: List[dict], models: List[str]) -> Tuple[float, List[float]]:
    per_item = []
    for item in items:
        bits = bitvector(item, models)
        p = sum(bits) / len(models)
        per_item.append(4 * p * (1 - p))
    return sum(per_item) / len(per_item), per_item


def diversity_score(items: List[dict], models: List[str]) -> float:
    bitvectors = [bitvector(item, models) for item in items]

    if len(bitvectors) < 2:
        return 0.0

    n = len(bitvectors)
    counts = Counter(bitvectors)
    raw_diversity = 1.0 - sum(count * count for count in counts.values()) / (n * n)

    # At most min(n, 2**m) distinct correctness vectors can occur. Simpson
    # diversity is maximised when item counts are as even as possible across
    # those attainable vectors.
    attainable_vectors = min(n, 1 << len(models))
    base, remainder = divmod(n, attainable_vectors)
    minimum_squared_count = (
        (attainable_vectors - remainder) * base * base
        + remainder * (base + 1) * (base + 1)
    )
    maximum = 1.0 - minimum_squared_count / (n * n)
    return raw_diversity / maximum if maximum else 0.0


def pairwise_disagreement_rates(items: List[dict], models: List[str]) -> Dict[Tuple[str, str], float]:
    """For every pair of models, the fraction of items on which they disagree."""
    bitvectors = [bitvector(item, models) for item in items]
    n = len(bitvectors)
    rates: Dict[Tuple[str, str], float] = {}
    for k, l in itertools.combinations(range(len(models)), 2):
        disagreements = sum(1 for bv in bitvectors if bv[k] != bv[l])
        rates[(models[k], models[l])] = disagreements / n if n else 0.0
    return rates


def pairwise_separation_score(
    rates: Dict[Tuple[str, str], float],
    threshold: float = PAIRWISE_THRESHOLD,
    floor: float = PAIRWISE_FLOOR,
) -> float:
    """Harmonic mean of per-pair credits, each floored at ``floor``.

    Credit rises linearly to 1 at ``threshold``. Flooring avoids a true
    zero sending the whole harmonic mean to 0.
    """
    if not 0 < threshold <= 1:
        raise ValueError("pairwise threshold must be in (0, 1]")
    if not 0 < floor <= 1:
        raise ValueError("pairwise floor must be in (0, 1]")
    if not rates:
        return 0.0
    credits = [max(min(rate / threshold, 1.0), floor) for rate in rates.values()]
    return len(credits) / sum(1.0 / s for s in credits)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--matrix", required=True, help="Path to correctness matrix JSON from evaluate_responses.py")
    parser.add_argument("--per-item", action="store_true", help="Also print per-item discrimination")
    parser.add_argument("--per-pair", action="store_true", help="Also print per-model-pair disagreement rates")
    parser.add_argument("--pairwise-threshold", type=float, default=PAIRWISE_THRESHOLD,
                         help="Disagreement rate (0-1) at which a model pair receives full separation "
                              "credit (default 0.05, i.e. 5%% of items); lower rates receive partial credit.")
    parser.add_argument("--pairwise-floor", type=float, default=PAIRWISE_FLOOR,
                         help="Floor applied to per-pair credit before the harmonic mean "
                              "(default 0.01), so a single unseparated pair does not zero the term.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    models, items = load_matrix(args.matrix)

    disc, per_item = discrimination_score(items, models)
    div = diversity_score(items, models)
    rates = pairwise_disagreement_rates(items, models)
    sep = pairwise_separation_score(rates, args.pairwise_threshold, args.pairwise_floor)
    score = disc * div * sep
    worst_pair, worst_rate = min(rates.items(), key=lambda kv: kv[1])

    print(f"models (m)                          : {len(models)}")
    print(f"items (n)                           : {len(items)}")
    print(f"discrimination                      : {disc:.4f}")
    print(f"diversity                           : {div:.4f}")
    print(f"harmonic pairwise separation (full credit at {args.pairwise_threshold:.0%}, "
          f"floor {args.pairwise_floor:.2f}): {sep:.4f}")
    print(f"worst pair                          : {worst_pair[0]} vs {worst_pair[1]} ({worst_rate:.3f})")
    print(f"score (disc x diversity x separation): {score:.4f}")

    if args.per_item:
        print("\nper-item discrimination:")
        for item, d in zip(items, per_item):
            snippet = item["input"][:60]
            print(f"  [{item['idx']:>4}] discrimination={d:.3f}  input={snippet!r}")

    if args.per_pair:
        print("\npairwise disagreement rates (ascending, worst first):")
        for (a, b), rate in sorted(rates.items(), key=lambda kv: kv[1]):
            print(f"  {a} vs {b}: {rate:.3f}")


if __name__ == "__main__":
    main()
