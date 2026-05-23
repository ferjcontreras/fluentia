"""Tests for Google ADK tool wrapper factory."""

from typing import Any
from unittest.mock import AsyncMock

import pytest

from fluentia.providers.google_tools import create_adk_tool_wrapper
from fluentia.session.events import SessionEvent
from fluentia.session.events import SessionEventType
from fluentia.tools.base import BaseTool
from fluentia.tools.state import ToolResult
from fluentia.tools.state import ToolState


class _DummyTool(BaseTool):
    """A simple tool for testing the wrapper."""

    @property
    def name(self) -> str:
        return "testTool"

    @property
    def description(self) -> str:
        return "A test tool"

    @property
    def input_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {"value": {"type": "string"}}}

    async def execute(self, input_data: dict[str, Any]) -> ToolResult:
        return ToolResult(state=ToolState.COMPLETED, data={"echo": input_data.get("value")})


class _FailingTool(BaseTool):
    """A tool that returns FAILED state."""

    @property
    def name(self) -> str:
        return "failingTool"

    @property
    def description(self) -> str:
        return "A tool that fails"

    @property
    def input_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}}

    async def execute(self, input_data: dict[str, Any]) -> ToolResult:
        return ToolResult(state=ToolState.FAILED, message="something went wrong")


class _ExplodingTool(BaseTool):
    """A tool that raises an exception."""

    @property
    def name(self) -> str:
        return "explodingTool"

    @property
    def description(self) -> str:
        return "A tool that explodes"

    @property
    def input_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}}

    async def execute(self, input_data: dict[str, Any]) -> ToolResult:
        raise RuntimeError("boom")


class TestCreateAdkToolWrapper:
    """Tests for create_adk_tool_wrapper."""

    def test_wrapper_metadata(self):
        """Test that wrapper has correct __name__ and __doc__."""
        emit: AsyncMock = AsyncMock()
        wrapper = create_adk_tool_wrapper(_DummyTool(), emit)
        assert wrapper.__name__ == "testTool"
        assert wrapper.__doc__ == "A test tool"

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Test wrapper calls tool and returns result data."""
        emit: AsyncMock = AsyncMock()
        wrapper = create_adk_tool_wrapper(_DummyTool(), emit)
        result: dict[str, Any] = await wrapper(value="hello")
        assert result == {"echo": "hello"}

    @pytest.mark.asyncio
    async def test_emits_tool_started(self):
        """Test that TOOL_STARTED is emitted before execution."""
        emit: AsyncMock = AsyncMock()
        wrapper = create_adk_tool_wrapper(_DummyTool(), emit)
        await wrapper(value="hello")

        first_call: SessionEvent = emit.call_args_list[0][0][0]
        assert first_call.type == SessionEventType.TOOL_STARTED
        assert first_call.payload["tool_name"] == "testTool"
        assert "tool_id" in first_call.payload

    @pytest.mark.asyncio
    async def test_emits_tool_completed(self):
        """Test that TOOL_COMPLETED is emitted on success."""
        emit: AsyncMock = AsyncMock()
        wrapper = create_adk_tool_wrapper(_DummyTool(), emit)
        await wrapper(value="hello")

        assert emit.call_count == 2
        second_call: SessionEvent = emit.call_args_list[1][0][0]
        assert second_call.type == SessionEventType.TOOL_COMPLETED
        assert second_call.payload["tool_name"] == "testTool"
        assert second_call.payload["result"] == {"echo": "hello"}

    @pytest.mark.asyncio
    async def test_emits_tool_failed_on_failed_result(self):
        """Test that TOOL_FAILED is emitted when tool returns FAILED state."""
        emit: AsyncMock = AsyncMock()
        wrapper = create_adk_tool_wrapper(_FailingTool(), emit)
        result: dict[str, Any] = await wrapper()

        assert "error" in result
        assert emit.call_count == 2
        second_call: SessionEvent = emit.call_args_list[1][0][0]
        assert second_call.type == SessionEventType.TOOL_FAILED
        assert "something went wrong" in second_call.payload["error"]

    @pytest.mark.asyncio
    async def test_emits_tool_failed_on_exception(self):
        """Test that TOOL_FAILED is emitted when tool raises an exception."""
        emit: AsyncMock = AsyncMock()
        wrapper = create_adk_tool_wrapper(_ExplodingTool(), emit)
        result: dict[str, Any] = await wrapper()

        assert "error" in result
        assert "boom" in result["error"]
        assert emit.call_count == 2
        second_call: SessionEvent = emit.call_args_list[1][0][0]
        assert second_call.type == SessionEventType.TOOL_FAILED

    @pytest.mark.asyncio
    async def test_tool_id_consistent(self):
        """Test that tool_id is the same in STARTED and COMPLETED events."""
        emit: AsyncMock = AsyncMock()
        wrapper = create_adk_tool_wrapper(_DummyTool(), emit)
        await wrapper(value="test")

        started: SessionEvent = emit.call_args_list[0][0][0]
        completed: SessionEvent = emit.call_args_list[1][0][0]
        assert started.payload["tool_id"] == completed.payload["tool_id"]
