"""Health and readiness endpoint handlers."""

import time
from typing import Any

from fluentia.config import AppConfig

# Module-level start time, set when the module is first imported
_start_time: float = time.monotonic()


def get_health() -> dict[str, Any]:
    """Liveness probe handler. Returns 200 if the process is running."""
    uptime: float = round(time.monotonic() - _start_time, 1)
    return {"status": "ok", "version": "1.0.0", "uptime_seconds": uptime}


def get_readiness(config: AppConfig) -> dict[str, Any]:
    """Readiness probe handler. Reports provider availability."""
    providers: dict[str, str] = {}

    if config.google.api_key:
        providers["google"] = "available"
    else:
        providers["google"] = "not_configured"

    # Bedrock uses IRSA in production so credentials may not be in config
    providers["bedrock"] = "available"

    return {"status": "ready", "providers": providers}
