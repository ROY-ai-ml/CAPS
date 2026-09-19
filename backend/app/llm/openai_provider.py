"""OpenAI LLM Provider Implementation."""
import json
from typing import Any, Dict, Optional
import httpx

from app.core.config import settings
from app.llm.base import BaseLLMProvider, LLMResponse


class OpenAIProvider(BaseLLMProvider):
    """Integrates OpenAI API using httpx."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY or settings.LLM_API_KEY
        self.model = model or settings.LLM_MODEL or "gpt-4o"
        self.base_url = "https://api.openai.com/v1"

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            tokens = data.get("usage", {}).get("total_tokens", 0)
            return LLMResponse(content=content, model=self.model, tokens_used=tokens, raw=data)

    async def complete_structured(
        self,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> LLMResponse:
        system = (system_prompt or "") + "\nYou MUST respond strictly in valid JSON format."
        res = await self.complete(prompt, system_prompt=system, temperature=temperature)
        try:
            # Strip potential ```json markdown wrapper
            clean_text = res.content.strip()
            if clean_text.startswith("```"):
                clean_text = clean_text.split("\n", 1)[-1]
                if clean_text.endswith("```"):
                    clean_text = clean_text.rsplit("```", 1)[0]
            structured = json.loads(clean_text.strip())
            res.structured = structured
        except Exception:
            res.structured = {"raw_output": res.content}
        return res
