@echo off
setlocal
title StudyBuddy CPU Fine-Tune (Qwen3 0.6B)
cd /d "%~dp0"
set OMP_NUM_THREADS=2
set MKL_NUM_THREADS=2
set TOKENIZERS_PARALLELISM=false

echo.
echo ==========================================================
echo   StudyBuddy CPU-only LoRA fine-tuning
echo ==========================================================
echo.
echo No T4/GPU is required. This uses Qwen3 0.6B and CPU only.
echo Training may take hours and will still use RAM and CPU.
echo Keep the laptop plugged in and close other applications.
echo The process uses low priority where supported.
echo.
echo Recommended: at least 8 GB RAM total, preferably 16 GB,
echo and at least 10 GB free disk space for model conversion.
echo.
choice /C YN /M "Continue with CPU-only fine-tuning"
if errorlevel 2 exit /b 0

where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python was not found. Install Python 3.11 or 3.12 from python.org, then retry.
  pause
  exit /b 1
)
where git >nul 2>&1
if errorlevel 1 (
  echo ERROR: Git for Windows is required for the GGUF conversion step.
  echo Install it from https://git-scm.com/download/win
  pause
  exit /b 1
)
where cmake >nul 2>&1
if errorlevel 1 (
  echo ERROR: CMake is required. Install CMake and Visual Studio Build Tools 2022
  echo with the "Desktop development with C++" workload.
  echo Then restart Command Prompt and retry.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  if errorlevel 1 (
    echo ERROR: Could not create Python virtual environment.
    pause
    exit /b 1
  )
)
set VENV_PY=%CD%\.venv\Scripts\python.exe

"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 goto :failed
"%VENV_PY%" -m pip install --index-url https://download.pytorch.org/whl/cpu torch
if errorlevel 1 goto :failed
"%VENV_PY%" -m pip install -r training\requirements-cpu.txt
if errorlevel 1 goto :failed

"%VENV_PY%" training\validate_dataset.py
if errorlevel 1 goto :failed

echo.
echo Starting fine-tuning. Do not close this window.
"%VENV_PY%" training\train_cpu_lora.py --base-model Qwen/Qwen3-0.6B --train-file training\train.jsonl --eval-file training\eval.jsonl --output-dir studybuddy-cpu-training-output --epochs 1 --max-length 256 --cpu-threads 2
if errorlevel 1 goto :failed

echo.
echo Fine-tuning complete. Building a quantized model for Ollama.
echo This step needs CMake and Visual Studio C++ Build Tools.
"%VENV_PY%" training\export_to_ollama.py --merged-model studybuddy-cpu-training-output\merged-f32 --output-dir studybuddy-cpu-training-output\ollama-output --llama-cpp-dir tools\llama.cpp --model-name studybuddy-cpu-trained
if errorlevel 1 goto :failed

echo.
echo SUCCESS. Install your CPU-trained model with:
echo cd studybuddy-cpu-training-output\ollama-output
echo ollama create studybuddy-cpu-trained -f Modelfile.trained
echo ollama run studybuddy-cpu-trained
echo Then open StudyBuddy, refresh, and choose Laptop CPU (light) mode.
pause
exit /b 0

:failed
echo.
echo The step failed. Read the error above. No existing Ollama model was deleted.
pause
exit /b 1
