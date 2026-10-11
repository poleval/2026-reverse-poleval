#!/usr/bin/env python3
"""Step 1 of 3: query a model panel over an OpenAI-compatible chat
completions endpoint (localhost by default) with a participant's Track 1
submission, and save the raw answers.

Example:
    # credentials in .env: EVAL_BASE_URL, EVAL_API_KEY
    python scripts/query_models.py \\
        --items example-submission/track-1/items.jsonl \\
        --models-file development/models.txt \\
        --output-dir example-submission/runs/responses

Writes one JSONL file per model, `responses/<safe-model-name>.jsonl`, with
one record per item:

    {"idx": 0, "input": "...", "gold": "...", "model": "...",
     "prompt": "...", "output": "..."}

Every item uses the fixed official system message and the fixed
unmodified `input` as the user message, per README.md ("Main
assumptions").

Decoding defaults to temperature 0 (greedy/deterministic), per
README.md.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from typing import List, Optional, Tuple

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (  # noqa: E402
    DEFAULT_SYSTEM_PROMPT,
    load_dotenv,
    load_items,
    read_jsonl,
)
from task_params import load_model_ids  # noqa: E402

DEFAULT_BASE_URL = "http://localhost:8000/v1"


def safe_filename(model_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", model_id)


def build_messages(prompt: str) -> List[dict]:
    return [
        {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]


def query_one(base_url: str, api_key: str, model: str, prompt: str,
              temperature: float, max_tokens: int, timeout: float, retries: int,
              disable_thinking: bool = False) -> Tuple[str, dict]:
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": build_messages(prompt),
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if disable_thinking:
        # vLLM / Qwen3.x: boolean false only; strings like "false" are ignored.
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    last_error: Optional[BaseException] = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return content, data
        except Exception as exc:  # noqa: BLE001 - broad on purpose, retried
            last_error = exc
            if attempt < retries:
                time.sleep(min(2 ** attempt, 30))
    raise RuntimeError(f"failed to query model {model!r} after {retries} attempts: {last_error}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--items", required=True, help="Path to items.jsonl (input, gold, optional aliases)")
    parser.add_argument("--models", nargs="+", default=None, help="One or more model IDs on the endpoint")
    parser.add_argument("--models-file", default=None,
                        help="Text file with one model ID per line (alternative to --models)")
    parser.add_argument("--output-dir", required=True, help="Directory to write one JSONL file per model")
    parser.add_argument("--base-url", default=None,
                         help="OpenAI-compatible base URL (default: EVAL_BASE_URL from .env, "
                              f"else {DEFAULT_BASE_URL})")
    parser.add_argument("--api-key-env", default="EVAL_API_KEY",
                         help="Env var holding the API key (default: EVAL_API_KEY from .env)")
    parser.add_argument("--temperature", type=float, default=0.0,
                         help="Decoding temperature; the proposal fixes this at 0 (greedy)")
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--timeout", type=float, default=60.0, help="Per-request HTTP timeout in seconds")
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--limit", type=int, default=None, help="Only query the first N items (smoke-testing)")
    parser.add_argument("--save-raw-response", action="store_true",
                         help="Also store the full raw API response under 'raw_response' (bulkier files)")
    parser.add_argument("--no-resume", action="store_true",
                        help="Overwrite existing JSONL files instead of skipping completed idxs")
    parser.add_argument("--disable-thinking", action="store_true",
                        help="Send chat_template_kwargs.enable_thinking=false (Qwen3.x non-thinking). "
                             "No effect on models whose template always thinks (e.g. QwQ-32B).")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    env_file = load_dotenv()
    if env_file:
        print(f"[info] loaded {env_file}", file=sys.stderr)

    base_url = args.base_url or os.environ.get("EVAL_BASE_URL") or DEFAULT_BASE_URL
    api_key = os.environ.get(args.api_key_env) or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit(
            f"API key not set: put {args.api_key_env} in .env (see .env.example) "
            "or export it in the environment"
        )

    if args.models_file:
        file_models = load_model_ids(args.models_file)
        args.models = (args.models or []) + file_models
    if not args.models:
        raise SystemExit("provide --models and/or --models-file")

    items = load_items(args.items)
    if args.limit:
        items = items[: args.limit]

    os.makedirs(args.output_dir, exist_ok=True)

    for model in args.models:
        out_path = os.path.join(args.output_dir, f"{safe_filename(model)}.jsonl")
        done_idxs = set()
        if os.path.exists(out_path) and not args.no_resume:
            expected = {
                item.idx: (item.input, item.gold, item.aliases, item.input)
                for item in items
            }
            for rec in read_jsonl(out_path):
                idx = rec.get("idx")
                if (
                    idx in expected
                    and rec.get("model") == model
                    and (rec.get("input"), rec.get("gold"), rec.get("aliases", []), rec.get("prompt")) == expected[idx]
                ):
                    if idx in done_idxs:
                        raise SystemExit(f"{out_path}: duplicate response index {idx}")
                    done_idxs.add(idx)
                else:
                    raise SystemExit(f"{out_path}: response does not match items; use a fresh output directory")
        elif os.path.exists(out_path) and args.no_resume:
            os.remove(out_path)

        remaining = [it for it in items if it.idx not in done_idxs]
        print(f"[info] querying {model}: {len(remaining)} remaining / {len(items)} items -> {out_path}")
        if not remaining:
            print(f"[info] {model}: already complete, skipping")
            continue

        with open(out_path, "a", encoding="utf-8") as out_f:
            for item in remaining:
                prompt = item.input
                output, raw = query_one(
                    base_url, api_key, model, prompt,
                    args.temperature, args.max_tokens, args.timeout, args.retries,
                    disable_thinking=args.disable_thinking,
                )
                record = {
                    "idx": item.idx,
                    "input": item.input,
                    "gold": item.gold,
                    "aliases": item.aliases,
                    "model": model,
                    "prompt": prompt,
                    "output": output,
                }
                if args.save_raw_response:
                    record["raw_response"] = raw
                out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                out_f.flush()
                print(f"  [{item.idx}] ok", file=sys.stderr)

    print("[done]")


if __name__ == "__main__":
    main()
