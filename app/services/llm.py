import httpx
import json
from typing import AsyncGenerator
from app.core.config import get_settings
from app.core.exceptions import LLMError
from app.core.logging import logger

settings = get_settings()


class OllamaService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT

    async def is_healthy(self) -> bool:
        """Ping Ollama to check if it's reachable."""
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(self.base_url, timeout=3)
                return r.status_code == 200
        except Exception:
            return False

    async def generate(self, prompt: str) -> str:
        """Single-shot generation — returns the full response as a string."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        logger.debug(f"Sending prompt to Ollama (model={self.model})")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                r.raise_for_status()
                return r.json()["response"]
        except httpx.HTTPStatusError as e:
            raise LLMError(f"HTTP {e.response.status_code}: {e.response.text}")
        except httpx.TimeoutException:
            raise LLMError(f"Request timed out after {self.timeout}s")
        except Exception as e:
            raise LLMError(str(e))

    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Streaming generation — yields text chunks as they arrive from Ollama."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
        }
        logger.debug(f"Starting streaming request to Ollama (model={self.model})")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=payload,
                ) as r:
                    r.raise_for_status()
                    async for line in r.aiter_lines():
                        if line:
                            chunk = json.loads(line)
                            yield chunk.get("response", "")
                            if chunk.get("done"):
                                break
        except httpx.TimeoutException:
            raise LLMError(f"Streaming timed out after {self.timeout}s")
        except Exception as e:
            raise LLMError(str(e))


# Singleton instance
ollama_service = OllamaService()