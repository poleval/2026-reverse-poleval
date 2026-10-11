"""Reference evaluator: reproduces the official default exact-match
normalisation. For extra surface forms prefer the official aliases
checker (inline ``aliases`` in ``items.jsonl``)
instead of custom code. Copy this file only if you need an equivalence
that aliases cannot express.

Contract (see ../README.md, "Tracks"):

    accept(prediction: str, gold: str) -> bool

Must be deterministic, must not touch the network, and must return a
plain bool.
"""
import re
import unicodedata


def _normalise(text: str) -> str:
    text = "" if text is None else str(text)
    text = unicodedata.normalize("NFKC", text)
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def accept(prediction: str, gold: str) -> bool:
    return _normalise(prediction) == _normalise(gold)
