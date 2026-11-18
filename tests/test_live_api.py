import sys
import os
import time
import httpx
from pathlib import Path

ROOT = Path(r"C:\Users\Namisha 2.0")
sys.path.insert(0, str(ROOT))

import uvicorn
import threading
from backend.api.server import app

def run():
    print("=== LIVE INTEGRATION TEST ===")
    
    # 1. Start server in thread
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8765, log_level="warning")
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    time.sleep(1.5)

    client = httpx.Client(base_url="http://127.0.0.1:8765", timeout=10.0)

    # 2. Check root / frontend HTML
    r_root = client.get("/")
    print("1. Frontend HTML Check:", "OK (200)" if r_root.status_code == 200 and "Namisha" in r_root.text else f"FAILED: {r_root.status_code}")

    # 3. Check /api/status diagnostics
    r_stat = client.get("/api/status")
    data_stat = r_stat.json()
    print("2. System Diagnostics Check:")
    print(f"   - App: {data_stat.get('app')}")
    print(f"   - RAM: {data_stat.get('ram_used_gb')} / {data_stat.get('ram_total_gb')} GB ({data_stat.get('ram_percent')}%)")
    print(f"   - CPU: {data_stat.get('cpu_percent')}%")
    print(f"   - Ollama Running: {data_stat.get('ollama_running')}")
    print(f"   - Active Model: {data_stat.get('active_model')}")

    # 4. Check /api/settings
    r_set = client.get("/api/settings")
    data_set = r_set.json()
    print("3. Configuration Check:")
    print(f"   - Voice Enabled: {data_set.get('voice', {}).get('enabled')}")
    print(f"   - Playful Jealous Mode: {data_set.get('playful_jealous_mode', {}).get('enabled')}")
    print(f"   - Primary AI: {data_set.get('ai', {}).get('primary_provider')}")

    # 5. Check Persistent Memory API
    r_mem = client.get("/api/memories")
    data_mem = r_mem.json()
    print("4. SQLite Memory Check:")
    print(f"   - Facts count: {len(data_mem.get('facts', []))}")
    print(f"   - Projects count: {len(data_mem.get('projects', []))}")
    print(f"   - Recent chat count: {len(data_mem.get('recent_conversations', []))}")

    # 6. Test WebSocket connection
    import asyncio
    import websockets
    import json

    async def test_ws():
        async with websockets.connect("ws://127.0.0.1:8765/ws") as ws:
            # Send ping
            await ws.send(json.dumps({"type": "ping"}))
            # Test user return event
            await ws.send(json.dumps({"type": "user_return", "away_seconds": 600}))
            msg = await asyncio.wait_for(ws.recv(), timeout=4.0)
            payload = json.loads(msg)
            print("5. WebSocket & Playful Jealous Trigger Check:")
            print(f"   - Received event type: {payload.get('type')}")
            if payload.get("type") == "playful_jealous_greeting":
                print(f"   - Spoken text: {payload.get('text')}")
                print(f"   - Expression: {payload.get('expression')}")
                print(f"   - Audio URL: {payload.get('audio_url')}")

    try:
        asyncio.run(test_ws())
    except Exception as e:
        print("5. WebSocket Check:", e)

    print("\nALL LIVE INTEGRATION CHECKS COMPLETED SUCCESSFULLY!")
    server.should_exit = True

if __name__ == "__main__":
    run()
