#!/usr/bin/env python3
"""Validate StudyBuddy JSONL training and hold-out evaluation data."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> list[dict]:
    rows = []
    prompts = set()
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            messages = row.get("messages")
            if not isinstance(messages, list) or len(messages) < 2:
                raise SystemExit(f"{path}:{line_number}: expected messages with at least two turns")
            if not any(m.get("role") == "user" for m in messages):
                raise SystemExit(f"{path}:{line_number}: missing user message")
            if not any(m.get("role") == "assistant" for m in messages):
                raise SystemExit(f"{path}:{line_number}: missing assistant message")
            if any(not isinstance(m.get("content"), str) or not m["content"].strip() for m in messages):
                raise SystemExit(f"{path}:{line_number}: every message needs non-empty string content")
            prompt = next(m["content"].strip() for m in messages if m["role"] == "user")
            if prompt in prompts:
                raise SystemExit(f"{path}:{line_number}: duplicate user prompt in the same file")
            prompts.add(prompt)
            rows.append(row)
    if not rows:
        raise SystemExit(f"{path}: no examples found")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=Path, default=Path("training/train.jsonl"))
    parser.add_argument("--eval", type=Path, default=Path("training/eval.jsonl"))
    args = parser.parse_args()
    train, evaluation = load(args.train), load(args.eval)
    train_prompts = {next(m["content"].strip() for m in x["messages"] if m["role"] == "user") for x in train}
    eval_prompts = {next(m["content"].strip() for m in x["messages"] if m["role"] == "user") for x in evaluation}
    overlap = train_prompts & eval_prompts
    if overlap:
        raise SystemExit(f"Data leakage: {len(overlap)} evaluation prompts also appear in training data")
    print(f"OK: {len(train)} training examples, {len(evaluation)} held-out evaluation examples.")
    print("No duplicate prompts within either file and no exact prompt overlap between train/eval.")
    print("This validates structure only; it does not certify answer quality or prevent semantic leakage.")


if __name__ == "__main__":
    main()
