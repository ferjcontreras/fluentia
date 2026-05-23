"""Tests for health check endpoints."""

from fluentia.config import AppConfig
from fluentia.config import GoogleProviderConfig
from fluentia.observability.health import get_health
from fluentia.observability.health import get_readiness


class TestHealth:
    def test_get_health(self):
        """Test liveness probe returns ok status."""
        result = get_health()
        assert result["status"] == "ok"

    def test_get_health_includes_version(self):
        """Test liveness probe includes version."""
        result = get_health()
        assert result["version"] == "1.0.0"

    def test_get_health_includes_uptime(self):
        """Test liveness probe includes uptime."""
        result = get_health()
        assert "uptime_seconds" in result
        assert result["uptime_seconds"] >= 0


class TestReadiness:
    def test_get_readiness_default(self, app_config):
        """Test readiness probe with default config."""
        result = get_readiness(app_config)
        assert result["status"] == "ready"
        assert "providers" in result

    def test_google_not_configured_without_key(self, app_config):
        """Test Google shows not_configured without API key."""
        result = get_readiness(app_config)
        assert result["providers"]["google"] == "not_configured"

    def test_google_available_with_key(self):
        """Test Google shows available when API key is set."""
        config: AppConfig = AppConfig(google=GoogleProviderConfig(api_key="test-key"))
        result = get_readiness(config)
        assert result["providers"]["google"] == "available"

    def test_bedrock_always_available(self, app_config):
        """Test Bedrock is always reported as available."""
        result = get_readiness(app_config)
        assert result["providers"]["bedrock"] == "available"
