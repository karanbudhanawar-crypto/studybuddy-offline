# StudyBuddy fine-tuning starter

This directory contains a real supervised fine-tuning (SFT) workflow for a **LoRA adapter** on `Qwen/Qwen3-1.7B`. It is intended for a CUDA GPU notebook such as Google Colab when a GPU is available. It will not train usefully on the user's Ryzen/AMD low-VRAM laptop; use that laptop to run the quantized model after training.

## What's included
- `validate_dataset.py`: checks JSONL format, duplicate prompts, and exact prompt overlap between training/evaluation files.
- `train.jsonl`: curated synthetic starter examples for coding, computer science homework, exam answers, problem solving, and honest uncertainty.
- `eval.jsonl`: held-out examples used for evaluation loss; they are not included in training.
- `train_lora.py`: LoRA supervised fine-tuning using Transformers, TRL, Datasets, and PEFT.
- `export_to_ollama.py`: merges weights into the base checkpoint, converts the model with llama.cpp, quantizes it to Q4_K_M, and creates a Windows import ZIP.
- `StudyBuddy_Advanced_Finetune.ipynb`: click-open notebook flow for a CUDA GPU runtime.

## Recommended path
1. Open [StudyBuddy Advanced Fine-Tuning in Google Colab](https://colab.research.google.com/github/karanbudhanawar-crypto/studybuddy-offline/blob/main/training/StudyBuddy_Advanced_Finetune.ipynb). If direct opening does not work, download the notebook from [GitHub](https://github.com/karanbudhanawar-crypto/studybuddy-offline/blob/main/training/StudyBuddy_Advanced_Finetune.ipynb) and upload it to Colab.
2. In Colab choose `Runtime → Change runtime type → T4 GPU` if offered. Free compute availability and limits vary; a GPU is not guaranteed.
3. Run cells in order. The script trains 3 epochs using max sequence length 1024, saves a LoRA adapter, evaluates on `eval.jsonl`, and merges the adapter back into the original-precision model.
4. Download `studybuddy-advanced-import.zip` from the last cell.
5. On Windows, extract the ZIP and run this command in the extracted folder:
   ```bat
   ollama create studybuddy-advanced-trained -f Modelfile.trained
   ```
6. Test the resulting model with `ollama run studybuddy-advanced-trained`. In the StudyBuddy website, hard refresh and select **Advanced — StudyBuddy model**. When the trained tag is detected, Advanced mode prefers it.

## Optional manual commands
From a CUDA GPU runtime:
```bash
pip install -r training/requirements.txt
python training/train_lora.py --train-file training/train.jsonl --eval-file training/eval.jsonl --output-dir /content/studybuddy-training-output --epochs 3 --max-length 1024
python training/export_to_ollama.py --merged-model /content/studybuddy-training-output/merged-fp16 --output-dir /content/studybuddy-training-output/ollama-output
```

## Important limitations
- The current starter dataset contains synthetic examples made for this project. It is a useful pipeline test, not a large corpus, and cannot guarantee a meaningful quality gain. Review and expand it with accurate, permissioned examples for the tasks you care about.
- Evaluate with unseen coding, math, CS, and instruction-following prompts before replacing your previous model. An improved evaluation loss does not guarantee better answers.
- Fine-tuning changes the model's weights. It does not add web search, run arbitrary programs, or provide vision unless the underlying model supports it.
- This does not recreate Astra or any proprietary model. It fine-tunes the openly available Qwen3 base model with a StudyBuddy dataset and adapter.
- The export requires several GB of temporary storage and downloading the GGUF ZIP can take time. Keep enough disk space and do not interrupt the conversion.
- Only upload data you have rights to use. Do not include private chats, passwords, API keys, student records, or other personal data in training files.
