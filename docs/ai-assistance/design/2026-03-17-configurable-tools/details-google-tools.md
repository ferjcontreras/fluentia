# Google ADK Tool Bridge

## Current State

The Google provider creates an ADK Agent with an empty tools list:

```python
# src/fluentia/providers/google.py:76-78
agent: Agent = Agent(
    name="voice_agent", model=self._config.model_name, tools=[], instruction=prompt
)
```

The Bedrock provider, by contrast, receives a `ToolProcessor` at construction time and uses it to execute tools during the session (`_handle_tool_call()`).

## How ADK Tools Work

From the Google ADK samples, tools in ADK are:

1. **Plain Python functions** with type hints and docstrings:
   ```python
   def get_weather(city: str) -> dict:
       """Get current weather for a city."""
       return {"temp": 22, "condition": "sunny"}

   agent = Agent(tools=[get_weather], ...)
   ```

2. **Built-in toolsets** imported from `google.adk.tools`:
   ```python
   from google.adk.tools import google_search
   agent = Agent(tools=[google_search], ...)
   ```

ADK inspects the function's signature, docstring, and type hints to build the tool schema automatically. When the model decides to call a tool, ADK's runner executes the function and sends the result back to the model -- all transparently within `runner.run_live()`.

## Bridge Design

### Wrapper Function Factory

For each Fluentia `BaseTool`, we generate a wrapper async function that:
1. Emits `TOOL_STARTED` via the session context.
2. Calls `tool.execute(input_data)`.
3. Emits `TOOL_COMPLETED` or `TOOL_FAILED`.
4. Returns the result (so ADK can send it back to the model).

```python
def create_adk_tool_wrapper(
    tool: BaseTool,
    emit: Callable[[SessionEvent], Awaitable[None]],
) -> Callable[..., Awaitable[dict[str, Any]]]:
    """Create an ADK-compatible async function that wraps a BaseTool."""

    async def tool_wrapper(**kwargs: Any) -> dict[str, Any]:
        tool_use_id: str = str(uuid4())

        # Emit TOOL_STARTED
        await emit(SessionEvent(
            type=SessionEventType.TOOL_STARTED,
            payload={"tool_id": tool_use_id, "tool_name": tool.name},
        ))

        try:
            result: ToolResult = await tool.execute(kwargs)

            if result.state == ToolState.COMPLETED:
                await emit(SessionEvent(
                    type=SessionEventType.TOOL_COMPLETED,
                    payload={
                        "tool_id": tool_use_id,
                        "tool_name": tool.name,
                        "result": result.data or {},
                    },
                ))
                return result.data or {}
            else:
                await emit(SessionEvent(
                    type=SessionEventType.TOOL_FAILED,
                    payload={
                        "tool_id": tool_use_id,
                        "tool_name": tool.name,
                        "error": result.message or "Tool execution failed",
                    },
                ))
                return {"error": result.message or "Tool execution failed"}

        except Exception as e:
            await emit(SessionEvent(
                type=SessionEventType.TOOL_FAILED,
                payload={
                    "tool_id": tool_use_id,
                    "tool_name": tool.name,
                    "error": str(e),
                },
            ))
            return {"error": str(e)}

    # Set function metadata for ADK schema inference
    tool_wrapper.__name__ = tool.name
    tool_wrapper.__doc__ = tool.description

    return tool_wrapper
```

### Why **kwargs Instead of Typed Parameters

ADK infers the tool schema from function parameters. For tools with dynamic schemas (like `getCityTimeTool` with a `city` parameter), ideally we would generate a function with the exact typed signature. However:

- Generating typed functions dynamically is fragile and hard to maintain.
- ADK also accepts `**kwargs` and falls back to the tool's description for schema.
- We can optionally provide an explicit schema via ADK's `FunctionTool` if `**kwargs` proves insufficient.

For Phase 4, `**kwargs` with a good docstring is the pragmatic choice. If ADK's schema inference needs more, we can switch to `FunctionTool` with explicit `input_schema`.

### Alternative: ADK FunctionTool with Explicit Schema

If `**kwargs` does not produce good schema inference, we can use:

```python
from google.adk.tools import FunctionTool

def create_adk_function_tool(tool: BaseTool, emit: ...) -> FunctionTool:
    wrapper = create_adk_tool_wrapper(tool, emit)
    return FunctionTool(
        func=wrapper,
        name=tool.name,
        description=tool.description,
        # ADK may accept an explicit schema here
    )
```

This is a fallback. Try the simple wrapper first.

## Updated Google Provider

### Constructor Change

The Google provider now accepts a `ToolProcessor`, matching Bedrock:

