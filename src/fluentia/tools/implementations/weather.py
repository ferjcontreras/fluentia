"""Weather tool implementation."""

from datetime import UTC
from datetime import datetime
from typing import Any

from fluentia.tools.base import BaseTool
from fluentia.tools.state import ToolResult
from fluentia.tools.state import ToolState

CONDITIONS: list[str] = [
    "Sunny",
    "Partly Cloudy",
    "Cloudy",
    "Overcast",
    "Light Rain",
    "Rain",
    "Thunderstorm",
    "Snow",
]


class GetWeatherTool(BaseTool):
    """Tool for getting mock weather information for a city."""

    @property
    def name(self) -> str:
        """Get the tool name."""
        return "getWeatherTool"

    @property
    def display_name(self) -> str:
        """Get the human-readable tool name."""
        return "Weather"

    @property
    def description(self) -> str:
        """Get the tool description."""
        return (
            "Get current weather information for a city. "
            "The city must be provided in 'City, CC' format "
            "where CC is the ISO 3166-1 alpha-2 country code "
            "(e.g. 'Paris, FR', 'New York, US', 'Tokyo, JP')."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        """Get the input schema."""
        return {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": (
                        "City name in 'City, CC' format using ISO 3166-1 "
                        "alpha-2 country code (e.g. 'London, GB', "
                        "'Buenos Aires, AR', 'Sydney, AU')"
                    ),
                }
            },
            "required": ["city"],
        }

    async def execute(self, input_data: dict[str, Any]) -> ToolResult:
        """Execute the tool to get mock weather for a city."""
        city_raw: str = input_data.get("city", "")
        city: str = city_raw.strip()
        if not city:
            return ToolResult(state=ToolState.FAILED, message="City name is required")

        today: str = datetime.now(tz=UTC).strftime("%Y-%m-%d")
        seed: int = hash(city.lower() + today)

        return ToolResult(
            state=ToolState.COMPLETED,
            data={
                "city": city,
                "temperature_celsius": (seed % 44) - 5,
                "condition": CONDITIONS[seed % len(CONDITIONS)],
                "humidity_percent": 30 + (seed % 66),
            },
        )
