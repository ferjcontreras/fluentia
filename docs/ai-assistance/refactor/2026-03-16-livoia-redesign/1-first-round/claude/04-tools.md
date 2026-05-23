# Tool Framework Design

## Overview

The tool framework allows LLM/speech models to invoke server-side actions during a conversation. The current PoC implementation is well-designed and will be carried forward with minor reorganization.

## Current State

The PoC has:
- `BaseTool` ABC with `name`, `description`, `input_schema`, `execute`
- `ToolProcessor` for registration, lookup, and execution
- `GetDateAndTimeTool` as the only built-in tool
- Tool specs formatted for Nova Sonic API (`toolSpec` format with JSON-stringified schema)
- SpeechCaller handles tool execution automatically during conversations

Currently, the Bedrock adapter does **not** register any tools (the `tools` parameter defaults to `[]`). The tool framework is wired but unused in the web demo.

## Design for the New Project

### Package Structure

```
livoia/tools/
├── __init__.py          # Public API: BaseTool, ToolProcessor, ToolConfig
├── base.py              # BaseTool ABC, ToolConfig
├── processor.py         # ToolProcessor
└── builtin/
    ├── __init__.py      # Re-export built-in tools
    └── date_time.py     # GetDateAndTimeTool
```

### BaseTool ABC (unchanged)

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
    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]: ...

    def to_tool_spec(self) -> dict[str, Any]:
        """Convert to Nova Sonic API format."""
        return {
            "toolSpec": {
                "name": self.name,
                "description": self.description,
                "inputSchema": {"json": json.dumps(self.input_schema)},
            }
        }
```

### ToolProcessor (unchanged)

- `register_tool(tool)`: Register a tool
- `get_tool(name)`: Look up by name (case-insensitive)
- `get_all_tool_specs()`: Get specs for all registered tools
- `execute_tool(name, input_data)`: Execute a tool by name

### Tool Spec Format Consideration

The current `to_tool_spec()` produces the Nova Sonic format. When Google ADK supports tools, it may need a different format. Two approaches:

**Option A: Provider-specific formatting (recommended)**
- `BaseTool` stores raw schema
- Each provider formats the spec for its API

**Option B: Multiple format methods**
- `to_bedrock_spec()`, `to_google_spec()` on BaseTool

For v1, keep the current approach since only Bedrock uses tools. Refactor when Google tool support is added.

## Integration with Bedrock Provider

The Bedrock provider's tool execution flow:

```
1. NovaSonicClient receives ToolUse event from model
2. NovaSonicClient puts SpeechEvents.ToolUse on event queue
3. Provider's event processing loop sees ToolUse event
4. Provider calls ToolProcessor.execute_tool()
5. Provider sends result back via NovaSonicClient.send_tool_result()
6. Model processes result and continues conversation
```

This is the same flow as the PoC's SpeechCaller, but the tool execution logic will live in the BedrockProvider rather than a separate SpeechCaller module (since there's no need for the intermediate module layer).

## Future: User-Configurable Tools

### UI for Tool Configuration

A future version of the Settings tab (or a dedicated "Tools" section) will allow users to:

1. See available tools with descriptions
2. Toggle tools on/off
3. Configure tool-specific parameters

### Tool Configuration Message

Extend the `prompt_config` WebSocket message:

```json
{
  "type": "prompt_config",
  "agent_name": "Taylor",
  "company_name": "Avature",
  "questions": "...",
  "guidelines": "...",
  "enabled_tools": ["getDateAndTime", "searchWeb"]
}
```

The backend would filter registered tools based on `enabled_tools` before passing them to the provider.

## Future: Orchestrator Tools

### Concept

Livoia agent can invoke external agents via the company's Orchestrator system. For example:

```python
class OrchestratorTool(BaseTool):
    @property
    def name(self) -> str:
        return "invokeOrchestratorAgent"

    @property
    def description(self) -> str:
        return (
            "Invoke an external agent from the Orchestrator system. "
            "Use this when the user requests complex tasks like "
            "writing a job description or generating a report."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "agent_name": {"type": "string", "description": "Name of the agent to invoke"},
                "task_description": {"type": "string", "description": "What the agent should do"},
            },
            "required": ["agent_name", "task_description"],
        }

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        # Call Orchestrator API
        # This is async and may take seconds to minutes
        result = await self._orchestrator_client.invoke(
            agent_name=input_data["agent_name"],
            task=input_data["task_description"],
        )
        return {"result": result}
```

### Long-Running Tool Considerations

Orchestrator tools may take significant time (seconds to minutes). Design considerations:

1. **Async execution**: Tool `execute()` is already async, so it can `await` long operations
2. **During execution**: The conversation continues. The LLM is waiting for the tool result but the audio stream remains active. The LLM should tell the user "I'm working on that, give me a moment."
3. **Result delivery**: When the tool completes, the result is sent back to the model, which can then discuss it with the user
4. **UI feedback**: The Tool Use tab (future) shows the pending operation with a spinner
5. **Timeout**: Tools should have configurable timeouts to prevent indefinite waits

### Tool Transparency

When a tool is invoked, the backend should emit a WebSocket event so the frontend can display it:

```json
{
  "toolInvocation": {
    "name": "invokeOrchestratorAgent",
    "input": {"agent_name": "job-description-writer", "task_description": "..."},
    "status": "running"
  },
  "author": "system"
}
```

And when it completes:

```json
{
  "toolResult": {
    "name": "invokeOrchestratorAgent",
    "output": {"result": "..."},
    "duration_ms": 5200,
    "status": "completed"
  },
  "author": "system"
}
```

## Future: Web Search Tool

```python
class WebSearchTool(BaseTool):
    @property
    def name(self) -> str:
        return "searchWeb"

    @property
    def description(self) -> str:
        return "Search the web for current information."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["query"],
        }

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        results = await self._search_client.search(input_data["query"])
        return {"results": results}
```

## Future: File Search Tool

```python
class FileSearchTool(BaseTool):
    @property
    def name(self) -> str:
        return "searchFiles"

    @property
    def description(self) -> str:
        return "Search and read files from a specified directory."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "directory": {"type": "string"},
                "query": {"type": "string"},
            },
            "required": ["directory", "query"],
        }
```