```python
class GoogleProvider(BaseProvider):
    def __init__(
        self,
        provider_config: GoogleProviderConfig,
        tool_processor: ToolProcessor,
    ) -> None:
        self._config = provider_config
        self._tool_processor = tool_processor
        self._session_service = InMemorySessionService()
```

### handle_session Changes

In `handle_session()`, build the ADK tools list from the agent's enabled tools:

```python
async def handle_session(self, websocket: WebSocket, session_context: SessionContext) -> None:
    prompt: str = session_context.agent_definition.render_prompt()
    run_config: RunConfig = self._build_run_config(websocket)

    # Build ADK tool wrappers from Fluentia tools
    enabled_tools: list[str] = session_context.agent_definition.enabled_tools
    adk_tools: list[Any] = self._build_adk_tools(enabled_tools, session_context.emit)

    # Add google_search if enabled
    if "google_search" in enabled_tools:
        from google.adk.tools import google_search
        adk_tools.append(google_search)

    agent: Agent = Agent(
        name="voice_agent",
        model=self._config.model_name,
        tools=adk_tools,
        instruction=prompt,
    )
    # ... rest unchanged
```

### New Method: _build_adk_tools

```python
def _build_adk_tools(
    self,
    enabled_tools: list[str],
    emit: Callable[[SessionEvent], Awaitable[None]],
) -> list[Any]:
    """Build ADK-compatible tool wrappers from enabled Fluentia tools."""
    adk_tools: list[Any] = []
    for tool_name in enabled_tools:
        if tool_name == "google_search":
            continue  # Handled separately (ADK built-in)
        tool: BaseTool | None = self._tool_processor._tools.get(tool_name.lower())
        if tool:
            wrapper = create_adk_tool_wrapper(tool, emit)
            adk_tools.append(wrapper)
        else:
            logger.warning("Tool not found for Google ADK: %s", tool_name)
    return adk_tools
```

### Updated _convert_adk_event

ADK may emit tool-related information in its event stream. We should check for `toolUse` or `functionCall` fields in the event dict and log them. For built-in tools like `google_search` (where we cannot wrap with our event emitter), we may need to parse ADK events to emit `TOOL_STARTED`/`TOOL_COMPLETED`.

```python
def _convert_adk_event(self, adk_event: Any) -> list[SessionEvent]:
    events: list[SessionEvent] = []
    event_dict: dict[str, Any] = adk_event.model_dump(exclude_none=True, by_alias=True)

    # ... existing handlers for turnComplete, interrupted, transcription, audio ...

    # Handle tool-related ADK events (for built-in tools like google_search)
    if "toolCall" in event_dict or "functionCall" in event_dict:
        logger.debug("ADK tool event: %s", event_dict)
        # TODO: Parse and emit TOOL_STARTED/TOOL_COMPLETED for built-in tools

    return events
```

The exact shape of ADK tool events needs to be discovered during implementation (log and inspect). This is an open question.

## Registration in app.py

```python
# Providers now both receive tool_processor
providers: dict[str, BaseProvider] = {
    "google": GoogleProvider(
        provider_config=config.google,
        tool_processor=tool_processor,
    ),
    "bedrock": BedrockProvider(
        provider_config=config.bedrock,
        tool_processor=tool_processor,
    ),
}
```

## google_search as a Provider-Specific Tool

`google_search` is not a `BaseTool`. It is an ADK built-in that only works with Google. We handle it as a special case:

1. **Registration**: It is not registered in `ToolProcessor`. Instead, the Google provider recognizes the string `"google_search"` in `enabled_tools` and imports the ADK built-in.
2. **Tool catalog**: The `/api/agents` response includes `google_search` with a `provider: "google"` restriction. The frontend shows it grayed out when Bedrock is selected.
3. **Event emission**: Since we cannot wrap the built-in, tool events for `google_search` must come from parsing ADK events (open question, see above).

## Testing

| Test | Description |
|------|-------------|
| `test_create_adk_tool_wrapper` | Wrapper calls execute() and returns result |
| `test_wrapper_emits_tool_started` | TOOL_STARTED event emitted before execution |
| `test_wrapper_emits_tool_completed` | TOOL_COMPLETED emitted on success |
| `test_wrapper_emits_tool_failed` | TOOL_FAILED emitted on exception |
| `test_wrapper_handles_failed_result` | TOOL_FAILED emitted when ToolResult.state is FAILED |
| `test_build_adk_tools_filters_google_search` | google_search excluded from wrapper list |
| `test_google_provider_with_tools` | Integration: Google session with mocked tool execution |
