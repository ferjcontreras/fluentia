"""Date and time tool implementation."""

from datetime import UTC
from datetime import datetime
from typing import Any

from fluentia.tools.base import BaseTool
from fluentia.tools.state import ToolResult
from fluentia.tools.state import ToolState


class GetDateAndTimeTool(BaseTool):
    """Tool for getting the current date and time in UTC."""

    @property
    def name(self) -> str:
        """Get the tool name."""
        return "getDateAndTimeTool"

    @property
    def display_name(self) -> str:
        """Get the human-readable tool name."""
        return "Date & Time"

    @property
    def description(self) -> str:
        """Get the tool description."""
        return "Get information about the current date and time"

    @property
    def input_schema(self) -> dict[str, Any]:
        """Get the input schema."""
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, input_data: dict[str, Any]) -> ToolResult:  # noqa: ARG002
        """Execute the tool to get current date and time."""
        now: datetime = datetime.now(tz=UTC)
        return ToolResult(
            state=ToolState.COMPLETED,
            data={
                "current_time": now.strftime("%H:%M:%S"),
                "current_date": now.strftime("%Y-%m-%d"),
                "day_of_week": now.strftime("%A"),
                "timezone": "UTC",
            },
        )
