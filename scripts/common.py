"""Shared utilities for the Reverse PolEval reference pipeline.

Implements the pieces of the task proposal (../README.md) shared by
the three pipeline scripts:

    1. query_models.py        -- ask a model panel to answer submitted items
    2. evaluate_responses.py  -- score raw model outputs against gold
    3. compute_metric.py      -- turn the correctness matrix into the
                                  official discrimination x diversity x
                                  pairwise-separation score

Evaluator contract (see "Tracks" / "Main assumptions" in README.md):

    accept(prediction: str, gold: str) -> bool

It MUST be deterministic, MUST NOT touch the network, and MUST return a
plain bool -- not a float -- so the correctness bitvector used by the
ranking metrics is unambiguous. Official scoring uses a participant
evaluator only after organisers have manually accepted it; otherwise the
official exact-match normalisation is used. These scripts still fall back
automatically if a local file fails to load, as a development convenience.
"""
from __future__ import annotations

import importlib.util
import json
import os
import pickle
import re
import select
import signal
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional, Sequence

# Repo root: scripts/common.py -> parent.parent
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_dotenv(path: Optional[str] = None) -> Optional[str]:
    """Load KEY=VALUE pairs from .env into os.environ (do not override)."""
    env_path = path or os.path.join(_REPO_ROOT, ".env")
    if not os.path.isfile(env_path):
        return None
    with open(env_path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            if key and key not in os.environ:
                os.environ[key] = value
    return env_path

# Fixed official messages, published at Test A and used for every item.
DEFAULT_SYSTEM_PROMPT = (
    "Jesteś modelem rozwiązującym krótkie, automatycznie oceniane zadania "
    "dotyczące języka polskiego. Odpowiedz wyłącznie poprawną odpowiedzią na "
    "zadanie z wiadomości użytkownika. Nie dodawaj wyjaśnień, etykiet, "
    "cytatów ani dodatkowego tekstu."
)

EVALUATOR_TIMEOUT_SECONDS = 5.0


# --------------------------------------------------------------------------
# Normalisation
# --------------------------------------------------------------------------

def normalise(text: Optional[str], case_fold: bool = False) -> str:
    """Official normalisation: Unicode NFKC, strip, compact whitespace,
    optional case folding."""
    text = "" if text is None else str(text)
    text = unicodedata.normalize("NFKC", text)
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    if case_fold:
        text = text.casefold()
    return text


def default_exact_match(prediction: Optional[str], gold: Optional[str], case_fold: bool = False) -> bool:
    return normalise(prediction, case_fold) == normalise(gold, case_fold)


def aliases_match(
    prediction: Optional[str],
    gold: Optional[str],
    extra_forms: Optional[Sequence[str]] = None,
    case_fold: bool = False,
) -> bool:
    """Official aliases checker: prediction matches gold or any extra form.

    Comparison uses the same normalisation as exact match. ``gold`` is always
    a candidate; ``extra_forms`` are additional surface forms from
    the item's ``aliases`` array.
    """
    pred = normalise(prediction, case_fold)
    if not pred:
        return False
    candidates = [gold]
    if extra_forms:
        candidates.extend(extra_forms)
    return any(pred == normalise(form, case_fold) for form in candidates if form is not None)


# --------------------------------------------------------------------------
# Submitted JSON array (input, gold, optional aliases)
# --------------------------------------------------------------------------

@dataclass
class Item:
    idx: int
    input: str
    gold: str
    aliases: List[str] = field(default_factory=list)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def load_items(path: str) -> List[Item]:
    """Load the strict submission schema; indices are zero-based array positions.

    Budget and length limits are checked by validate_format.py. This loader
    checks types, fields and non-empty/unique inputs for every pipeline entry.
    """
    with open(path, encoding="utf-8") as f:
        records = json.load(f, object_pairs_hook=_unique_object)
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path}: expected a non-empty JSON array")
    items = []
    seen = set()
    for idx, record in enumerate(records):
        location = f"{path}: item {idx + 1}"
        if not isinstance(record, dict):
            raise ValueError(f"{location}: expected an object")
        if set(record) - {"input", "gold", "aliases"}:
            raise ValueError(f"{location}: unknown fields: {sorted(set(record) - {'input', 'gold', 'aliases'})}")
        for name in ("input", "gold"):
            if not isinstance(record.get(name), str) or not normalise(record[name]):
                raise ValueError(f"{location}: {name} must be a non-empty string")
        aliases = record.get("aliases", [])
        if not isinstance(aliases, list) or any(not isinstance(a, str) or not normalise(a) for a in aliases):
            raise ValueError(f"{location}: aliases must be an array of non-empty strings")
        key = normalise(record["input"])
        if key in seen:
            raise ValueError(f"{location}: duplicate input after official normalisation")
        seen.add(key)
        items.append(Item(idx=idx, input=record["input"], gold=record["gold"], aliases=aliases))
    return items


