"""Tests for the weather tool."""

import pytest

from fluentia.tools.implementations.weather import GetWeatherTool
from fluentia.tools.state import ToolState


@pytest.fixture
def tool() -> GetWeatherTool:
    """Create a GetWeatherTool instance."""
    return GetWeatherTool()


class TestGetWeatherTool:
    """Tests for GetWeatherTool."""

    def test_metadata(self, tool: GetWeatherTool):
        """Test tool metadata properties."""
        assert tool.name == "getWeatherTool"
        assert tool.display_name == "Weather"
        assert "city" in tool.input_schema["properties"]

    @pytest.mark.asyncio
    async def test_valid_city(self, tool: GetWeatherTool):
        """Test getting weather for a valid city."""
        result = await tool.execute({"city": "London, GB"})
        assert result.state == ToolState.COMPLETED
        assert result.data is not None
        assert result.data["city"] == "London, GB"
        assert -5 <= result.data["temperature_celsius"] <= 38
        assert 30 <= result.data["humidity_percent"] <= 95
        assert isinstance(result.data["condition"], str)

    @pytest.mark.asyncio
    async def test_deterministic(self, tool: GetWeatherTool):
        """Test that results are deterministic for the same city on the same day."""
        result1 = await tool.execute({"city": "Tokyo, JP"})
        result2 = await tool.execute({"city": "Tokyo, JP"})
        assert result1.data == result2.data

    @pytest.mark.asyncio
    async def test_different_cities_differ(self, tool: GetWeatherTool):
        """Test that different cities produce different results."""
        result1 = await tool.execute({"city": "London, GB"})
        result2 = await tool.execute({"city": "Sydney, AU"})
        assert result1.data is not None
        assert result2.data is not None
        # At least one field should differ (extremely unlikely to match all 3)
        assert (
            result1.data["temperature_celsius"] != result2.data["temperature_celsius"]
            or result1.data["condition"] != result2.data["condition"]
            or result1.data["humidity_percent"] != result2.data["humidity_percent"]
        )

    @pytest.mark.asyncio
    async def test_empty_input(self, tool: GetWeatherTool):
        """Test empty city input returns FAILED."""
        result = await tool.execute({"city": ""})
        assert result.state == ToolState.FAILED

    @pytest.mark.asyncio
    async def test_missing_city_key(self, tool: GetWeatherTool):
        """Test missing city key returns FAILED."""
        result = await tool.execute({})
        assert result.state == ToolState.FAILED
