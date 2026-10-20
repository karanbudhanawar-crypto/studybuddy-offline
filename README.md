# StudyBuddy Offline AI Chatbot

StudyBuddy is an installable student assistant for coding help, homework, exam preparation, projects, and suggestions. It uses an AI model running locally through Ollama; this repository hosts only the browser interface.

## Features
- Student-friendly chat UI with coding, homework, and exam prompts.
- Connects to Ollama running on the same device.
- Progressive Web App (PWA) files and offline cache for the interface.
- No paid cloud AI API key required.

## Important architecture note
Render hosts the static interface, not the AI model. For replies, the device opening the app needs Ollama and a downloaded model. To run the interface and model fully offline, serve it locally instead of using the hosted site.

## Windows setup
1. Install Ollama: https://ollama.com/download/windows
2. Download a model in Command Prompt: `ollama pull qwen2.5:1.5b-instruct`
3. Start Ollama.
4. Open StudyBuddy and click **Connection settings**. Keep address `http://localhost:11434`, then click **Check connection / models**.
5. If the browser blocks a request from your Render website, configure Ollama's allowed origins to include the exact `https://YOUR-SITE.onrender.com` URL (avoid `*`) and restart Ollama. Browser local-network/CORS behavior may vary.

## Deploy to Render
Create a **Static Site** from this GitHub repository, branch `main`, build command `echo 'No build required'`, publish directory `.`. Render will serve `index.html` from the repository root over HTTPS.

## Run locally
From the folder, run `python -m http.server 8000` and open `http://localhost:8000`.

## Privacy
Prompts are sent directly from the browser to the selected local Ollama endpoint. This project has no server-side model or cloud database. Chats stay in page memory for the current session; the endpoint and selected model are stored in browser local storage.

## Files
- `index.html` — app interface
- `style.css` — layout and design
- `app.js` — chat logic and Ollama connection
- `manifest.webmanifest`, `service-worker.js`, `icon.svg` — installable PWA and offline shell
