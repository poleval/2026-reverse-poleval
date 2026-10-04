#!/usr/bin/env python3
"""Score model JSONL responses against items.json, including inline aliases.

Example:
    python scripts/evaluate_responses.py --items items.json --responses-dir responses --output correctness_matrix.json

Custom evaluators require manual acceptance and a hermetic sandbox for
organiser use. They cannot be combined with non-empty inline aliases.
"""
from __future__ import annotations

import argparse
import glob
import json
from common import Evaluator, load_items, read_jsonl
from task_params import CASE_FOLD


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", required=True, help="Original items.json used for inference")
    parser.add_argument("--responses-dir", required=True)
    parser.add_argument("--evaluator", default=None)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    submitted = load_items(args.items)
    if args.evaluator and any(item.aliases for item in submitted):
        raise SystemExit("use either inline aliases or a custom evaluator, not both")
    response_files = sorted(glob.glob(f"{args.responses_dir}/*.jsonl"))
    if not response_files:
        raise SystemExit(f"no .jsonl files found in {args.responses_dir}")
    # Validate the entire matrix before executing a checker or writing output.
    outputs = {}
    for path in response_files:
        records = list(read_jsonl(path))
        if not records:
            raise SystemExit(f"{path}: empty response file")
        model = records[0].get("model")
        if not isinstance(model, str) or not model or model in outputs:
            raise SystemExit(f"{path}: missing or duplicate model")
        by_idx = {}
        for rec in records:
            idx = rec.get("idx")
            if type(idx) is not int or not 0 <= idx < len(submitted) or idx in by_idx:
                raise SystemExit(f"{path}: unexpected or duplicate item index {idx!r}")
            item = submitted[idx]
            if (rec.get("model") != model or rec.get("input") != item.input
                    or rec.get("gold") != item.gold
                    or rec.get("aliases", []) != item.aliases):
                raise SystemExit(f"{path}: item {idx + 1} does not match the submission/model")
            if not isinstance(rec.get("output"), str):
                raise SystemExit(f"{path}: item {idx + 1}: output must be a string")
            by_idx[idx] = rec["output"]
        if len(by_idx) != len(submitted):
            raise SystemExit(f"{path}: incomplete responses: {len(by_idx)}/{len(submitted)} items")
        outputs[model] = by_idx
    models = list(outputs)
    matrix = []
    with Evaluator(args.evaluator, case_fold=CASE_FOLD, timeout=args.timeout) as evaluator:
        for item in submitted:
            matrix.append({
                "idx": item.idx, "input": item.input, "gold": item.gold,
                "aliases": item.aliases,
                "correct": {model: evaluator.accept(outputs[model][item.idx], item.gold,
                            None if args.evaluator else item.aliases) for model in models},
            })
        if evaluator.fallback_reason:
            print(f"[warn] {evaluator.fallback_reason}")
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump({"models": models, "items": matrix}, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[done] wrote {args.output} ({len(matrix)} items x {len(models)} models)")


if __name__ == "__main__":
    main()
