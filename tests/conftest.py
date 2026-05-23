"""Common test fixtures and configurations for Fluentia."""

import pytest

from fluentia.config import AppConfig
from fluentia.config import BedrockProviderConfig
from fluentia.config import GoogleProviderConfig


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Override env vars so Pydantic BaseSettings uses code defaults, not .env overrides."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("FLUENTIA_DEFAULT_AGENT", "english_teacher")


@pytest.fixture
def google_config():
    """Fixture for a Google provider config with defaults."""
    return GoogleProviderConfig()


@pytest.fixture
def bedrock_config():
    """Fixture for a Bedrock provider config with defaults."""
    return BedrockProviderConfig()


@pytest.fixture
def app_config():
    """Fixture for the root app config with defaults."""
    return AppConfig()
