"""Tests for Bedrock voice provider."""

import json
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from fluentia.config import BedrockProviderConfig
from fluentia.providers.base import SessionContext
from fluentia.providers.bedrock.client import _InternalToolUseEvent
from fluentia.providers.bedrock.provider import BedrockProvider
from fluentia.session.events import SessionEvent
from fluentia.session.events import SessionEventType
from fluentia.tools import ToolProcessor
from fluentia.tools import ToolResult
from fluentia.tools import ToolState
from fluentia.tools.implementations import GetDateAndTimeTool


@pytest.fixture
def tool_processor() -> ToolProcessor:
    """Fixture for a ToolProcessor with a registered tool."""
    processor: ToolProcessor = ToolProcessor()
    processor.register(GetDateAndTimeTool())
    return processor


@pytest.fixture
def provider(tool_processor: ToolProcessor) -> BedrockProvider:
    """Fixture for a BedrockProvider."""
    config: BedrockProviderConfig = BedrockProviderConfig()
    return BedrockProvider(provider_config=config, tool_processor=tool_processor)


class TestBedrockProviderFormatToolSpecs:
    """Tests for BedrockProvider._format_tool_specs."""

    def test_formats_enabled_tools(self, provider: BedrockProvider):
        """Test that tool specs are formatted for Bedrock API."""
        specs: list[dict[str, Any]] = provider._format_tool_specs(["getDateAndTimeTool"])
        assert len(specs) == 1
        tool_spec: dict[str, Any] = specs[0]["toolSpec"]
        assert tool_spec["name"] == "getDateAndTimeTool"
        assert "description" in tool_spec
        assert "inputSchema" in tool_spec
        # inputSchema.json should be a JSON string
        parsed: dict[str, Any] = json.loads(tool_spec["inputSchema"]["json"])
        assert isinstance(parsed, dict)

    def test_empty_enabled_tools(self, provider: BedrockProvider):
        """Test formatting with no enabled tools."""
        specs: list[dict[str, Any]] = provider._format_tool_specs([])
        assert specs == []

    def test_unknown_tool_filtered(self, provider: BedrockProvider):
        """Test that unknown tools are filtered out."""
        specs: list[dict[str, Any]] = provider._format_tool_specs(["nonexistent_tool"])
        assert specs == []


class TestBedrockProviderHandleToolCall:
    """Tests for BedrockProvider._handle_tool_call."""

    @pytest.mark.asyncio
    async def test_successful_tool_execution(self, provider: BedrockProvider):
        """Test handling a successful tool call."""
        mock_client: MagicMock = MagicMock()
        mock_client.send_tool_result = AsyncMock()
        emit: AsyncMock = AsyncMock()
        context: SessionContext = SessionContext(
            user_id="u1", session_id="s1", agent_definition=MagicMock(enabled_tools=[]), emit=emit
        )
        event: _InternalToolUseEvent = _InternalToolUseEvent(
            tool_use_id="tu-1", tool_name="getDateAndTimeTool", tool_input={"timezone": "UTC"}
        )

        await provider._handle_tool_call(mock_client, event, context)

        # Should emit TOOL_STARTED and TOOL_COMPLETED
        assert emit.call_count == 2
        started_event: SessionEvent = emit.call_args_list[0][0][0]
        completed_event: SessionEvent = emit.call_args_list[1][0][0]
        assert started_event.type == SessionEventType.TOOL_STARTED
        assert completed_event.type == SessionEventType.TOOL_COMPLETED
        assert completed_event.payload["tool_name"] == "getDateAndTimeTool"

        # Should send result back to Bedrock
        mock_client.send_tool_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_tool_emits_failure(self, provider: BedrockProvider):
        """Test handling an unknown tool call."""
        mock_client: MagicMock = MagicMock()
        mock_client.send_tool_result = AsyncMock()
        emit: AsyncMock = AsyncMock()
        context: SessionContext = SessionContext(
            user_id="u1", session_id="s1", agent_definition=MagicMock(enabled_tools=[]), emit=emit
        )
        event: _InternalToolUseEvent = _InternalToolUseEvent(
            tool_use_id="tu-1", tool_name="nonexistent_tool", tool_input={}
        )

        await provider._handle_tool_call(mock_client, event, context)

        # Should emit TOOL_STARTED and TOOL_FAILED
        assert emit.call_count == 2
        failed_event: SessionEvent = emit.call_args_list[1][0][0]
        assert failed_event.type == SessionEventType.TOOL_FAILED
        assert "nonexistent_tool" in failed_event.payload["message"]

        # Should send error result back to Bedrock
        mock_client.send_tool_result.assert_called_once()
        result_args: dict[str, Any] = mock_client.send_tool_result.call_args[0][1]
        assert "error" in result_args

    @pytest.mark.asyncio
    async def test_failed_tool_execution(self, provider: BedrockProvider):
        """Test handling a tool that returns FAILED state."""
        mock_client: MagicMock = MagicMock()
        mock_client.send_tool_result = AsyncMock()
        emit: AsyncMock = AsyncMock()
        context: SessionContext = SessionContext(
            user_id="u1", session_id="s1", agent_definition=MagicMock(enabled_tools=[]), emit=emit
        )

        # Mock the tool processor to return a FAILED result
        failed_result: ToolResult = ToolResult(
            state=ToolState.FAILED, message="Something went wrong"
        )
        provider._tool_processor.execute = AsyncMock(return_value=failed_result)

        event: _InternalToolUseEvent = _InternalToolUseEvent(
            tool_use_id="tu-1", tool_name="getDateAndTimeTool", tool_input={}
        )

        await provider._handle_tool_call(mock_client, event, context)

        # Should emit TOOL_STARTED and TOOL_FAILED
        assert emit.call_count == 2
        failed_event: SessionEvent = emit.call_args_list[1][0][0]
        assert failed_event.type == SessionEventType.TOOL_FAILED
        assert "Something went wrong" in failed_event.payload["message"]

        # Should send error result back to Bedrock
        mock_client.send_tool_result.assert_called_once()
        result_args: dict[str, Any] = mock_client.send_tool_result.call_args[0][1]
        assert "error" in result_args
