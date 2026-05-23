"""Structured JSON logging with correlation IDs."""

import logging
from typing import Any

import structlog


class HealthCheckFilter(logging.Filter):
    """Filter out health check endpoint log entries."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Exclude /health and /ready from access logs."""
        message: str = record.getMessage()
        return "/health" not in message and "/ready" not in message


def mask_sensitive_values(
    logger: Any,  # noqa: ARG001  # pylint: disable=unused-argument
    method_name: str,  # noqa: ARG001  # pylint: disable=unused-argument
    event_dict: Any,
) -> Any:
    """Structlog processor that redacts sensitive values."""
    sensitive_patterns: tuple[str, ...] = ("_key", "_secret", "_token", "_password", "_credential")
    for key in list(event_dict.keys()):
        key_lower: str = key.lower()
        if any(pattern in key_lower for pattern in sensitive_patterns):
            event_dict[key] = "***REDACTED***"
    return event_dict


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structured logging with structlog."""
    numeric_level: int = getattr(logging, log_level.upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            mask_sensitive_values,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Route standard-library logging through structlog so that logger.info()
    # calls in provider / session code produce the same JSON output as
    # structlog.get_logger() calls.
    root: logging.Logger = logging.getLogger()
    root.setLevel(numeric_level)
    # Remove any pre-existing handlers (e.g. from basicConfig)
    root.handlers.clear()
    handler: logging.Handler = logging.StreamHandler()
    handler.setLevel(numeric_level)
    formatter: structlog.stdlib.ProcessorFormatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            mask_sensitive_values,
        ],
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)

    # Apply health check filter to uvicorn access logger
    uvicorn_access: logging.Logger = logging.getLogger("uvicorn.access")
    uvicorn_access.addFilter(HealthCheckFilter())

    # Cap noisy third-party loggers
    for noisy_logger in ("websockets", "google_adk", "google_genai", "google.adk", "google.genai"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def log_config_summary(config: Any) -> None:
    """Log configuration summary with secrets redacted."""
    log: structlog.stdlib.BoundLogger = structlog.get_logger()
    summary: dict[str, Any] = {}
    sensitive_patterns: tuple[str, ...] = ("key", "secret", "token", "password", "credential")

    for field_name in type(config).model_fields:
        value: Any = getattr(config, field_name)
        if any(pattern in field_name.lower() for pattern in sensitive_patterns):
            summary[field_name] = "***REDACTED***"
        elif hasattr(type(value), "model_fields"):
            # Nested Pydantic model: summarize recursively
            nested: dict[str, Any] = {}
            for nested_name in type(value).model_fields:
                nested_value: Any = getattr(value, nested_name)
                if any(pattern in nested_name.lower() for pattern in sensitive_patterns):
                    nested[nested_name] = "***REDACTED***"
                else:
                    nested[nested_name] = str(nested_value)
            summary[field_name] = nested
        else:
            summary[field_name] = str(value)

    log.info("app_started", config=summary)
