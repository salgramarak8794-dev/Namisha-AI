# Namisha 2.0 — Local AI Anime Desktop Companion

Namisha is a friendly, intelligent anime desktop companion designed for Windows. She lives on the right side of your desktop, interacts via voice and text, understands your emotional state, assists with coding workflows, and operates primarily on a local AI engine.

---

## Key Features

- **2D Rigged Anime Avatar:** Responsive canvas character featuring 15 distinct facial expressions, natural blinking, eye gaze tracking, and audio amplitude lip-synchronization.
- **Low-Resource Architecture:** Optimized specifically for standard laptop hardware (such as dual-core AMD Ryzen processors with 8 GB RAM). Runs via native Windows Edge WebView2 with a runtime footprint of ~45 MB RAM.
- **Dual AI Engine:** Connects to local Ollama (`llama3.2:3b`) for private, offline interactions, with optional Google Gemini cloud routing for deep architectural reasoning.
- **Voice-First Playful Interaction:** Includes an optional affectionate "Playful Jealous Mode" triggered with spoken voice and facial expressions upon returning from away events (with cooldown timers and non-intrusive boundaries).
- **Persistent Memory:** Local SQLite storage for user preferences, ongoing coding projects, and conversational context with full inspection and reset controls.
- **Screen Awareness & Coding Support:** On-demand, permission-gated screen capture and code assistance with workspace boundary enforcement.
- **Clean Process Lifecycle:** Zero background persistence. Double-click to launch, and clean shutdown on exit with no lingering background tasks.

---

## Project Structure

```text
Namisha 2.0/
├── backend/
│   ├── ai/          # Ollama and Gemini clients, smart router
│   ├── api/         # FastAPI server and WebSocket IPC bridge
│   ├── coding/      # Workspace scanner and traceback analyzer
│   ├── emotion/     # Emotion classifier and playful jealousy manager
│   ├── memory/      # SQLite persistent storage and context builder
│   ├── screen/      # Permission-gated screen capture (MSS)
│   ├── security/    # Permissions and boundary checks
│   └── voice/       # Edge-TTS / SAPI5 speech and Faster-Whisper STT
├── config/
│   ├── personality.json  # Editable character prompt and dialogues
│   └── settings.json     # Application settings and feature toggles
├── database/        # Local SQLite database (namisha_memory.db)
├── frontend/
│   ├── css/         # Dark violet translucent theme and floating HUD
│   ├── js/          # 2D character rig and WebSocket client
│   └── index.html   # Desktop viewport
├── scripts/         # Utility and setup scripts
├── tests/           # Component unit test suite
├── run_desktop.py   # Desktop application launcher
├── run.bat          # Development launcher with console output
├── start.bat        # Background launcher
└── stop.bat         # Clean shutdown script
```

---

## Quick Start

### 1. Requirements
- Windows 10 / 11 (64-bit)
- Python 3.10+
- [Ollama](https://ollama.com/) running locally with `llama3.2:3b`:
  ```bash
  ollama run llama3.2:3b
  ```

### 2. Launching Namisha
- **Start Namisha:** Double-click `run.bat` (or `start.bat`)
- **Stop Namisha:** Double-click `stop.bat` (or close the desktop window)

### 3. Running Automated Tests
```powershell
python tests/test_components.py
```
