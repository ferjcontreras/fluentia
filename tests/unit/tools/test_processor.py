"""Tests for the tool processor."""

import pytest

from fluentia.tools.base import BaseTool
from fluentia.tools.processor import ToolProcessor
from fluentia.tools.state import ToolResult
from fluentia.tools.state import ToolState


class DummyTool(BaseTool):
    @property
    def name(self):
        return "dummy"

    @property
    def description(self):
        return "A dummy tool for testing"

    @property
    def input_schema(self):
        return {"type": "object", "properties": {"value": {"type": "string"}}}

    async def execute(self, input_data):
        return ToolResult(state=ToolState.COMPLETED, data={"echo": input_data.get("value")})


class FailingTool(BaseTool):
    @property
    def name(self):
        return "failing"

    @property
    def description(self):
        return "A tool that always fails"

    @property
    def input_schema(self):
        return {"type": "object", "properties": {}}

    async def execute(self, input_data):
        raise RuntimeError("intentional failure")


class TestToolProcessor:
    def test_register_and_list(self):
        processor = ToolProcessor()
        processor.register(DummyTool())
        assert "dummy" in processor.registered_tools

    def test_register_duplicate_raises(self):
        processor = ToolProcessor()
        processor.register(DummyTool())
        with pytest.raises(ValueError, match="already registered"):
            processor.register(DummyTool())

    def test_get_tool_specs(self):
        processor = ToolProcessor()
        processor.register(DummyTool())
        specs = processor.get_tool_specs()
        assert len(specs) == 1
        assert specs[0]["name"] == "dummy"
        assert specs[0]["display_name"] == "dummy"
        assert "input_schema" in specs[0]

    def test_display_name_default(self):
        tool = DummyTool()
        assert tool.display_name == "dummy"

    def test_get_enabled_specs_filters(self):
        processor = ToolProcessor()
        processor.register(DummyTool())
        processor.register(FailingTool())

        specs = processor.get_enabled_specs(["dummy"])
        assert len(specs) == 1
        assert specs[0]["name"] == "dummy"

    async def test_execute_success(self):
        processor = ToolProcessor()
        processor.register(DummyTool())
        result = await processor.execute("dummy", {"value": "hello"})
        assert result.state == ToolState.COMPLETED
        assert result.data == {"echo": "hello"}

    async def test_execute_unknown_tool(self):
        processor = ToolProcessor()
        with pytest.raises(KeyError, match="Unknown tool"):
            await processor.execute("nonexistent", {})

    async def test_execute_failure_returns_failed_result(self):
        processor = ToolProcessor()
        processor.register(FailingTool())
        result = await processor.execute("failing", {})
        assert result.state == ToolState.FAILED
        assert "intentional failure" in result.message
