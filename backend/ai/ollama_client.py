import json
import httpx
from typing import AsyncGenerator, Dict, Any, List, Optional

class OllamaClient:
    def __init__(self, endpoint: str = "http://localhost:11434", default_model: str = "llama3.2:3b"):
        self.endpoint = endpoint.rstrip("/")
        self.default_model = default_model

    async def is_running(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.endpoint}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> List[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.endpoint}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    return data.get("models", [])
        except Exception:
            pass
        return []

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        chosen_model = model or self.default_model
        payload = {
            "model": chosen_model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 256  # Keeps replies conversational & fast for voice
            }
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", f"{self.endpoint}/api/chat", json=payload) as response:
                if response.status_code != 200:
                    yield f"Error: Ollama returned status {response.status_code}"
                    return
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        msg = chunk.get("message", {}).get("content", "")
                        if msg:
                            yield msg
                    except json.JSONDecodeError:
                        continue
