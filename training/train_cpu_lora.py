#!/usr/bin/env python3
"""Low-priority CPU-only LoRA fine-tuning for StudyBuddy on modest Windows laptops.

Default base: Qwen3 0.6B. Expect slow training on a Ryzen 3-class CPU.
This does real parameter-efficient fine-tuning, but the small starter dataset cannot
guarantee better general reasoning. Do not use this script on a machine you need to
remain fully responsive during the run.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# Keep BLAS/PyTorch from trying to use every core before Torch is imported.
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"Dataset file not found: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path}, line {line_number}: {exc}") from exc
            messages = record.get("messages")
            if not isinstance(messages, list) or len(messages) < 2:
                raise ValueError(f"{path}, line {line_number}: expected at least two messages.")
            if not any(m.get("role") == "user" for m in messages):
                raise ValueError(f"{path}, line {line_number}: missing user message.")
            if not any(m.get("role") == "assistant" for m in messages):
                raise ValueError(f"{path}, line {line_number}: missing assistant message.")
            if any(not isinstance(m.get("content"), str) or not m["content"].strip() for m in messages):
                raise ValueError(f"{path}, line {line_number}: every message needs non-empty string content.")
            rows.append(record)
    if not rows:
        raise ValueError(f"No valid training examples in {path}")
    return rows


def set_low_priority() -> None:
    """Make training yield CPU time to interactive apps where supported."""
    try:
        import psutil

        process = psutil.Process()
        if os.name == "nt":
            process.nice(psutil.IDLE_PRIORITY_CLASS)
        else:
            os.nice(10)
        print("Process priority lowered to help keep the laptop responsive.", flush=True)
    except Exception as exc:
        print(f"Could not lower process priority automatically: {exc}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-model", default="Qwen/Qwen3-0.6B")
    parser.add_argument("--train-file", type=Path, default=Path("training/train.jsonl"))
    parser.add_argument("--eval-file", type=Path, default=Path("training/eval.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("studybuddy-cpu-training-output"))
    parser.add_argument("--epochs", type=float, default=1.0)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--max-examples", type=int, default=0, help="0 uses all examples; try 12 for a quick smoke test.")
    parser.add_argument("--cpu-threads", type=int, default=2)
    parser.add_argument("--min-free-gib", type=float, default=5.0)
    parser.add_argument("--force-low-memory", action="store_true", help="Continue despite low available RAM; out-of-memory risk increases.")
    parser.add_argument("--normal-priority", action="store_true", help="Do not lower process priority.")
    args = parser.parse_args()

    if args.max_length < 128:
        raise SystemExit("--max-length should be at least 128.")
    if args.cpu_threads < 1 or args.cpu_threads > 4:
        raise SystemExit("--cpu-threads must be between 1 and 4 for this low-resource profile.")
    try:
        import psutil
    except ImportError as exc:
        raise SystemExit("Missing psutil. Install training/requirements-cpu.txt first.") from exc

    memory = psutil.virtual_memory()
    available_gib = memory.available / (1024 ** 3)
    total_gib = memory.total / (1024 ** 3)
    print(f"Detected RAM: {total_gib:.1f} GiB total, {available_gib:.1f} GiB available.")
    print("CPU-only training is slow. Use AC power, close other apps, and expect the laptop to feel slower.")
    if available_gib < args.min_free_gib and not args.force_low_memory:
        raise SystemExit(
            f"Only {available_gib:.1f} GiB RAM is currently available; this run requires at least "
            f"{args.min_free_gib:.1f} GiB available by default. Close apps and retry, or explicitly "
            "use --force-low-memory at your own risk. 8 GiB total RAM is a bare minimum; 16 GiB is safer."
        )

    os.environ["OMP_NUM_THREADS"] = str(args.cpu_threads)
    os.environ["MKL_NUM_THREADS"] = str(args.cpu_threads)

    import torch
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
    from trl import SFTConfig, SFTTrainer

    if torch.cuda.is_available():
        print("A GPU exists but this script deliberately trains on CPU.")
    torch.set_num_threads(args.cpu_threads)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    set_seed(42)
    if not args.normal_priority:
        set_low_priority()

    train_rows = read_jsonl(args.train_file)
    eval_rows = read_jsonl(args.eval_file)
    if args.max_examples > 0:
        train_rows = train_rows[:args.max_examples]
    print(f"Base model: {args.base_model}")
    print(f"Training examples: {len(train_rows)} | held-out evaluation examples: {len(eval_rows)}")
    print(f"Device: CPU | threads: {args.cpu_threads} | max length: {args.max_length} | epochs: {args.epochs}")
    print("Downloading/loading the base model may take time on the first run...")

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True,
    )
    model.to("cpu")
    model.config.use_cache = False

    lora = LoraConfig(
        r=4,
        lora_alpha=8,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "v_proj"],
    )

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    adapter_dir = output_dir / "adapter"
    merged_dir = output_dir / "merged-f32"

    config = SFTConfig(
        output_dir=str(output_dir / "checkpoints"),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=5e-5,
        lr_scheduler_type="linear",
        warmup_ratio=0.03,
        logging_steps=2,
        eval_strategy="epoch",
        save_strategy="no",
        bf16=False,
        fp16=False,
        use_cpu=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        max_length=args.max_length,
        packing=False,
        assistant_only_loss=True,
        report_to="none",
        optim="adamw_torch",
        dataloader_num_workers=0,
        seed=42,
        data_seed=42,
    )
    trainer = SFTTrainer(
        model=model,
        args=config,
        train_dataset=Dataset.from_list(train_rows),
        eval_dataset=Dataset.from_list(eval_rows),
        processing_class=tokenizer,
        peft_config=lora,
    )

    started = time.time()
    train_result = trainer.train()
    print(f"Training took {(time.time() - started) / 60:.1f} minutes.", flush=True)
    trainer.save_model(str(adapter_dir))
    tokenizer.save_pretrained(adapter_dir)
    metrics = dict(train_result.metrics)
    try:
        metrics.update(trainer.evaluate())
    except Exception as exc:
        metrics["evaluation_warning"] = str(exc)
    metrics.update({
        "base_model": args.base_model,
        "train_examples": len(train_rows),
        "eval_examples": len(eval_rows),
        "epochs_requested": args.epochs,
        "max_length": args.max_length,
        "device": "cpu",
        "cpu_threads": args.cpu_threads,
        "total_ram_gib": round(total_gib, 2),
        "warning": "This small synthetic starter dataset may not improve general capability. Evaluate unseen tasks before use.",
    })
    (output_dir / "training_report.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"LoRA adapter saved to: {adapter_dir}", flush=True)
    print("Merging LoRA into Qwen3 0.6B base weights for Ollama GGUF export...", flush=True)
    merged = trainer.model.merge_and_unload()
    merged.config.use_cache = True
    merged_dir.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(str(merged_dir), safe_serialization=True, max_shard_size="1GB")
    tokenizer.save_pretrained(merged_dir)
    print(f"Merged checkpoint saved to: {merged_dir}", flush=True)
    print("Next step: run training/export_to_ollama.py and pass --model-name studybuddy-cpu-trained.")


if __name__ == "__main__":
    main()
