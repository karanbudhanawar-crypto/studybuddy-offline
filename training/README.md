# StudyBuddy fine-tuning options

This folder now has two routes: a **CPU-only laptop route** and an optional **GPU route**. CPU training does not require a T4, but it is not fast; it can take hours and requires enough RAM and disk space.

## Recommended for a modest Windows laptop: CPU-only training
- `train_cpu_lora.py`: real LoRA fine-tuning of Qwen3 0.6B using CPU-only PyTorch, a low CPU thread limit, low process priority, and a RAM preflight check.
- `TRAIN_ON_LAPTOP_CPU.bat`: Windows batch workflow that creates a venv, installs CPU PyTorch and the required libraries, validates the dataset, fine-tunes locally, then builds/quantizes GGUF for Ollama.
- `requirements-cpu.txt`: dependencies for the CPU training route.
- `export_to_ollama.py`: Windows-aware CPU GGUF export and packaging script.
- `train.jsonl`: 81 synthetic starter examples.
- `eval.jsonl`: 8 separate examples for evaluation.
- `validate_dataset.py`: checks data structure, duplicate prompts, and exact train/eval prompt overlap.

### Requirements and trade-offs
- No GPU/T4 is required.
- This route deliberately trains the smaller **Qwen3 0.6B**, not Qwen3 1.7B, to reduce memory use. It may be faster at inference but has lower raw capacity.
- At least 8 GB system RAM is a bare minimum; 16 GB is safer. The script stops if available RAM is too low unless you deliberately override the guard.
- Keep the laptop plugged in and close other applications. It lowers its own process priority and uses two CPU threads by default, but it can still make the laptop feel slower.
- The training dataset is small; this is a starter fine-tune, not a guarantee of better general reasoning. Fine-tuning does not add tools, web access, or image understanding.

### Windows steps
1. Download/extract the GitHub repository and keep its folder structure.
2. Install Python 3.11–3.13, Git for Windows, CMake, and Visual Studio Build Tools 2022 with the **Desktop development with C++** workload. CMake and C++ tools are needed for the CPU GGUF export step.
3. Double-click `TRAIN_ON_LAPTOP_CPU.bat` inside the `training` directory.
4. The process creates `studybuddy-cpu-trained` and prints the exact Ollama import command. Confirm with `ollama run studybuddy-cpu-trained`.
5. Open StudyBuddy, press Ctrl+Shift+R, and choose **Laptop CPU — light model**. The website prefers `studybuddy-cpu-trained` when present, otherwise it uses `qwen3:0.6b` if you have it installed.

If model training completes but C++ export fails, the merged checkpoint is saved at `studybuddy-cpu-training-output/merged-f32`. Fix the compiler/CMake setup and run `training/export_to_ollama.py` again against that folder.

## Optional GPU route
`StudyBuddy_Advanced_Finetune.ipynb` and `train_lora.py` fine-tune Qwen3 1.7B and are intended for a CUDA GPU runtime. Use those only if you have access to an appropriate GPU; this is not required for CPU-only fine-tuning.

## Data quality and evaluation
The examples are synthetic and may contain limitations. Review outputs on unseen prompts for coding, math, CS subjects, multilingual explanations, and refusal/uncertainty. Do not place private chats, passwords, API keys, student records, or other sensitive data in the training set.