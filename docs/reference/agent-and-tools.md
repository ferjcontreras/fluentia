# Agent and Tool Framework Reference

This document describes how agents and tools are defined, registered, and used in Fluentia.

## Agents

### Agent Definition

An agent is a frozen dataclass (`src/fluentia/agents/base.py`) that combines a Jinja2 prompt template with configuration metadata:

```python
@dataclass(frozen=True)
class AgentDefinition:
    name: str                                    # Unique identifier (e.g., "interviewer")
    display_name: str                            # Human-readable name (e.g., "Interview Agent")
    description: str                             # What the agent does
    template_path: str                           # Path to Jinja2 template (relative to resources/)
    default_variables: dict[str, Any] = {}       # Default template variables
    enabled_tools: list[str] = []                # Tools the agent can use
    provider_settings: dict[str, Any] | None = None  # Provider-specific overrides
```

Agents are configuration objects, not classes with behavior. The same `AgentDefinition` works with any provider.

### Prompt Rendering

The `render_prompt()` method merges user-supplied variables with defaults and renders the Jinja2 template:

```python
agent_def.render_prompt({"company_name": "Acme Corp", "questions": "Tell me about yourself."})
```

Variables from the `prompt_config` WebSocket message override `default_variables`. The rendered string becomes the system prompt sent to the voice model.

### Config Fields

The `config_fields` property returns the names of all keys in `default_variables`. The frontend uses this list (via `GET /api/agents`) to generate configuration forms dynamically.

### Agent Registry

The `AgentRegistry` class (`src/fluentia/agents/registry.py`) stores agent definitions by name:

```python
registry = AgentRegistry()
registry.register(interviewer_agent)

agent = registry.get("interviewer")       # Returns AgentDefinition
all_agents = registry.list_agents()       # Returns list[AgentDefinition]
```

Agents are registered during application startup in `create_app()`.

### Built-in Agent: Interviewer

The `interviewer` agent (`src/fluentia/agents/interviewer.py`) conducts structured voice interviews. Its default variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `agent_name` | `Taylor` | Name the agent uses to introduce itself |
| `company_name` | `Avature` | Company mentioned in the interview |
| `questions` | (3 default questions) | Newline-separated interview questions |
| `guidelines` | (default guidelines) | Behavioral instructions for the agent |

The prompt template is at `src/fluentia/agents/templates/interviewer.j2`.

### Creating a New Agent

1. Create a Jinja2 template in `src/fluentia/agents/templates/`
2. Define an `AgentDefinition` instance in a new file under `src/fluentia/agents/`
3. Register it in `create_app()`:

```python
from fluentia.agents.my_agent import my_agent

agent_registry.register(my_agent)
```

The agent becomes available via the `agent` query parameter in the WebSocket URL and appears in the `GET /api/agents` response.

## Tools

### Tool Interface

All tools implement `BaseTool` (`src/fluentia/tools/base.py`):

```python
class BaseTool(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str: ...

    @property
    @abc.abstractmethod
    def description(self) -> str: ...

    @property
    @abc.abstractmethod
    def input_schema(self) -> dict[str, Any]: ...

    @abc.abstractmethod
    async def execute(self, input_data: dict[str, Any]) -> ToolResult: ...
```

| Property | Description |
|----------|-------------|
| `name` | Unique identifier, camelCase by convention (e.g., `getDateAndTimeTool`) |
| `description` | What the tool does (sent to the model as part of tool configuration) |
| `input_schema` | JSON Schema describing expected input parameters |
| `execute()` | Async method that performs the tool's action |

### Tool Results

Tools return a `ToolResult` (`src/fluentia/tools/state.py`):

```python
@dataclass(frozen=True)
class ToolResult:
    state: ToolState          # COMPLETED or FAILED
    data: dict[str, Any] | None = None   # Result data (on success)
    message: str | None = None           # Error or status message
```

`ToolState` is a `StrEnum` with values: `STARTED`, `PROGRESS`, `COMPLETED`, `FAILED`.

### Tool Processor

The `ToolProcessor` class (`src/fluentia/tools/processor.py`) serves as a registry and dispatcher:

```python
processor = ToolProcessor()
processor.register(GetDateAndTimeTool())

# Get specs for model configuration
specs = processor.get_tool_specs()           # All registered tools
specs = processor.get_enabled_specs(["getDateAndTimeTool"])  # Subset

# Execute a tool
result = await processor.execute("getDateAndTimeTool", {})
```

Key behaviors:

- Tool names are stored lowercase for case-insensitive lookup
- `register()` raises `ValueError` if a tool name is already registered
- `execute()` raises `KeyError` if the tool name is not found
- If a tool's `execute()` raises an exception, the processor catches it and returns a `ToolResult` with `state=FAILED`

### Built-in Tool: GetDateAndTimeTool

Returns the current UTC date and time (`src/fluentia/tools/implementations/date_time.py`):

**Input schema**: No parameters required (`{}`)

**Output data**:

```json
{
  "current_time": "14:30:00",
  "current_date": "2025-03-17",
  "day_of_week": "Monday",
  "timezone": "UTC"
}
```

### Creating a New Tool

1. Create a class implementing `BaseTool` in `src/fluentia/tools/implementations/`
2. Export it from `src/fluentia/tools/implementations/__init__.py`
3. Register it in `create_app()`:

```python
from fluentia.tools.implementations import MyNewTool

tool_processor.register(MyNewTool())
```

4. Add the tool name to the `enabled_tools` list of any agent that should use it:

```python
my_agent = AgentDefinition(
    ...,
    enabled_tools=["getDateAndTimeTool", "myNewTool"],
)
```

### How Tools Are Invoked

The tool invocation flow differs slightly between providers, but follows the same pattern:

1. The voice model decides to call a tool based on the tool specifications in its configuration
2. The provider receives a tool-use request with the tool name and input parameters
3. The provider emits a `TOOL_STARTED` event via `context.emit()`
4. The provider calls `ToolProcessor.execute()` with the tool name and input
5. The provider emits `TOOL_COMPLETED` (with result data) or `TOOL_FAILED` (with error message)
6. The provider sends the tool result back to the voice model, which incorporates it into its response

The Bedrock provider handles this directly in `_handle_tool_call()`. The Google provider delegates tool handling to the ADK framework.

### Agent-Tool Relationship

An agent's `enabled_tools` list determines which tools are available during a session with that agent. The provider uses `ToolProcessor.get_enabled_specs()` to get specifications only for the agent's enabled tools, then passes those to the voice model.

This design allows different agents to use different tool subsets without modifying the tool implementations.
