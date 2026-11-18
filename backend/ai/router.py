from typing import AsyncGenerator, Dict, Any, List, Optional
from .ollama_client import OllamaClient
from .gemini_client import GeminiClient

class AIRouter:
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        ai_cfg = settings.get("ai", {})
        self.ollama = OllamaClient(
            endpoint=ai_cfg.get("ollama_endpoint", "http://localhost:11434"),
            default_model=ai_cfg.get("ollama_model", "llama3.2:3b")
        )
        self.gemini = GeminiClient(
            api_key=ai_cfg.get("gemini_api_key", ""),
            model=ai_cfg.get("gemini_model", "gemini-2.5-flash")
        )
        self.intelligent_routing = ai_cfg.get("intelligent_routing", True)

    def choose_provider(self, user_prompt: str) -> str:
        ai_cfg = self.settings.get("ai", {})
        primary = ai_cfg.get("primary_provider", "ollama")
        
        # If Gemini is not enabled or not configured, always use Ollama
        if not ai_cfg.get("gemini_enabled", False) or not self.gemini.is_configured():
            return "ollama"

        if not self.intelligent_routing:
            return primary

        # Smart routing heuristics
        lower = user_prompt.lower()
        complex_coding_keywords = ["refactor this entire", "complex architecture", "deep analysis", "optimize algorithm", "multi-threading bug"]
        if any(kw in lower for kw in complex_coding_keywords):
            return "gemini"
        
        return "ollama"

    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        forced_provider: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "")
                break

        provider = forced_provider or self.choose_provider(last_user_msg)
        
        # Format messages with system prompt at index 0
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        yield {"type": "provider_info", "provider": provider}

        if provider == "gemini" and self.gemini.is_configured():
            async for token in self.gemini.stream_chat(messages, system_instruction=system_prompt):
                yield {"type": "token", "token": token}
        else:
            # Fallback or primary: Ollama
            async for token in self.ollama.stream_chat(full_messages):
                yield {"type": "token", "token": token}
