"""Factory for instantiating configured LLM Providers."""
from app.core.config import settings
from app.llm.base import BaseLLMProvider
from app.llm.gemini_provider import GeminiProvider
from app.llm.mock_provider import MockLLMProvider
from app.llm.openai_provider import OpenAIProvider


def get_llm_provider(provider_type: str = None) -> BaseLLMProvider:
    """Returns the requested or globally configured LLM provider."""
    ptype = (provider_type or settings.LLM_PROVIDER).lower()

    if ptype == "openai":
        return OpenAIProvider()
    elif ptype in ("gemini", "google"):
        return GeminiProvider()
    elif ptype == "mock":
        return MockLLMProvider()
    else:
        # Default fallback to deterministic mock provider
        return MockLLMProvider()
