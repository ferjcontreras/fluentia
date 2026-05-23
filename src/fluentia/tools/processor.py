"""Tool registry and dispatcher."""

import logging
from collections.abc import Awaitable
from collections.abc import Callable
from typing import Any

from fluentia.tools.base import BaseTool
from fluentia.tools.state import ToolResult
from fluentia.tools.state import ToolState

logger: logging.Logger = logging.getLogger(__name__)


class ToolProcessor:
    """Registry and dispatcher for tools."""

    def __init__(self) -> None:
        """Initialize an empty tool processor."""
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool. Raises ValueError if name already registered."""
        key: str = tool.name.lower()
        if key in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[key] = tool
        logger.debug("Registered tool: %s", tool.name)

    def get_tool_specs(self) -> list[dict[str, Any]]:
        """Return generic tool specifications for all registered tools."""
        return [
            {
                "name": tool.name,
                "display_name": tool.display_name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self._tools.values()
        ]

    def get_enabled_specs(self, enabled_tools: list[str]) -> list[dict[str, Any]]:
        """Return specs only for the named tools."""
        specs: list[dict[str, Any]] = []
        for tool_name in enabled_tools:
            tool: BaseTool | None = self._tools.get(tool_name.lower())
            if tool:
                specs.append(
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.input_schema,
                    }
                )
            else:
                logger.warning("Enabled tool not found: %s", tool_name)
        return specs

    async def execute(
        self,
        tool_name: str,
        input_data: dict[str, Any],
        on_progress: Callable[[str], Awaitable[None]] | None = None,  # noqa: ARG002  # pylint: disable=unused-argument
    ) -> ToolResult:
        """Execute a tool by name.

        Args:
            tool_name: The tool to execute (case-insensitive).
            input_data: Input parameters matching the tool's input_schema.
            on_progress: Optional callback for intermediate progress messages.

        Returns:
            ToolResult with COMPLETED or FAILED state.

        Raises:
            KeyError: If tool_name is not registered.
        """
        tool: BaseTool | None = self._tools.get(tool_name.lower())
        if tool is None:
            raise KeyError(f"Unknown tool: {tool_name}")

        logger.debug("Executing tool: %s", tool_name)

        try:
            result: ToolResult = await tool.execute(input_data)
            logger.debug("Tool %s completed with state %s", tool_name, result.state)
            return result
        except Exception as e:
            logger.exception("Error executing tool %s", tool_name)
            return ToolResult(state=ToolState.FAILED, message=f"Tool execution failed: {e!s}")

    def get_tool(self, name: str) -> BaseTool | None:
        """Look up a tool by name (case-insensitive)."""
        return self._tools.get(name.lower())

    @property
    def registered_tools(self) -> list[str]:
        """Get list of registered tool names."""
        return [tool.name for tool in self._tools.values()]
