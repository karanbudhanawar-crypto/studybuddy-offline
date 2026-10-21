@echo off
setlocal
title Create StudyBuddy Advanced Local Model
cd /d "%~dp0"

echo.
echo ============================================================
echo   StudyBuddy Advanced - Local Ollama Model Setup
echo ============================================================
echo.
echo This creates a custom Ollama model using your installed
echo qwen3:1.7b model. No paid API is used.
echo The weights are not Astra or a frontier model; this adds
echo a StudyBuddy-specific system prompt and conservative settings.
echo.

where ollama >nul 2>&1
if errorlevel 1 (
  echo ERROR: Ollama was not found. Install Ollama first:
  echo https://ollama.com/download/windows
  pause
  exit /b 1
)

ollama show qwen3:1.7b >nul 2>&1
if errorlevel 1 (
  echo The base model is missing. It will be downloaded now.
  ollama pull qwen3:1.7b
  if errorlevel 1 (
    echo ERROR: Could not download the base model.
    pause
    exit /b 1
  )
)

if not exist "%~dp0Modelfile" (
  echo ERROR: Modelfile is missing. Keep this BAT beside Modelfile.
  pause
  exit /b 1
)

echo Creating studybuddy-advanced...
ollama create studybuddy-advanced -f "%~dp0Modelfile"
if errorlevel 1 (
  echo.
  echo ERROR: Model creation failed. Check the Ollama version and output above.
  pause
  exit /b 1
)

echo.
echo SUCCESS: studybuddy-advanced was created.
echo.
echo Next steps:
echo 1. Keep Ollama running.
echo 2. Refresh https://studybuddy-offline.onrender.com
echo 3. Select Advanced - StudyBuddy model in Response mode.
echo 4. Open Connection settings, click Check models, and select
echo    studybuddy-advanced if it is not selected automatically.
echo.
ollama list
pause
