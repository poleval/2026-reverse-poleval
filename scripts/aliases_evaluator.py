"""Official aliases checker for each item's optional aliases array in items.jsonl.

Gold is always accepted under official NFKC/whitespace normalisation.
No participant code or separate alias file is needed.
"""
from __future__ import annotations

import os
import sys
from typing import Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import aliases_match  # noqa: E402


def accept(
    prediction: str,
    gold: str,
    extra_forms: Optional[Sequence[str]] = None,
) -> bool:
    return aliases_match(prediction, gold, extra_forms)
