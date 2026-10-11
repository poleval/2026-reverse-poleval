# Example submission (smoke test)

This folder is a complete dummy entry for pipeline tests. **It is not a
valid Reverse PolEval submission:** every item is integer multiplication,
so the Polish-necessity gate fails.

| Track | Path | What it is |
| --- | --- | --- |
| 1 | `track-1/items.jsonl` | 200 items from `generate(seed=1)` |
| 2 | `track-2/generate.py` | `generate(seed) → 200` items |

No custom evaluator: official exact match. Extra surface forms go in each item's optional `aliases` array (not used here).

```bash
python scripts/validate_format.py --items example-submission/track-1/items.jsonl

python example-submission/track-2/generate.py --seed 1 --out /tmp/mul-1.jsonl
python example-submission/track-2/generate.py --seed 2 --out /tmp/mul-2.jsonl
python scripts/check_generator_seeds.py --sets /tmp/mul-1.jsonl /tmp/mul-2.jsonl
```

`track-1/items.jsonl` must match `generate(1)`.
