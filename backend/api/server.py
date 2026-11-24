import os
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import psutil

from ..memory.memory_manager import MemoryManager
from ..ai.router import AIRouter
from ..emotion.emotion_engine import EmotionEngine
from ..emotion.jealous_manager import JealousManager
from ..voice.tts_engine import TTSEngine
from ..voice.stt_engine import STTEngine
from ..screen.screen_capture import ScreenCapture
from ..coding.code_assistant import CodeAssistant

# Paths
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "settings.json"
PERSONALITY_PATH = Path(__file__).parent.parent.parent / "config" / "personality.json"
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"

# Helper to load/save JSON
def load_json(p: Path) -> Dict[str, Any]:
    if p.exists():
        with open(p, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {}

def save_json(p: Path, data: Dict[str, Any]):
    with open(p, "w", encoding="utf-8-sig") as f:
        json.dump(data, f, indent=2)

# ---------- FastAPI app ----------
app = FastAPI(title="Namisha Companion API", version="2.0.0")
router = app  # alias for backward‑compatible decorators

# CORS middleware (allow all for local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Initialise modules ----------
settings = load_json(CONFIG_PATH)
personality = load_json(PERSONALITY_PATH)

memory_mgr = MemoryManager()
ai_router = AIRouter(settings)
emotion_engine = EmotionEngine()
jealous_mgr = JealousManager(settings, personality.get("playful_jealous_dialogues", []))
tts_engine = TTSEngine(settings.get("voice", {}))
stt_engine = STTEngine()
screen_cap = ScreenCapture()
code_asst = CodeAssistant()

# Serve static frontend
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
async def root():
    return FileResponse(FRONTEND_DIR / "index.html")

# ----- API endpoints -----
@app.get("/api/status")
async def get_status():
    mem = psutil.virtual_memory()
    ollama_ok = await ai_router.ollama.is_running()
    return {
        "app": "Namisha 2.0",
        "cpu_percent": psutil.cpu_percent(interval=None),
        "ram_used_gb": round((mem.total - mem.available) / (1024**3), 2),
        "ram_total_gb": round(mem.total / (1024**3), 2),
        "ram_percent": mem.percent,
        "ollama_running": ollama_ok,
        "active_model": settings.get("ai", {}).get("ollama_model", "llama3.2:3b"),
        "lightweight_mode": settings.get("general", {}).get("lightweight_mode", False),
    }

@app.get("/api/settings")
async def get_settings():
    return settings

# Endpoint to generate TTS on‑the‑fly (used for goodbye line)
@router.post("/speak")
async def speak(payload: Dict[str, Any]):
    """Generate TTS for a given text and return the audio URL.
    Expected payload: {"text": "...", "expression": "sad"}
    """
    text = payload.get("text", "")
    expression = payload.get("expression", "neutral")
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    speech_res = await tts_engine.generate_speech(text)
    audio_url = None
    if speech_res:
        audio_url = f"/api/audio/{Path(speech_res['file_path']).name}"
    return {"status": "queued", "audio_url": audio_url, "expression": expression}

# Graceful shutdown endpoint – creates a flag file inspected by run_desktop.py
@router.post("/shutdown")
async def shutdown_endpoint():
    flag_path = Path(__file__).parent.parent.parent / "shutdown.flag"
    flag_path.write_text("1", encoding="utf-8")
    return {"status": "shutdown_requested"}

# Settings update – replaces the previous duplicate implementation
@router.post("/api/settings")
async def update_settings(new_settings: Dict[str, Any]):
    global settings
    settings.update(new_settings)
    save_json(CONFIG_PATH, settings)
    # Propagate changes to running engines
    tts_engine.set_muted(settings.get("voice", {}).get("muted", False))
    stt_engine.set_muted(settings.get("voice", {}).get("muted", False))
    return {"status": "updated", "settings": settings}

# Serve generated audio files
@app.get("/api/audio/{filename}")
async def serve_audio(filename: str):
    file_path = tts_engine.temp_dir / filename
    if file_path.exists():
        return FileResponse(file_path, media_type="audio/mpeg" if filename.endswith(".mp3") else "audio/wav")
    raise HTTPException(status_code=404, detail="Audio file not found")

@app.get("/api/memories")
async def get_memories():
    return {
        "facts": memory_mgr.get_all_facts(),
        "projects": memory_mgr.get_all_projects(),
        "recent_conversations": memory_mgr.get_recent_conversations(limit=20),
    }

@app.delete("/api/memories/reset")
async def reset_memories():
    memory_mgr.reset_all_memories()
    return {"status": "all memories reset"}

# ---------- WebSocket ----------
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    jealous_mgr.record_activity()
    try:
        while True:
            data_text = await websocket.receive_text()
            data = json.loads(data_text)
            event_type = data.get("type")

            # 1. User Return (Playful Jealous) ------------------------------------------------
            if event_type in ("window_focus", "user_return"):
                greeting = jealous_mgr.check_return_greeting()
                if greeting:
                    speech_res = await tts_engine.generate_speech(greeting["spoken_text"])
                    audio_url = f"/api/audio/{Path(speech_res['file_path']).name}" if speech_res else None
                    await websocket.send_json({
                        "type": "playful_jealous_greeting",
                        "text": greeting["spoken_text"],
                        "expression": greeting["expression"],
                        "audio_url": audio_url,
                        "voice_only": True,
                    })
                continue

            # 2. Ping ---------------------------------------------------------------------------
            if event_type == "ping":
                jealous_mgr.record_activity()
                continue

            # 3. Chat Message --------------------------------------------------------------------
            if event_type == "user_message":
                user_msg = data.get("message", "").strip()
                if not user_msg:
                    continue
                jealous_mgr.record_activity()
                memory_mgr.add_conversation_message("user", user_msg)

                # Gather recent history
                recent = memory_mgr.get_recent_conversations(limit=6)
                msgs_for_llm = [{"role": r["role"], "content": r["content"]} for r in recent]
                memory_ctx = memory_mgr.get_relevant_context()
                sys_prompt = personality.get("system_prompt", "")
                if memory_ctx:
                    sys_prompt += f"\n\nContext about the user:\n{memory_ctx}"

                # Notify UI we are thinking
                await websocket.send_json({"type": "expression_change", "expression": "thinking"})

                full_reply = ""
                async for chunk in ai_router.stream_response(msgs_for_llm, sys_prompt):
                    if chunk["type"] == "token":
                        token = chunk["token"]
                        full_reply += token
                        await websocket.send_json({"type": "token", "token": token})

                # Extract emotion tag and store conversation
                clean_reply, final_emotion = emotion_engine.extract_emotion_tag(full_reply)
                memory_mgr.add_conversation_message("assistant", clean_reply, emotion=final_emotion)

                # Send final expression
                await websocket.send_json({"type": "expression_change", "expression": final_emotion})

                # TTS response if enabled
                if settings.get("voice", {}).get("enabled", True):
                    speech_res = await tts_engine.generate_speech(clean_reply)
                    if speech_res:
                        audio_url = f"/api/audio/{Path(speech_res['file_path']).name}"
                        await websocket.send_json({
                            "type": "audio_response",
                            "audio_url": audio_url,
                            "expression": final_emotion,
                        })
                continue

            # 4. Voice STT request ---------------------------------------------------------------
            if event_type == "start_stt":
                await websocket.send_json({"type": "stt_status", "status": "listening"})
                await websocket.send_json({"type": "expression_change", "expression": "curious"})
                transcribed = await stt_engine.record_and_transcribe(max_duration=8.0)
                await websocket.send_json({"type": "stt_status", "status": "idle"})
                if transcribed:
                    await websocket.send_json({"type": "transcription_result", "text": transcribed})
                else:
                    await websocket.send_json({"type": "expression_change", "expression": "neutral"})
                continue

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
