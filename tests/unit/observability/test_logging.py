"""Tests for structured logging configuration."""

import logging
from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

from fluentia.config import AppConfig
from fluentia.observability.logging import HealthCheckFilter
from fluentia.observability.logging import configure_logging
from fluentia.observability.logging import log_config_summary
from fluentia.observability.logging import mask_sensitive_values


class TestHealthCheckFilter:
    """Tests for HealthCheckFilter."""

    def test_allows_normal_log_entries(self):
        """Test that non-health-check entries pass through."""
        log_filter: HealthCheckFilter = HealthCheckFilter()
        record: logging.LogRecord = logging.LogRecord(
            name="uvicorn.access",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="GET /api/agents 200",
            args=(),
            exc_info=None,
        )
        assert log_filter.filter(record) is True

    def test_filters_health_endpoint(self):
        """Test that /health entries are filtered."""
        log_filter: HealthCheckFilter = HealthCheckFilter()
        record: logging.LogRecord = logging.LogRecord(
            name="uvicorn.access",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="GET /health 200",
            args=(),
            exc_info=None,
        )
        assert log_filter.filter(record) is False

    def test_filters_ready_endpoint(self):
        """Test that /ready entries are filtered."""
        log_filter: HealthCheckFilter = HealthCheckFilter()
        record: logging.LogRecord = logging.LogRecord(
            name="uvicorn.access",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="GET /ready 200",
            args=(),
            exc_info=None,
        )
        assert log_filter.filter(record) is False


class TestMaskSensitiveValues:
    """Tests for mask_sensitive_values structlog processor."""

    def test_redacts_api_key(self):
        """Test that API key values are redacted."""
        event_dict: dict[str, Any] = {"api_key": "super-secret-key", "message": "hello"}
        result: Any = mask_sensitive_values(None, "", event_dict)
        assert result["api_key"] == "***REDACTED***"
        assert result["message"] == "hello"

    def test_redacts_secret(self):
        """Test that secret values are redacted."""
        event_dict: dict[str, Any] = {"aws_secret": "my-secret"}
        result: Any = mask_sensitive_values(None, "", event_dict)
        assert result["aws_secret"] == "***REDACTED***"

    def test_redacts_token(self):
        """Test that token values are redacted."""
        event_dict: dict[str, Any] = {"session_token": "abc123"}
        result: Any = mask_sensitive_values(None, "", event_dict)
        assert result["session_token"] == "***REDACTED***"

    def test_redacts_password(self):
        """Test that password values are redacted."""
        event_dict: dict[str, Any] = {"db_password": "pass123"}
        result: Any = mask_sensitive_values(None, "", event_dict)
        assert result["db_password"] == "***REDACTED***"

    def test_redacts_credential(self):
        """Test that credential values are redacted."""
        event_dict: dict[str, Any] = {"aws_credential": "cred123"}
        result: Any = mask_sensitive_values(None, "", event_dict)
        assert result["aws_credential"] == "***REDACTED***"

    def test_leaves_non_sensitive_untouched(self):
        """Test that non-sensitive values are not redacted."""
        event_dict: dict[str, Any] = {"event": "session_start", "user_id": "u1"}
        result: Any = mask_sensitive_values(None, "", event_dict)
        assert result["event"] == "session_start"
        assert result["user_id"] == "u1"

    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        event_dict: dict[str, Any] = {"API_KEY": "secret", "Api_Token": "tok"}
        result: Any = mask_sensitive_values(None, "", event_dict)
        assert result["API_KEY"] == "***REDACTED***"
        assert result["Api_Token"] == "***REDACTED***"


class TestConfigureLogging:
    """Tests for configure_logging function."""

    def test_configure_logging_does_not_raise(self):
        """Test that configure_logging completes without error."""
        configure_logging("DEBUG")

    def test_configure_logging_default_level(self):
        """Test that configure_logging works with default level."""
        configure_logging()

    def test_configure_logging_invalid_level_falls_back(self):
        """Test that an invalid level falls back to INFO."""
        configure_logging("INVALID_LEVEL")

    def test_health_check_filter_added_to_uvicorn(self):
        """Test that HealthCheckFilter is added to uvicorn access logger."""
        configure_logging("INFO")
        uvicorn_logger: logging.Logger = logging.getLogger("uvicorn.access")
        filter_types: list[type] = [type(f) for f in uvicorn_logger.filters]
        assert HealthCheckFilter in filter_types

    def test_noisy_loggers_capped(self):
        """Test that third-party loggers are set to WARNING."""
        configure_logging("DEBUG")
        for name in ("websockets", "google_adk", "google_genai", "google.adk", "google.genai"):
            assert logging.getLogger(name).level == logging.WARNING


class TestLogConfigSummary:
    """Tests for log_config_summary function."""

    def test_log_config_summary_does_not_raise(self):
        """Test that log_config_summary completes without error."""
        config: AppConfig = AppConfig()
        configure_logging("INFO")
        log_config_summary(config)

    @patch("fluentia.observability.logging.structlog.get_logger")
    def test_log_config_summary_redacts_sensitive(self, mock_get_logger: MagicMock):
        """Test that sensitive config fields are redacted."""
        mock_logger: MagicMock = MagicMock()
        mock_get_logger.return_value = mock_logger

        config: AppConfig = AppConfig()
        log_config_summary(config)

        mock_logger.info.assert_called_once()
        call_kwargs: dict[str, Any] = mock_logger.info.call_args[1]
        summary: dict[str, Any] = call_kwargs["config"]

        # Google nested config should have api_key redacted
        assert summary["google"]["api_key"] == "***REDACTED***"

    @patch("fluentia.observability.logging.structlog.get_logger")
    def test_log_config_summary_includes_non_sensitive(self, mock_get_logger: MagicMock):
        """Test that non-sensitive config fields are included."""
        mock_logger: MagicMock = MagicMock()
        mock_get_logger.return_value = mock_logger

        config: AppConfig = AppConfig()
        log_config_summary(config)

        call_kwargs: dict[str, Any] = mock_logger.info.call_args[1]
        summary: dict[str, Any] = call_kwargs["config"]

        assert summary["port"] == "8000"
        assert summary["log_level"] == "INFO"
        assert summary["default_provider"] == "google"
