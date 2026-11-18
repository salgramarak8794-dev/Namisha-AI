import os
from typing import AsyncGenerator, Dict, Any, List, Optional

class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = model
        self.client = None
        if self.api_key:
            self._init_client()

    def _init_client(self):
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            print(f"Failed to initialize Gemini client: {e}")
            self.client = None

    def is_configured(self) -> bool:
        return bool(self.api_key and self.client)

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        if not self.is_configured():
            yield "Gemini API key is not configured. Please check your settings."
            return

        try:
            # Format prompt from history
            prompt_parts = []
            for m in messages:
                role = "User" if m.get("role") == "user" else "Namisha"
                prompt_parts.append(f"{role}: {m.get('content', '')}")
            full_prompt = "\n".join(prompt_parts)

            response = self.client.models.generate_content_stream(
                model=self.model,
                contents=full_prompt,
                config={"system_instruction": system_instruction} if system_instruction else None
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"Gemini Error: {str(e)}"
