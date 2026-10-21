# StudyBuddy Offline AI Chatbot

StudyBuddy is an installable student assistant for coding, homework, exam preparation, projects, and suggestions. It sends prompts directly from your browser to an AI model running locally through Ollama; this repository does not host a cloud AI model.

## Live app

https://studybuddy-offline.onrender.com

## Features
- Student-friendly chat UI with coding, homework, exam, and project prompts.
- Local chat history saved in the browser (reopen, rename, delete; stored on this device/browser).
- Response modes: general, coding/debugging, homework tutor, exam answer, advice, and creative writing.
- Attach text/code files to a question and export a conversation as Markdown.
- Copy individual messages and regenerate the last response.
- A fixed built-in HTML calculator and a Python/Tkinter calculator example that do not depend on AI-generated code.
- Copy generated code with one click.
- Stop a long-running local generation from the send button.
- Local model responses are capped to keep small CPU-only computers responsive.
- Live sandbox preview combines related HTML, CSS, and JavaScript blocks from one answer into a working demo; SVG snippets are also previewable. Python and desktop-language previews explain how to run code locally.
- Connects to Ollama running on the same device.
- Progressive Web App (PWA) install support and offline cache for the interface.
- No paid cloud AI API key required.

## Important architecture note
Render hosts the static interface, not the AI model. For AI replies, the device opening the website needs Ollama and a downloaded model. The UI can be cached and open offline after first load, but the browser still needs to reach local Ollama for replies. To run fully offline, keep the interface cached/served locally and run Ollama on that same device.

## Windows setup
1. Install Ollama: https://ollama.com/download/windows
2. Open Command Prompt and download a small model: `ollama pull qwen2.5:1.5b-instruct`
3. Start Ollama.
4. Open StudyBuddy, select **Connection settings**, keep address `http://127.0.0.1:11434`, then click **Check models**.
5. If the browser blocks requests from the hosted Render website, configure Ollama's allowed origins to include only the exact site origin `https://studybuddy-offline.onrender.com`, then fully restart Ollama. Do not use `*` for allowed origins. Browser local-network/CORS behavior may vary by browser/version.

## Render deployment
- Type: Static Site
- Branch: `main`
- Build command: `echo 'No build required'`
- Publish directory: `.`
- Auto deploy: enabled

The site is automatically redeployed when new commits are pushed to `main`.

## Run locally
From the project folder run `python -m http.server 8000`, then open http://localhost:8000. For local Ollama calls, use `http://127.0.0.1:11434` in Connection settings.

## Privacy
Prompts are sent from your browser to the Ollama endpoint configured in the app. There is no server-side model or cloud database. Conversations remain in page memory for the current session; the chosen endpoint and model are stored in browser local storage.

## Project files
- `index.html` — app, styles, and chat logic
- `manifest.webmanifest` — installable PWA settings
- `service-worker.js` — offline cache for the interface
- `icon.svg` — app icon

## Python/Tkinter calculator example

The app includes a built-in Python calculator source example under **Python calculator**. Its Preview button displays an interactive browser-based equivalent; the Tkinter program itself runs locally on Windows with Python installed.

```bat
python examples/python_calculator.py
```

A standalone source file is available in `examples/python_calculator.py`.


### Use the built-in Python example in the website
Open StudyBuddy and click **Python calculator**. The source appears in a Python code block with Copy code and Preview controls. The preview is an interactive browser equivalent; it does not execute Python in the browser.
