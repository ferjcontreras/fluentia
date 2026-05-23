"""Tool execution state and result types."""

from dataclasses import dataclass
from dataclasses import field
from enum import StrEnum
from typing import Any


class ToolState(StrEnum):
    """Lifecycle states for tool execution."""

    STARTED = "started"
    PROGRESS = "progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class ToolResult:
    """Result of a tool execution."""

    state: ToolState
    data: dict[str, Any] | None = field(default=None)
    message: str | None = field(default=None)
