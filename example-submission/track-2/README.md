# Example Track 2 submission (smoke test)

This is the shape of a Track 2 delivery: a **repository** organisers clone
and run offline.

Implements `generate(seed) → 200` items. Deterministic, no network.
This example has no external lexicon; a real morphology generator would
vendor a snapshot under `data/` (SQLite/TSV + licence + content hash) and
sample it — never download SGJP or call a service at generate time.

```bash
python example-submission/track-2/generate.py --seed 1 --out /tmp/seed1.json
```

Expected layout for a real submission:

```text
generate.py
data/                 # vendored DB / forms table
README.md
LICENSE               # OSI-approved (this example: MIT)
data/LICENSE          # redistributable with the archive
```

Licence: MIT (OSI-approved, so organisers can rerun it). Not a valid
Reverse PolEval entry: arithmetic, gold survives translation.
