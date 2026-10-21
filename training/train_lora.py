#!/usr/bin/env python3
"""Supervised LoRA fine-tuning for StudyBuddy Advanced.

Designed for a CUDA GPU runtime (for example, a free Colab GPU when available).
This is real parameter-efficient fine-tuning, not just a changed system prompt.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import torch
from datasets import Dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
from trl import SFTConfig, SFTTrainer


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on {path}:{line_number}: {exc}") from exc
            messages = item.get("messages")
            if not isinstance(messages, list) or len(messages) < 2:
                raise ValueError(f"{path}:{line_number} needs a messages array with at least a user and assistant message.")
            roles = [message.get("role") for message in messages]
            if "user" not in roles or "assistant" not in roles:
                raise ValueError(f"{path}:{line_number} must contain user and assistant roles.")
            if not all(isinstance(message.get("content"), str) for message in messages):
                raise ValueError(f"{path}:{line_number} each message needs string content.")
            rows.append(item)
    if not rows:
        raise ValueError(f"No valid training examples found in {path}")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-model", default="Qwen/Qwen3-1.7B",
                        help="Hugging Face base model ID. Use the exact matching base when exporting.")
    parser.add_argument("--train-file", type=Path, default=Path("training/train.jsonl"))
    parser.add_argument("--eval-file", type=Path, default=Path("training/eval.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("studybuddy-training-output"))
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--skip-merge", action="store_true",
                        help="Save only the LoRA adapter, without merging a full checkpoint.")
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise SystemExit(
            "No CUDA GPU is available. This training script is designed for an NVIDIA CUDA runtime. "
            "Your Ryzen/AMD laptop is better used for inference; open training/StudyBuddy_Advanced_Finetune.ipynb "
            "in Google Colab and select a GPU runtime if one is available."
        )
    if args.max_length < 256:
        raise SystemExit("--max-length should be at least 256.")
    set_seed(args.seed)

    train_rows = read_jsonl(args.train_file)
    eval_rows = read_jsonl(args.eval_file)
    print(f"Base model: {args.base_model}")
    print(f"Training examples: {len(train_rows)} | Held-out evaluation examples: {len(eval_rows)}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    use_bf16 = torch.cuda.is_bf16_supported()
    dtype = torch.bfloat16 if use_bf16 else torch.float16

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=dtype,
        device_map="auto",
        low_cpu_mem_usage=True,
    )
    model.config.use_cache = False

    lora = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
    )

    output_dir = args.output_dir.resolve()
    checkpoints = output_dir / "checkpoints"
    adapter_dir = output_dir / "adapter"
    merged_dir = output_dir / "merged-fp16"
    output_dir.mkdir(parents=True, exist_ok=True)

    config = SFTConfig(
        output_dir=str(checkpoints),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=args.learning_rate,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        logging_steps=2,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        bf16=use_bf16,
        fp16=not use_bf16,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        max_length=args.max_length,
        packing=False,
        assistant_only_loss=True,
        report_to="none",
        optim="adamw_torch",
        seed=args.seed,
        data_seed=args.seed,
    )

    trainer = SFTTrainer(
        model=model,
        args=config,
        train_dataset=Dataset.from_list(train_rows),
        eval_dataset=Dataset.from_list(eval_rows),
        processing_class=tokenizer,
        peft_config=lora,
    )

    result = trainer.train()
    trainer.save_model(str(adapter_dir))
    tokenizer.save_pretrained(adapter_dir)
    metrics = dict(result.metrics)
    try:
        metrics.update(trainer.evaluate())
    except Exception as exc:  # Preserve the training result if eval logging has a version-specific issue.
        metrics["evaluation_warning"] = str(exc)
    metrics.update({
        "base_model": args.base_model,
        "train_examples": len(train_rows),
        "eval_examples": len(eval_rows),
        "epochs_requested": args.epochs,
        "max_length": args.max_length,
        "adapter_dir": str(adapter_dir),
        "warning": "A small starter dataset is not sufficient to guarantee general improvement. Compare held-out tasks before replacing your current model.",
    })
    (output_dir / "training_report.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"LoRA adapter saved to: {adapter_dir}")
    print(f"Training report saved to: {output_dir / 'training_report.json'}")

    if args.skip_merge:
        print("Merge skipped; to create a full checkpoint, rerun without --skip-merge.")
        return

    print("Merging LoRA into the original-precision base weights for GGUF conversion...")
    merged_model = trainer.model.merge_and_unload()
    merged_model.config.use_cache = True
    merged_dir.mkdir(parents=True, exist_ok=True)
    merged_model.save_pretrained(
        merged_dir,
        safe_serialization=True,
        max_shard_size="2GB",
    )
    tokenizer.save_pretrained(merged_dir)
    print(f"Merged checkpoint saved to: {merged_dir}")
    print("Next: run training/export_to_ollama.py on the merged-fp16 directory.")


if __name__ == "__main__":
    main()
