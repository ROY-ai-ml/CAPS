"""Pytest configuration ensuring deterministic test suite execution."""
import pytest
from app.core.config import settings


@pytest.fixture(autouse=True, scope="session")
def enforce_mock_provider_for_tests():
    """Guarantees automated test suites use deterministic mock provider."""
    original_provider = settings.LLM_PROVIDER
    settings.LLM_PROVIDER = "mock"
    yield
    settings.LLM_PROVIDER = original_provider
