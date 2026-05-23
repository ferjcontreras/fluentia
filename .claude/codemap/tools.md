# Tool Execution Framework

## Overview

The tool system allows LLM and speech models to invoke external functions during conversations. Tools are defined as classes extending `BaseTool`, registered with a `ToolProcessor`, and their JSON schemas are passed to models. During voice conversations, the SpeechCaller automatically executes tools and returns results to the model.

---

## BaseTool (Abstract Interface)

**File**: `src/fluentia/tools/base.py`

- `ToolConfig(BaseModel)` (line 11): Configuration
  - `enabled_tools`: list[str] -- names of tools to enable
- `BaseTool(ABC)` (line 24): Abstract base for all tools
  - `name` (property, abstract): Tool identifier string
  - `description` (property, abstract): Human-readable description for the model
  - `input_schema` (property, abstract): JSON Schema dict defining expected input
  - `execute(input_data)` (async, abstract): Perform the tool's action
  - `to_tool_spec()`: Generates the complete tool specification dict for model APIs

---

## ToolProcessor (Registry & Dispatcher)

**File**: `src/fluentia/tools/processor.py`

- `ToolProcessor` (line 12): Central tool manager
  - `register_tool(tool)`: Add a tool to the registry
  - `get_tool(name)`: Retrieve a registered tool by name
  - `get_enabled_tool_specs(config)`: Get JSON specs for enabled tools only
  - `get_all_tool_specs()`: Get JSON specs for all registered tools
  - `execute_tool(name, input_data)` (async): Look up and execute a tool by name
  - `registered_tools` (property): Dict of all registered tools
  - `enabled_tools` (property): List of currently enabled tool names

---

## Built-in Implementations

### GetDateAndTimeTool
**File**: `src/fluentia/tools/implementations/date_time.py`

- `GetDateAndTimeTool(BaseTool)` (line 11)
  - Name: "get_date_and_time"
  - Input: Empty schema (no parameters needed)
  - Output: dict with formattedTime, date, year, month, day, dayOfWeek, timezone
  - Uses pytz for timezone handling

---

## Adding a New Tool

1. Create a new file in `src/fluentia/tools/implementations/`
2. Define a class extending `BaseTool`
3. Implement `name`, `description`, `input_schema`, and `execute()`
4. Register it with `ToolProcessor.register_tool()` in the voice agent setup

---

## Integration with Speech

Tools are used during voice conversations via `SpeechCaller`:
- Tool specs are passed to `SpeechCaller.connect()` when starting a conversation
- When the model requests a tool, `SpeechCaller._handle_tool_use()` dispatches execution
- Results are sent back via `send_tool_result()`
- See `src/fluentia/modules/speech_caller.py:79` for the integration logic
