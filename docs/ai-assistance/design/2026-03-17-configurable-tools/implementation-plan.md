# Plan: Configurable Tools (Phase 4)

## Context

Fluentia has two tool-related gaps: (1) Google provider passes `tools=[]` to ADK, so no tool calls work with Gemini, and (2) users cannot see or toggle tools from the UI. This plan implements the full Phase 4 spec from `docs/ai-assistance/design/2026-03-17-configurable-tools/`.

## Implementation Steps

### Step 1: BaseTool — add `display_name` property
**File**: `src/fluentia/tools/base.py`
- Add non-abstract `display_name` property that defaults to `self.name`
- Override in `GetDateAndTimeTool` to return `"Date & Time"`

### Step 2: GetCityTimeTool implementation
**Files**: `src/fluentia/tools/implementations/city_time.py` (new), `src/fluentia/tools/implementations/__init__.py`
- ~35 major cities in `CITY_TIMEZONES` dict mapping city names to IANA timezones
- Uses `zoneinfo.ZoneInfo` (stdlib)
- Input schema: `{"city": str}`, case-insensitive lookup
- Returns `{city, timezone, current_time, current_date, day_of_week}`
- Returns `FAILED` for unknown cities
- Export from `__init__.py`

### Step 3: Google ADK tool bridge
**File**: `src/fluentia/providers/google_tools.py` (new)
- `create_adk_tool_wrapper(tool, emit)` factory function
- Generates async `**kwargs` wrapper with `__name__` = tool.name, `__doc__` = tool.description
- Emits `TOOL_STARTED` before execution, `TOOL_COMPLETED`/`TOOL_FAILED` after
- Uses `uuid4()` for `tool_use_id`

### Step 4: GoogleProvider — accept ToolProcessor and build ADK tools
**File**: `src/fluentia/providers/google.py`
- Constructor gains `tool_processor: ToolProcessor` parameter
- New `_build_adk_tools(enabled_tools, emit)` method:
  - Iterates enabled tools, skips `"google_search"` (handled separately)
  - Looks up each in `self._tool_processor._tools` (case-insensitive)
  - Creates wrapper via `create_adk_tool_wrapper()`
- In `handle_session()`: build `adk_tools` list, optionally append `google_search` ADK built-in
- Pass `tools=adk_tools` to `Agent()`

### Step 5: SessionManager — extract `enabled_tools` from prompt_config
**File**: `src/fluentia/session/manager.py`
- In `_receive_prompt_config()`: extract `enabled_tools` list from data, return it alongside variables
  - Change return type to a tuple or a small dataclass/dict with both `variables` and `enabled_tools`
- In `handle_websocket()`: if `enabled_tools` is not None, override `agent_def.enabled_tools` when creating the new `AgentDefinition`

### Step 6: /api/agents — extend response with tool metadata
**File**: `src/fluentia/app.py`
- Define `PROVIDER_TOOLS` constant for provider-specific tools (`google_search`)
- Add `build_agent_tools(agent, tool_processor)` helper function
- Extend `/api/agents` response: each agent gains `"tools": [...]` with `name`, `display_name`, `description`, `enabled_by_default`, `provider_restriction`
- Register `GetCityTimeTool` in lifespan
- Pass `tool_processor` to `GoogleProvider` constructor
- Update interviewer agent's `enabled_tools` to include `"getCityTimeTool"`

### Step 7: Frontend — tool toggles in Settings tab
**Files**: `src/fluentia/static/index.html`, `src/fluentia/static/js/app.js`, `src/fluentia/static/css/styles.css`

**HTML** (`index.html`):
- Add "Tools" section between Configuration and hint text in `.settings-column-left`
- Container div `#toolTogglesContainer`

**JS** (`app.js`):
- `buildToolToggles(agent, currentProvider)` — generates toggle rows from `agent.tools`
- `collectEnabledTools()` — returns list of checked tool names
- Update `sendPromptConfig()` to include `enabled_tools`
- Call `buildToolToggles()` from `selectAgent()` and on provider change
- Provider change: preserve non-restricted toggle states, disable restricted tools
- `setSettingsLocked()`: also disable tool toggle checkboxes during session

**CSS** (`styles.css`):
- `.tools-section`, `.tool-toggle`, `.tool-toggle-switch`, `.toggle-slider`, `.tool-toggle-info`, `.tool-toggle-name`, `.tool-toggle-desc`, `.tool-toggle-badge`, `.tools-empty`
- iOS-style toggle switch

### Step 8: Agent definitions — update enabled_tools
**Files**: `src/fluentia/agents/interviewer.py`, `src/fluentia/agents/qa_assistant.py`
- Interviewer: `enabled_tools=["getDateAndTimeTool", "getCityTimeTool"]`
- QA assistant: leave as `[]` (no tools by default)

### Step 9: Unit tests
**New test files**:
- `tests/unit/tools/test_city_time.py` — known city, unknown city, empty input, case insensitivity, metadata
- `tests/unit/providers/test_google_tools.py` — wrapper metadata, execution, TOOL_STARTED/COMPLETED/FAILED events, error handling

**Modified test files**:
- `tests/unit/providers/test_google.py` — update `_make_provider()` to pass `tool_processor`, add test for `_build_adk_tools`
- `tests/unit/session/test_manager.py` — test prompt_config with `enabled_tools` override
- `tests/unit/tools/test_processor.py` — test `display_name` default behavior

### Step 10: CODEMAP update
**File**: `.claude/CODEMAP.md`
- Add `src/fluentia/providers/google_tools.py` under Providers
- Add `src/fluentia/tools/implementations/city_time.py` under Tools

## Key Files to Modify

| File | Change |
|------|--------|
| `src/fluentia/tools/base.py` | Add `display_name` property |
| `src/fluentia/tools/implementations/city_time.py` | **New** — GetCityTimeTool |
| `src/fluentia/tools/implementations/__init__.py` | Export GetCityTimeTool |
| `src/fluentia/providers/google_tools.py` | **New** — ADK tool wrapper factory |
| `src/fluentia/providers/google.py` | Accept ToolProcessor, build ADK tools |
| `src/fluentia/session/manager.py` | Extract enabled_tools from prompt_config |
| `src/fluentia/app.py` | Register city time tool, pass tool_processor to Google, extend /api/agents |
| `src/fluentia/agents/interviewer.py` | Add getCityTimeTool to enabled_tools |
| `src/fluentia/static/index.html` | Add tools section HTML |
| `src/fluentia/static/js/app.js` | Tool toggle logic |
| `src/fluentia/static/css/styles.css` | Toggle switch styles |
| `.claude/CODEMAP.md` | Add new files |

## Reusable Patterns

- **Tool registration**: follows existing `ToolProcessor.register()` pattern (`app.py:50-51`)
- **Tool implementation**: follows `GetDateAndTimeTool` pattern (`tools/implementations/date_time.py`)
- **Test patterns**: `DummyTool`/`FailingTool` from `test_processor.py`, mock ADK events from `test_google.py`
- **Settings form**: follows `buildSettingsForm()` pattern in `app.js:66-114`
- **AgentDefinition override**: follows existing `AgentDefinition()` copy pattern in `manager.py:76-85`
- **Provider constructor with ToolProcessor**: follows `BedrockProvider.__init__()` pattern

## Verification

1. `./check_code.sh` — ruff format, ruff check, mypy, pylint
2. `uv run pytest` — all unit tests pass
3. `uv run tox` — full quality gate before committing
4. Manual: start app, select interviewer agent, verify tools appear in Settings tab, toggle tools, start Google session, ask "What time is it in Tokyo?"
