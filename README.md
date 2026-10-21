# StudyBuddy Offline AI Chatbot

StudyBuddy is a browser-based student assistant that uses an AI model running locally through Ollama. The site is hosted on Render; the model and prompts run on the user's computer.

## Live app
https://studybuddy-offline.onrender.com

## Features
- Local chat history: reopen, rename, and delete conversations in this browser.
- Response modes: general, Advanced, coding/debugging, homework, exam answers, advice, and creative writing.
- Attach small text/code files and export chats as Markdown.
- Copy messages and generated code; retry an answer or stop a long generation.
- Sandboxed previews for HTML, CSS, JavaScript, and SVG.
- Built-in working calculator and standalone Python/Tkinter calculator example.
- No paid AI API key is required.

## Important: what "StudyBuddy Advanced" means
The **Advanced** mode is a custom local profile based on Qwen3 1.7B. It applies StudyBuddy-specific instructions and conservative generation settings. It is **not Astra**, does not use Astra weights, and cannot gain frontier-model capabilities from prompts alone. Answer quality still depends on the underlying model, hardware, and task.

## Create the custom local model on Windows
1. Download this repository using GitHub's **Code → Download ZIP** and extract it. Keep `Modelfile` and `CREATE_STUDYBUDDY_ADVANCED.bat` in the same extracted root folder.
2. Ensure Ollama is installed and running: https://ollama.com/download/windows
3. Double-click `CREATE_STUDYBUDDY_ADVANCED.bat`. It checks for the base model `qwen3:1.7b` and downloads it if missing, then creates the custom tag `studybuddy-advanced`.
4. Open StudyBuddy, hard-refresh with Ctrl+Shift+R, select **Advanced — StudyBuddy model** in the response-mode picker, then open **Connection settings → Check models** if needed.
5. Confirm `studybuddy-advanced` is selected as the model. If it is not installed, Advanced instructions still work with the currently selected local model.

The custom tag reuses Qwen3 1.7B weights and adds a StudyBuddy system prompt and runtime defaults; it does not download an Astra model or add new learned knowledge. Qwen3 1.7B is about 1.4 GB for the Q4_K_M model file; actual memory use is higher while it runs. This text model cannot interpret images.

### Optional image understanding
For offline image questions, you can separately install a vision model with `ollama pull gemma3:4b` (about 3.3 GB on disk) and select it under **Connection settings**. It may be too slow or memory-hungry on a low-RAM laptop, so this is optional. Image uploads only work with a vision-capable model.

## Run the standalone Python calculator
The file `examples/python_calculator.py` is a complete Tkinter desktop calculator. With Python installed, run from the repository folder:
```bat
python examples/python_calculator.py
```
The website's Preview is an interactive browser equivalent, not a browser execution of Python.

## Offline and privacy notes
- The interface can be cached after its first visit; AI responses need Ollama running on the same computer and a browser permission setup that allows the site to reach localhost.
- Chat history, selected mode, model, and endpoint are stored in the browser's local storage. Text/code attachments are sent to the selected local Ollama endpoint when submitted.
- There is no server-side model or cloud database in this static site.
- Do not put passwords, API keys, or other secrets in prompts or attachments.

## Render deployment
- Static Site, branch `main`
- Build command: `echo 'No build required'`
- Publish directory: `.`
- Auto-deploy is enabled for commits to `main`.

## Repository files
- `index.html` — app, UI, chat logic, code previews and calculator demos
- `Modelfile` — configuration for the custom StudyBuddy model
- `CREATE_STUDYBUDDY_ADVANCED.bat` — Windows model creation helper
- `examples/python_calculator.py` — standalone Python/Tkinter calculator
- `manifest.webmanifest`, `service-worker.js`, `icon.svg` — installable PWA/offline shell


## Advanced local model
- The Advanced mode uses the custom Ollama model tag `studybuddy-advanced` when installed.
- `Modelfile` is based on `qwen3:1.7b`; `CREATE_STUDYBUDDY_ADVANCED.bat` checks/pulls that base and creates the custom tag.
- Qwen3 1.7B is a small text model, not Astra and not a replica of proprietary weights. The custom instructions improve response format but cannot create capabilities or accuracy not present in the base model.
- Qwen3 1.7B Q4_K_M is around 1.4 GB on disk; runtime memory use is higher and CPU inference may be slow on low-RAM systems.

## Optional local image understanding
The app can submit PNG/JPG/WEBP images to compatible local vision models. The default Qwen3 text model cannot see images. For a vision-capable model, run `ollama pull gemma3:4b` and select `gemma3:4b` in Connection settings. This image model is around 3.3 GB on disk and may exceed practical memory for a low-RAM laptop, so image support is optional. Image bytes are sent to the Ollama endpoint you selected; images aren't stored in saved chat history.



## Fine-tune StudyBuddy Advanced

A starter LoRA fine-tuning pipeline lives in [`training/`](https://github.com/karanbudhanawar-crypto/studybuddy-offline/tree/main/training). It includes 81 synthetic supervised examples, a separate held-out evaluation set, training and GGUF export scripts, and a Colab notebook. The actual fine-tuning still needs to be run on a CUDA GPU; it has not been run by this repository update.

Start here: [Open the fine-tuning notebook in Google Colab](https://colab.research.google.com/github/karanbudhanawar-crypto/studybuddy-offline/blob/main/training/StudyBuddy_Advanced_Finetune.ipynb).
