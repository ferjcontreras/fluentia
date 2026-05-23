"""Metrics collection with Protocol-based abstraction."""

from typing import Protocol

import structlog

log: structlog.stdlib.BoundLogger = structlog.get_logger()


class MetricsCollector(Protocol):
    """Interface for collecting application metrics."""

    def session_started(self, provider: str, agent: str) -> None:
        """Record a session start."""

    def session_ended(self, provider: str, agent: str, duration_seconds: float) -> None:
        """Record a session end."""

    def session_error(self, provider: str, agent: str, error_type: str) -> None:
        """Record a session error."""

    def tool_executed(self, tool_name: str, duration_seconds: float, success: bool) -> None:
        """Record a tool execution."""

    def provider_reconnection(self, provider: str, success: bool) -> None:
        """Record a provider reconnection attempt."""


class LoggingMetricsCollector:
    """Emits metrics as structured log events."""

    def session_started(self, provider: str, agent: str) -> None:
        """Log session start metric."""
        log.info("metric.session_started", provider=provider, agent=agent)

    def session_ended(self, provider: str, agent: str, duration_seconds: float) -> None:
        """Log session end metric."""
        log.info("metric.session_ended", provider=provider, agent=agent, duration=duration_seconds)

    def session_error(self, provider: str, agent: str, error_type: str) -> None:
        """Log session error metric."""
        log.info("metric.session_error", provider=provider, agent=agent, error_type=error_type)

    def tool_executed(self, tool_name: str, duration_seconds: float, success: bool) -> None:
        """Log tool execution metric."""
        log.info("metric.tool_executed", tool=tool_name, duration=duration_seconds, success=success)

    def provider_reconnection(self, provider: str, success: bool) -> None:
        """Log provider reconnection metric."""
        log.info("metric.provider_reconnection", provider=provider, success=success)
