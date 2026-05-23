# 5. Tool Framework

## Overview

Tools extend agent capabilities beyond conversation. A tool is a discrete, named operation that the voice model can invoke during a session -- for example, checking the current time, searching a database, or calling an external API.

The tool framework provides:
- A base class for defining tools
- A registry for tool registration and dispatch
- A result type with a state machine for async tool execution
- Provider-agnostic tool specs that each provider formats for its own API

## BaseTool

```python
class BaseTool(abc.ABC):
    """Abstract base class for all tools."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Unique tool identifier (camelCase by convention)."""
        raise NotImplementedError("Subclasses must implement `name`")

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """Description of what the tool does. Used by the model to decide when to call it."""
        raise NotImplementedError("Subclasses must implement `description`")

    @property
    @abc.abstractmethod
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema describing the tool's input parameters."""
        raise NotImplementedError("Subclasses must implement `input_schema`")

    @abc.abstractmethod
    async def execute(self, input_data: dict[str, Any]) -> ToolResult:
        """Execute the tool with the given input.

        Returns a ToolResult with state COMPLETED or FAILED.
        Long-running tools may emit intermediate PROGRESS results via callbacks.
        """
        raise NotImplementedError("Subclasses must implement `execute()`")
```

## ToolResult and ToolState

```python
class ToolState(str, Enum):
    """Lifecycle states for tool execution."""
    STARTED = "started"
    PROGRESS = "progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class ToolResult:
    """Result of a tool execution."""
    state: ToolState
    data: dict[str, Any] | None = None    # Tool output data
    message: str | None = None             # Human-readable status message
```

For simple tools (like `GetDateAndTimeTool`), `execute()` returns a single `ToolResult` with state `COMPLETED`.

For future long-running tools (like an Orchestrator call or a database search), the tool can emit intermediate state via a progress callback:

```python
async def execute(self, input_data: dict[str, Any]) -> ToolResult:
    await self.emit_progress("Searching the database...")
    results: list[dict[str, Any]] = await self._search(input_data["query"])
    return ToolResult(
        state=ToolState.COMPLETED,
        data={"results": results},
        message=f"Found {len(results)} matching records.",
    )
```

The progress callback is wired by the `ToolProcessor` when it executes the tool. Progress events are translated into `TOOL_PROGRESS` session events that the provider can use to:
1. Send progress information to the client (for UI display).
2. Inject a system message into the LLM context so the agent can vocally narrate progress (e.g., "I've started searching for that, give me a moment...").

## ToolProcessor

```python
class ToolProcessor:
    """Registry and dispatcher for tools."""

    def register(self, tool: BaseTool) -> None:
        """Register a tool. Raises ValueError if name already registered."""
        ...

    def get_tool_specs(self, format: str = "generic") -> list[dict[str, Any]]:
        """Return tool specifications, optionally filtered by enabled tools.

        Args:
            format: Spec format. "generic" returns raw schema.
                    Provider-specific formats handled by providers.
        """
        ...

    def get_enabled_specs(
        self, enabled_tools: list[str], format: str = "generic"
    ) -> list[dict[str, Any]]:
        """Return specs only for the named tools."""
        ...

    async def execute(
        self,
        tool_name: str,
        input_data: dict[str, Any],
        on_progress: Callable[[str], Awaitable[None]] | None = None,
    ) -> ToolResult:
        """Execute a tool by name.

        Args:
            tool_name: The tool to execute (case-insensitive).
            input_data: Input parameters matching the tool's input_schema.
            on_progress: Optional callback for intermediate progress messages.

        Returns:
            ToolResult with COMPLETED or FAILED state.

        Raises:
            KeyError: If tool_name is not registered.
        """
        ...
```

### Provider-Specific Tool Spec Formatting

The `ToolProcessor.get_tool_specs()` returns a generic format:

```python
{
    "name": "getDateAndTimeTool",
    "description": "Get the current date and time",
    "input_schema": {"type": "object", "properties": {}, "required": []}
}
```

Each provider is responsible for converting this generic format into its API-specific format:

**Bedrock Nova Sonic**:
```json
{
    "toolSpec": {
        "name": "getDateAndTimeTool",
        "description": "Get the current date and time",
        "inputSchema": {
            "json": "{\"type\": \"object\", \"properties\": {}, \"required\": []}"
        }
    }
}
```

**Google ADK** (future):
```python
# Google ADK uses its own Tool/FunctionDeclaration classes
FunctionDeclaration(
    name="getDateAndTimeTool",
    description="Get the current date and time",
    parameters={"type": "object", "properties": {}, "required": []},
)
```

This approach keeps the tool framework provider-agnostic while allowing each provider to use its native format.

## Built-In Tools

### GetDateAndTimeTool

Ported from the PoC. Returns the current date and time with timezone information.

```python
class GetDateAndTimeTool(BaseTool):
    name = "getDateAndTimeTool"
    description = "Get information about the current date and time"
    input_schema = {"type": "object", "properties": {}, "required": []}

    async def execute(self, input_data: dict[str, Any]) -> ToolResult:
        now: datetime = datetime.now(tz=UTC)
        return ToolResult(
            state=ToolState.COMPLETED,
            data={
                "current_time": now.strftime("%H:%M:%S"),
                "current_date": now.strftime("%Y-%m-%d"),
                "day_of_week": now.strftime("%A"),
                "timezone": "UTC",
            },
        )
```

## Future Tools

The tool framework is designed to support increasingly complex tools as new agent types are added.

### Near-Term Tools

| Tool | Agent(s) | Description |
|------|----------|-------------|
| `checkAvailability` | Scheduler | Query calendar API for available time slots |
| `createEvent` | Scheduler | Create a calendar event |
| `searchRecords` | Avature Assistant | Search Avature records (person, company, object) |
| `getRecordDetails` | Avature Assistant | Fetch details of a specific Avature record |

### Long-Term Tools

| Tool | Description |
|------|-------------|
| `webSearch` | Search the web for information |
| `orchestratorCall` | Call the Avature Orchestrator for complex multi-step workflows |

### Orchestrator Integration

The Avature Orchestrator is a long-running external service. Its integration will use the async tool pattern:

1. The `OrchestratorTool.execute()` sends a request to the Orchestrator API.
2. It polls for completion (or uses a webhook callback), emitting `PROGRESS` results.
3. The provider injects progress messages as system messages to the LLM.
4. The LLM vocally narrates: "I'm working on that for you, it should just take a moment..."
5. When the Orchestrator returns, the tool emits a `COMPLETED` result.
6. The provider sends the result back to the voice model, which incorporates it into the conversation.

This keeps the conversation flowing naturally while long-running operations complete in the background.

## Tool Registration

Tools are registered at application startup in the FastAPI lifespan handler:

```python
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    tool_processor: ToolProcessor = ToolProcessor()
    tool_processor.register(GetDateAndTimeTool())
    # Future: tool_processor.register(CheckAvailabilityTool())
    app.state.tool_processor = tool_processor
    yield
```

Agent definitions reference tools by name. The provider retrieves the `ToolProcessor` from app state and uses `get_enabled_specs(agent.enabled_tools)` to get only the tools the current agent is allowed to use.
