"""Frozen Test A parameters for the Reverse PolEval development period.

These values are binding from 13 October 2026. Scripts import them rather
than copying literals.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Track 1
N_ITEMS_MAX = 200
N_ITEMS_MIN = 50
N_ITEMS = N_ITEMS_MAX  # alias: item budget
MAX_INPUT_CHARS = 2000
MAX_GOLD_CHARS = 80
MAX_ALIASES_PER_ITEM = 5

# Track 2
K_SEEDS = 3  # Test B official ranking (mean over hidden seeds)
K_SEEDS_DEV = 1  # unofficial development-panel feedback only
MAX_SEED_JACCARD = 0.5
GENERATOR_TIMEOUT_SECONDS = 120.0

# Scoring
PAIRWISE_THRESHOLD = 0.05
PAIRWISE_FLOOR = 0.01
EVALUATOR_TIMEOUT_SECONDS = 5.0
SAMPLE_AUDIT_SIZE = 30
CASE_FOLD = False

# Decoding (development and hidden panels)
TEMPERATURE = 0.0
MAX_NEW_TOKENS = 64
PARAM_SIZE_CAP = "40B"

# Unofficial development-panel feedback
FEEDBACK_TZ = "Europe/Warsaw"
FEEDBACK_MAX_PER_TEAM_PER_WEEK = 1  # ISO week, Monday–Sunday in FEEDBACK_TZ

DEVELOPMENT_DIR = ROOT / "development"
MODELS_FILE = DEVELOPMENT_DIR / "models.txt"
FEEDBACK_LOG = DEVELOPMENT_DIR / "feedback-log.tsv"
QUALIFICATION_LOG = DEVELOPMENT_DIR / "qualification-log.tsv"
EVALUATOR_STATUS = DEVELOPMENT_DIR / "evaluator-status.tsv"


def load_model_ids(path: Path | str = MODELS_FILE) -> list[str]:
    path = Path(path)
    models = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                models.append(line)
    if not models:
        raise ValueError(f"{path}: no model IDs found")
    return models
