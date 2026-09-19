"""Abstract Base Class for LLM Providers."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class LLMResponse:
    """Standardized response schema from LLM invocation."""
    def __init__(
        self,
        content: str,
        structured: Optional[Dict[str, Any]] = None,
        model: str = "",
        tokens_used: int = 0,
        raw: Any = None,
    ):
        self.content = content
        self.structured = structured or {}
        self.model = model
        self.tokens_used = tokens_used
        self.raw = raw


class BaseLLMProvider(ABC):
    """Interface for pluggable model backends."""

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Generates text completion."""
        pass

    @abstractmethod
    async def complete_structured(
        self,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> LLMResponse:
        """Generates validated structured JSON response."""
        pass
