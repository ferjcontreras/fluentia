# Detailed Design: Component Specifications

## Tool Metadata in /api/agents Response

The `/api/agents` response is extended with a `tools` array per agent. Each tool entry includes metadata for the Settings UI.

### Enhanced Response

```json
[
  {
    "name": "interviewer",
    "display_name": "Interview Agent",
    "description": "Conducts structured voice interviews.",
    "fields": [ ... ],
    "tools": [
      {
        "name": "getDateAndTimeTool",
        "display_name": "Date & Time",
        "description": "Get the current date and time in UTC.",
        "enabled_by_default": true,
        "provider_restriction": null
      },
      {
        "name": "getCityTimeTool",
        "display_name": "City Time",
        "description": "Get the current date and time in a specific city.",
        "enabled_by_default": true,
        "provider_restriction": null
      },
      {
        "name": "google_search",
        "display_name": "Google Search",
        "description": "Search the web for information.",
        "enabled_by_default": false,
        "provider_restriction": "google"
      }
    ]
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Tool identifier (matches `BaseTool.name` or ADK built-in name) |
| `display_name` | string | Human-readable name for the UI |
| `description` | string | What the tool does |
| `enabled_by_default` | bool | Whether the agent enables this tool by default |
| `provider_restriction` | string or null | If set, tool only works with this provider |

### Backend: Tool Metadata Source

Tool metadata comes from two sources:

1. **Fluentia tools** (registered in `ToolProcessor`): name and description from `BaseTool` properties. `display_name` is derived from the name or added as a new `BaseTool` property.
2. **Provider-specific tools** (like `google_search`): hardcoded metadata in a registry constant.

```python
# Provider-specific tools that are not BaseTool instances
PROVIDER_TOOLS: list[dict[str, Any]] = [
    {
        "name": "google_search",
        "display_name": "Google Search",
        "description": "Search the web for information using Google.",
        "provider_restriction": "google",
    },
]
```

### Backend: Building the Tools Array

In the `/api/agents` endpoint handler:

```python
def build_agent_tools(
    agent: AgentDefinition,
    tool_processor: ToolProcessor,
) -> list[dict[str, Any]]:
    """Build the tools metadata array for an agent."""
    tools: list[dict[str, Any]] = []

    # Fluentia tools
    for spec in tool_processor.get_tool_specs():
        tools.append({
            "name": spec["name"],
            "display_name": spec.get("display_name", spec["name"]),
            "description": spec["description"],
            "enabled_by_default": spec["name"] in agent.enabled_tools,
            "provider_restriction": None,
        })

    # Provider-specific tools
    for pt in PROVIDER_TOOLS:
        tools.append({
            **pt,
            "enabled_by_default": pt["name"] in agent.enabled_tools,
        })

    return tools
```

### BaseTool Enhancement: display_name

Add an optional `display_name` property to `BaseTool` with a default fallback:

```python
class BaseTool(abc.ABC):
    @property
    def display_name(self) -> str:
        """Human-readable name. Defaults to name."""
        return self.name
```

Tools can override this. `GetDateAndTimeTool` returns `"Date & Time"`, `GetCityTimeTool` returns `"City Time"`.

---

## prompt_config Protocol Extension

The `prompt_config` WebSocket message gains an optional `enabled_tools` field:

### Phase 2 Format (from agent-selector spec)

```json
{
  "type": "prompt_config",
  "variables": { ... }
}
```

### Phase 4 Extension

```json
{
  "type": "prompt_config",
  "variables": { ... },
  "enabled_tools": ["getDateAndTimeTool", "getCityTimeTool"]
}
```

If `enabled_tools` is absent or null, the agent's default tool list is used. If present, it overrides the default list entirely. An empty array `[]` means no tools.

### SessionManager Changes

In `_receive_prompt_config()`:

```python
# Extract tool overrides
enabled_tools: list[str] | None = data.get("enabled_tools")
```

In `handle_websocket()`, if the user provided `enabled_tools`, override the agent definition:

```python
if enabled_tools is not None:
    agent_def = AgentDefinition(
        ...  # copy all fields
        enabled_tools=enabled_tools,
    )
