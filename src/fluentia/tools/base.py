"""Abstract base class for tools."""

import abc
from typing import Any

from fluentia.tools.state import ToolResult


class BaseTool(abc.ABC):
    """Abstract base class for all tools.

    Tools extend agent capabilities beyond conversation. Each tool is a
    discrete, named operation that a voice model can invoke during a session.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Unique tool identifier (camelCase by convention)."""
        raise NotImplementedError("Subclasses must implement `name`")

    @property
    def display_name(self) -> str:
        """Human-readable name for the UI. Defaults to name."""
        return self.name

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """Description of what the tool does. Used by the model to decide when to call it."""
        raise NotImplementedError("Subclasses must implement `description`")

    @property
    @abc.abstractmethod
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema describing the tool's input parameters."""
        raise NotImplementedError("Subclasses must implement `input_schema`")

    @abc.abstractmethod
    async def execute(self, input_data: dict[str, Any]) -> ToolResult:
        """Execute the tool with the given input.

        Args:
            input_data: Tool input parameters matching the input_schema.

        Returns:
            ToolResult with state COMPLETED or FAILED.
        """
        raise NotImplementedError("Subclasses must implement `execute()`")