# --------------------------------------------------------------------------
# JSONL IO
# --------------------------------------------------------------------------

def write_jsonl(path: str, records: Iterable[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path: str) -> Iterator[dict]:
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


# --------------------------------------------------------------------------
# Evaluator loading + isolation
#
# NOTE: this is a reference implementation, not a hardened security
# sandbox. Each call is isolated in its own forked OS process (so a hang
# does not block the pipeline and a crash does not take it down) with a
# wall-clock timeout, but it does not strip network access or cap
# memory/CPU. A production deployment should additionally run this inside
# a container/VM with no network egress (e.g. via a network namespace,
# seccomp profile, or nsjail/firejail) before trusting participant-
# submitted code on organiser infrastructure. Requires a Unix-like OS
# (relies on os.fork).
# --------------------------------------------------------------------------

def _load_evaluator_function(evaluator_path: str):
    spec = importlib.util.spec_from_file_location("participant_evaluator", evaluator_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"could not load module from {evaluator_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    if not hasattr(module, "accept") or not callable(module.accept):
        raise ValueError(f"{evaluator_path} does not define a callable `accept(prediction, gold)`")
    return module.accept


def _call_in_forked_process(fn, args, timeout: float):
    """Run fn(*args) in a freshly forked child process and return its
    result, enforcing a wall-clock timeout.

    Only the (small, primitive) result is pickled across the pipe -- the
    function itself is *not* pickled, since fork() gives the child a copy
    of the parent's memory (including a dynamically-loaded evaluator
    module that was never registered as an importable file).
    """
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:  # child
        os.close(read_fd)
        try:
            result = fn(*args)
            payload = pickle.dumps(("ok", result))
        except BaseException as exc:  # noqa: BLE001 - report, don't crash the pipe write
            payload = pickle.dumps(("error", repr(exc)))
        try:
            with os.fdopen(write_fd, "wb") as f:
                f.write(payload)
        finally:
            os._exit(0)  # never run parent's cleanup/atexit code in the child

    os.close(write_fd)
    try:
        ready, _, _ = select.select([read_fd], [], [], timeout)
        if not ready:
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)
            raise TimeoutError(f"evaluator exceeded {timeout}s timeout")
        with os.fdopen(read_fd, "rb") as f:
            data = f.read()
        os.waitpid(pid, 0)
    except BaseException:
        try:
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)
        except OSError:
            pass
        raise

    if not data:
        raise RuntimeError("evaluator process produced no output (crashed?)")
    status, value = pickle.loads(data)
    if status == "error":
        raise RuntimeError(f"evaluator raised: {value}")
    return value


class Evaluator:
    """Wraps a participant evaluator. Official scoring uses the file only
    after manual organiser acceptance (README.md). A file that fails
    load-time validation falls back to exact match; a runtime failure aborts
    evaluation so one matrix cannot mix evaluator and exact-match verdicts.
    """

    def __init__(self, evaluator_path: Optional[str] = None, case_fold: bool = False,
                 timeout: float = EVALUATOR_TIMEOUT_SECONDS):
        self.case_fold = case_fold
        self.timeout = timeout
        self.fallback_reason: Optional[str] = None
        self._fn = None
        if evaluator_path:
            try:
                self._fn = _load_evaluator_function(evaluator_path)
                self._sanity_check()
            except Exception as exc:
                self.fallback_reason = f"failed to load/validate evaluator ({exc}); using default exact match"
                self._fn = None

    def _call_raw(self, prediction: str, gold: str) -> bool:
        result = _call_in_forked_process(self._fn, (prediction, gold), self.timeout)
        if not isinstance(result, bool):
            raise TypeError(f"evaluator must return bool, got {type(result).__name__}: {result!r}")
        return result

    def _sanity_check(self) -> None:
        probe = "__poleval_qualification_probe__"
        if self._call_raw(probe, probe) is not True:
            raise ValueError("evaluator does not accept gold == prediction")
        if self._call_raw("", "__poleval_should_not_match__") is True:
            raise ValueError("evaluator appears to accept an unrelated/empty prediction")

    def accept(self, prediction: str, gold: str, extra_forms: Optional[Sequence[str]] = None) -> bool:
        if extra_forms is not None:
            return aliases_match(prediction, gold, extra_forms, self.case_fold)
        if self._fn is None:
            return default_exact_match(prediction, gold, self.case_fold)
        try:
            return self._call_raw(prediction, gold)
        except Exception as exc:
            raise RuntimeError(
                f"evaluator raised or timed out ({exc}); discard this run and rerun the entire "
                "submission with official exact match"
            ) from exc

    def close(self) -> None:
        pass  # no persistent resources to release; kept for API stability

    def __enter__(self) -> "Evaluator":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
