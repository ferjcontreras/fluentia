"""Tests for metrics collection."""

from fluentia.observability.metrics import LoggingMetricsCollector


class TestLoggingMetricsCollector:
    def test_session_started_does_not_raise(self):
        collector = LoggingMetricsCollector()
        collector.session_started("google", "english_teacher")

    def test_session_ended_does_not_raise(self):
        collector = LoggingMetricsCollector()
        collector.session_ended("google", "english_teacher", 42.0)

    def test_session_error_does_not_raise(self):
        collector = LoggingMetricsCollector()
        collector.session_error("google", "english_teacher", "timeout")

    def test_tool_executed_does_not_raise(self):
        collector = LoggingMetricsCollector()
        collector.tool_executed("GetDateAndTime", 0.5, True)

    def test_provider_reconnection_does_not_raise(self):
        collector = LoggingMetricsCollector()
        collector.provider_reconnection("bedrock", True)
