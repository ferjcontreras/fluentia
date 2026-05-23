"""Tests for the GetDateAndTimeTool."""

from fluentia.tools.implementations import GetDateAndTimeTool
from fluentia.tools.state import ToolState


class TestGetDateAndTimeTool:
    async def test_returns_completed(self):
        tool = GetDateAndTimeTool()
        result = await tool.execute({})
        assert result.state == ToolState.COMPLETED

    async def test_data_has_required_fields(self):
        tool = GetDateAndTimeTool()
        result = await tool.execute({})
        assert "current_date" in result.data
        assert "current_time" in result.data
        assert "timezone" in result.data

    def test_tool_metadata(self):
        tool = GetDateAndTimeTool()
        assert tool.name == "getDateAndTimeTool"
        assert "date" in tool.description.lower()
