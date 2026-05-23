# Summary: Design Intuition and Key Decisions

## Core Insight

The two problems (Google tool support and tool configurability) are entangled. Solving Google tool support requires a bridge between Fluentia's `BaseTool` abstraction and ADK's function-based tool model. Once that bridge exists, both providers have parity, and a unified tool catalog becomes meaningful to show in the UI.

## Key Decisions

### 1. Bridge BaseTool to ADK via wrapper functions, not ADK's native FunctionTool

Google ADK accepts tools as plain Python functions with type hints and docstrings. ADK inspects the function signature to build the tool schema automatically. Our `BaseTool` abstraction uses a different model: an `input_schema` JSON Schema property and an async `execute()` method.

Two bridge strategies:

- **Option A**: For each `BaseTool`, generate a Python function whose signature matches the tool's `input_schema`, and whose body calls `tool.execute()`. Pass these generated functions to `Agent(tools=[...])`.
- **Option B**: Use ADK's `FunctionTool` class to wrap a generic callable, providing the schema explicitly.

We choose **Option A** for Fluentia-defined tools and use **ADK built-in tools directly** (like `google_search`) when available. The wrapper function approach is the most natural for ADK and ensures ADK's internal tool handling (schema inference, argument marshalling) works correctly.

For the wrapper, we create a factory function that produces an `async def` with a `**kwargs` signature and proper docstring. ADK uses the docstring as the tool description and `**kwargs` for flexible input. The wrapper calls `tool.execute(kwargs)` internally.

### 2. Tool lifecycle events are emitted by the Google provider, not by ADK

ADK handles tool execution internally when using `runner.run_live()`. The runner receives a tool call from the model, executes the function, and sends the result back -- all opaque to our code. ADK events do not include explicit "tool started" / "tool completed" signals in the event stream.

This means we cannot emit `TOOL_STARTED`/`TOOL_COMPLETED` events from the Google provider the same way Bedrock does (where we intercept the tool call, execute manually, and emit events).

Two approaches:

- **Option A**: Intercept tool execution by wrapping each tool function with a before/after callback that emits events via the session context.
- **Option B**: Use ADK's `before_tool_callback` and `after_tool_callback` hooks on the Agent.

We choose **a combination**: wrap each tool function to emit `TOOL_STARTED` before calling `execute()` and `TOOL_COMPLETED`/`TOOL_FAILED` after. The wrapper has access to the `SessionContext.emit` callback via closure. This gives us the same event protocol as Bedrock without requiring changes to ADK's runner or relying on undocumented ADK callback behavior.

### 3. google_search is a special case: a provider-specific built-in tool

Google's `google_search` tool is an ADK built-in that calls Google's search API directly. It has no Fluentia `BaseTool` equivalent -- it is not a Python function we wrote. It only works with the Google provider.

We handle this as a **provider-specific tool** that appears in the tool catalog with a "Google only" badge. When the user selects the Bedrock provider, `google_search` is automatically disabled and its toggle is grayed out.

This introduces the concept of provider-scoped tools in the UI without adding provider logic to the tool framework itself. The backend simply does not include provider-specific tools when building the tool list for other providers.

### 4. Tool toggles are session-level overrides, not agent modifications

The agent's `enabled_tools` list defines the defaults. The Settings UI shows these tools as enabled by default. The user can toggle individual tools off (or on, if additional registered tools exist that the agent does not enable by default).

The resulting tool list is sent in the `prompt_config` message as `enabled_tools: [...]`. The `SessionManager` passes this to the provider, which uses it instead of the agent's default list.

This is a session-level override. It does not modify the `AgentDefinition`. Refreshing the page resets to agent defaults.

### 5. Tool metadata is served alongside agent metadata, not as a separate endpoint

Rather than a separate `GET /api/tools` endpoint, we extend the `/api/agents` response to include tool information per agent. Each agent's response includes a `tools` array with name, description, enabled-by-default status, and provider restrictions.

This keeps the frontend's data model simple: one fetch, one cache, all information about agents and their tools together. The frontend does not need to cross-reference two endpoints.

### 6. GetCityTimeTool is the second built-in tool

The city time tool (designed in the Phase 3 spec) is implemented here. It validates the multi-tool experience: an agent with two tools, both visible in the tool catalog, both executable by either provider.

## Trade-offs

| Decision | Benefit | Cost |
|----------|---------|------|
| Wrapper functions for ADK | Natural ADK integration, schema inference works | Wrapper generation code adds complexity |
| Event emission in wrapper | Same event protocol as Bedrock | Slightly couples wrapper to SessionContext |
| google_search as provider-specific | Access to Google's search API | Asymmetric tool availability between providers |
| Tool toggles in prompt_config | No backend state for preferences | Resets on page refresh |
| Tool metadata in /api/agents | Single fetch, cohesive data model | Larger agent response payload |
| Hardcoded city map | Zero dependencies, predictable | Limited city coverage |

## Risks

1. **ADK tool execution opacity**: If ADK changes how it handles tool functions (e.g., parallel execution, retry logic), our wrapper's event emission could produce incorrect STARTED/COMPLETED sequences. Mitigation: integration tests verify the event sequence.

2. **ADK event format for tool use**: ADK may emit tool-use related events in its event stream that we currently ignore in `_convert_adk_event()`. If these events contain useful information (tool name, result), we should parse them. Mitigation: log unhandled ADK events during development to discover tool-related fields.

3. **google_search rate limits**: Google Search API has usage limits. If the tool is enabled by default, users could hit limits quickly. Mitigation: `google_search` is disabled by default; users opt in via the toggle.
