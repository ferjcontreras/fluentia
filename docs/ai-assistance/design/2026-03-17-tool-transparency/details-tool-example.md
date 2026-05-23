# Tool Example: City Time Tool

This document describes a concrete tool that would exercise the Tool Transparency UI with a more interesting example than the existing `getDateAndTimeTool`. This tool is not part of Phase 3 scope (which is frontend-only), but it validates the design and could be implemented alongside or immediately after.

## Purpose

A tool that returns the current date and time in any city the user asks about. During a voice conversation, the user might say "What time is it in Tokyo?" and the model would invoke this tool, producing a visible tool card with structured results.

This is useful because:
- It takes a parameter (`city`), unlike `getDateAndTimeTool` which takes none -- so the Tool Activity card can display input parameters.
- The city-to-timezone mapping is non-trivial enough to justify a tool (the model should not guess timezone offsets).
- It is a natural extension of the existing date/time tool.

## Design

### Tool Definition

```python
"""City time tool implementation."""

import zoneinfo
from datetime import datetime
from typing import Any

from fluentia.tools.base import BaseTool
from fluentia.tools.state import ToolResult
from fluentia.tools.state import ToolState

# Map of common city names to IANA timezone identifiers.
# This is intentionally a curated list, not an exhaustive database.
CITY_TIMEZONES: dict[str, str] = {
    "new york": "America/New_York",
    "los angeles": "America/Los_Angeles",
    "chicago": "America/Chicago",
    "denver": "America/Denver",
    "london": "Europe/London",
    "paris": "Europe/Paris",
    "berlin": "Europe/Berlin",
    "madrid": "Europe/Madrid",
    "rome": "Europe/Rome",
    "amsterdam": "Europe/Amsterdam",
    "moscow": "Europe/Moscow",
    "dubai": "Asia/Dubai",
    "mumbai": "Asia/Kolkata",
    "delhi": "Asia/Kolkata",
    "bangkok": "Asia/Bangkok",
    "singapore": "Asia/Singapore",
    "hong kong": "Asia/Hong_Kong",
    "shanghai": "Asia/Shanghai",
    "beijing": "Asia/Shanghai",
    "tokyo": "Asia/Tokyo",
    "seoul": "Asia/Seoul",
    "sydney": "Australia/Sydney",
    "melbourne": "Australia/Melbourne",
    "auckland": "Pacific/Auckland",
    "sao paulo": "America/Sao_Paulo",
    "buenos aires": "America/Argentina/Buenos_Aires",
    "mexico city": "America/Mexico_City",
    "toronto": "America/Toronto",
    "vancouver": "America/Vancouver",
    "cairo": "Africa/Cairo",
    "johannesburg": "Africa/Johannesburg",
    "lagos": "Africa/Lagos",
    "nairobi": "Africa/Nairobi",
}


class GetCityTimeTool(BaseTool):
    """Tool for getting the current date and time in a specific city."""

    @property
    def name(self) -> str:
        """Get the tool name."""
        return "getCityTimeTool"

    @property
    def description(self) -> str:
        """Get the tool description."""
        return (
            "Get the current date and time in a specific city. "
            "Accepts a city name (e.g., 'Tokyo', 'New York', 'London')."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        """Get the input schema."""
        return {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name (e.g., 'Tokyo', 'New York', 'Buenos Aires')",
                }
            },
            "required": ["city"],
        }

    async def execute(self, input_data: dict[str, Any]) -> ToolResult:
        """Execute the tool to get current time in a city."""
        city_input: str = input_data.get("city", "").strip()
        if not city_input:
            return ToolResult(
                state=ToolState.FAILED,
                message="City name is required.",
            )

        city_lower: str = city_input.lower()
        tz_name: str | None = CITY_TIMEZONES.get(city_lower)

        if tz_name is None:
            return ToolResult(
                state=ToolState.FAILED,
                message=f"Unknown city: '{city_input}'. Try a major city name.",
            )

        tz: zoneinfo.ZoneInfo = zoneinfo.ZoneInfo(tz_name)
        now: datetime = datetime.now(tz=tz)

        return ToolResult(
            state=ToolState.COMPLETED,
            data={
                "city": city_input,
                "timezone": tz_name,
                "current_time": now.strftime("%H:%M:%S"),
                "current_date": now.strftime("%Y-%m-%d"),
                "day_of_week": now.strftime("%A"),
                "utc_offset": now.strftime("%z"),
            },
        )
```

### Key Decisions

**Hardcoded city map instead of a geocoding library**: The `CITY_TIMEZONES` dictionary maps ~35 major cities to IANA timezone identifiers. This has zero external dependencies, no network calls, and predictable behavior. The model's job is to extract the city name from the user's speech; the tool's job is to map it to a timezone.

**Graceful failure for unknown cities**: If the model passes a city not in the map, the tool returns `FAILED` with a helpful message. The model can then tell the user "I don't have timezone data for that city" rather than guessing.

**Uses `zoneinfo` from the standard library**: Python 3.9+ includes `zoneinfo`, which uses the system's IANA timezone database. No third-party packages needed.

### Registration

In `app.py` lifespan handler:

```python
from fluentia.tools.implementations import GetCityTimeTool

tool_processor.register(GetDateAndTimeTool())
tool_processor.register(GetCityTimeTool())
```

Add to the interviewer agent's enabled tools (or any agent that should have it):

```python
enabled_tools=["getDateAndTimeTool", "getCityTimeTool"],
```

### Tool Card Appearance

When the user asks "What time is it in Tokyo?" during a Bedrock session:

**Running state:**

```
┌──────────────────────────────────────────┐
│  ⟳  getCityTimeTool              0.1s... │
└──────────────────────────────────────────┘
```

**Completed state:**

```
┌──────────────────────────────────────────┐
│  ✓  getCityTimeTool               142ms  │
│                                          │
│  city: "Tokyo"                           │
│  timezone: "Asia/Tokyo"                  │
│  current_time: "23:30:00"               │
│  current_date: "2026-03-17"             │
│  day_of_week: "Tuesday"                 │
│  utc_offset: "+0900"                    │
│                                    ▼ More │
└──────────────────────────────────────────┘
```

Expanding "More" would show the input parameters:

```
  Input: { "city": "Tokyo" }
```

**Failed state (unknown city):**

```
┌──────────────────────────────────────────┐
│  ✗  getCityTimeTool               45ms   │
│                                          │
│  Unknown city: 'Smallville'. Try a       │
│  major city name.                        │
└──────────────────────────────────────────┘
```

### Conversation Center Notification

While the tool runs (typically <200ms):

```
  ⟳ Using getCityTimeTool...
```

The notification disappears when the tool completes, and the model speaks the answer.

## Testing

| Test | Description |
|------|-------------|
| `test_city_time_known_city` | Tokyo, New York, London return correct timezone and valid time |
| `test_city_time_case_insensitive` | "tokyo", "TOKYO", "Tokyo" all resolve correctly |
| `test_city_time_unknown_city` | Unknown city returns `FAILED` with descriptive message |
| `test_city_time_empty_input` | Empty string returns `FAILED` |
| `test_city_time_utc_offset` | UTC offset matches expected value for the timezone |