```

---

## GetCityTimeTool Implementation

As designed in the Phase 3 spec (`details-tool-example.md`). Implementation lives at `src/fluentia/tools/implementations/city_time.py`. Key points:

- Hardcoded `CITY_TIMEZONES` dictionary (~35 major cities).
- Uses Python's `zoneinfo` module (standard library, no dependencies).
- Input: `{"city": "Tokyo"}`.
- Output: `{"city": "Tokyo", "timezone": "Asia/Tokyo", "current_time": "23:30:00", ...}`.
- Returns `FAILED` for unknown cities.

Registration in `app.py`:

```python
from fluentia.tools.implementations import GetCityTimeTool

tool_processor.register(GetDateAndTimeTool())
tool_processor.register(GetCityTimeTool())
```

Add to interviewer agent's enabled tools:

```python
enabled_tools=["getDateAndTimeTool", "getCityTimeTool"],
```

---

## Component Interaction

### Session Start with Tool Override

```
User (Settings tab):
  - Selects "Interview Agent"
  - Sees tools: [✓] Date & Time, [✓] City Time, [ ] Google Search
  - Disables "Date & Time"
  - Clicks "Start Conversation"

Frontend:
  - Builds WebSocket URL: /ws/google/user-123/session-abc?agent=interviewer
  - Sends prompt_config:
    {
      "type": "prompt_config",
      "variables": { "agent_name": "Taylor", ... },
      "enabled_tools": ["getCityTimeTool"]
    }

SessionManager:
  - Resolves agent "interviewer"
  - Overrides enabled_tools to ["getCityTimeTool"]
  - Creates SessionContext with modified AgentDefinition
  - Delegates to GoogleProvider

GoogleProvider:
  - Builds ADK tools: [getCityTimeTool wrapper]
  - Creates ADK Agent with tools=[wrapper_fn]
  - Starts bidi session

During conversation:
  - User: "What time is it in Tokyo?"
  - Model calls getCityTimeTool(city="Tokyo")
  - Wrapper emits TOOL_STARTED
  - Wrapper calls tool.execute({"city": "Tokyo"})
  - Wrapper emits TOOL_COMPLETED with result
  - ADK sends result to model
  - Model speaks: "It's 11:30 PM in Tokyo."
```

### Provider Switch with Provider-Restricted Tools

```
User:
  - Selects "Interview Agent" with Google provider
  - Sees tools: [✓] Date & Time, [✓] City Time, [ ] Google Search
  - Enables Google Search

User switches provider to Bedrock:
  - Frontend: Google Search toggle becomes disabled (grayed out, unchecked)
  - Other tools remain as configured
  - Tooltip: "Only available with Google Gemini"
```

---

## Changes Summary

| Component | Change | Description |
|-----------|--------|-------------|
| `tools/base.py` | Modify | Add `display_name` property to `BaseTool` |
| `tools/implementations/city_time.py` | New | `GetCityTimeTool` implementation |
| `tools/implementations/__init__.py` | Modify | Export `GetCityTimeTool` |
| `providers/google.py` | Modify | Accept `ToolProcessor`, build ADK tool wrappers, emit events |
| `providers/google_tools.py` | New | `create_adk_tool_wrapper()` factory function |
| `app.py` | Modify | Register `GetCityTimeTool`, pass `tool_processor` to GoogleProvider, extend `/api/agents` response with tools |
| `session/manager.py` | Modify | Extract `enabled_tools` from prompt_config, override agent definition |
| `static/index.html` | Modify | Add tools section to Settings tab |
| `static/js/app.js` | Modify | Build tool toggles from agent metadata, send enabled_tools in prompt_config |
| `static/css/styles.css` | Modify | Tool toggle styles |

## Testing

### Unit Tests

| Test | Description |
|------|-------------|
| `test_city_time_tool` | Known city, unknown city, empty input, case insensitivity |
| `test_adk_tool_wrapper` | Wrapper function metadata, execution, event emission |
| `test_build_agent_tools` | Correct tools array with enabled_by_default and restrictions |
| `test_prompt_config_with_enabled_tools` | SessionManager extracts and applies tool overrides |
| `test_prompt_config_without_enabled_tools` | Agent defaults used when field absent |
| `test_display_name_default` | BaseTool.display_name falls back to name |

### Integration Tests

| Test | Description |
|------|-------------|
| `test_google_session_with_tools` | Google provider uses tool wrappers in ADK Agent |
| `test_tool_override_empty_list` | Sending `enabled_tools: []` produces no tools in session |
| `test_provider_tool_restriction` | google_search excluded from Bedrock sessions |
