import sys
import os
import time
import threading
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
import webview
from backend.api.server import app

SERVER_PORT = 8765

def run_api_server():
    """Runs FastAPI in background thread with clean exit signal handling."""
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=SERVER_PORT,
        log_level="error",
        access_log=False
    )
    server = uvicorn.Server(config)
    server.run()

def on_closed():
    """Cleanly terminates background processes on window close."""
    print("Namisha desktop window closed. Cleaning up all background resources...")
    os._exit(0)

def main():
    # 1. Start backend thread
    server_thread = threading.Thread(target=run_api_server, daemon=True)
    server_thread.start()
    time.sleep(1.2)  # Wait for port to open

    # 2. Window sizing and right-side positioning
    window_w = 360
    window_h = 620

    # Get primary screen dimensions if available
    try:
        screens = webview.screens
        if screens:
            primary = screens[0]
            start_x = max(0, primary.width - window_w - 24)
            start_y = max(0, (primary.height - window_h) // 2)
        else:
            start_x = 1100
            start_y = 100
    except Exception:
        start_x = 1100
        start_y = 100

    # 3. Create Edge WebView2 Transparent Desktop Window
    window = webview.create_window(
        title="Namisha",
        url=f"http://127.0.0.1:{SERVER_PORT}/",
        width=window_w,
        height=window_h,
        x=start_x,
        y=start_y,
        resizable=False,
        frameless=True,
        easy_drag=True,
        on_top=True,
        transparent=True,
        background_color="#00000000"
    )

    window.events.closed += on_closed
    webview.start(debug=False)

if __name__ == "__main__":
    main()
