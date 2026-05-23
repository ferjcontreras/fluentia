# Phase 4: Configurable Tools and Google ADK Tool Support

## Problem Statement

Fluentia has two tool-related gaps:

1. **Google provider has no tool support.** The Bedrock provider executes tools via `ToolProcessor` and emits tool lifecycle events. The Google provider passes `tools=[]` to the ADK Agent (`src/fluentia/providers/google.py:77`). A user asking "What time is it?" to Google Gemini gets a guess; the same question to Bedrock gets an accurate answer from `getDateAndTimeTool`.

2. **Tool configuration is invisible.** Users cannot see which tools an agent has, enable or disable them per session, or understand what tools do. The agent's `enabled_tools` list is opaque, set at registration time.

Phase 4 closes both gaps: it wires tools into the Google provider and gives users a UI to discover and toggle tools.

## Objectives

1. **Google ADK tool execution**: The Google provider executes Fluentia tools during voice sessions, with the same lifecycle events as Bedrock.
2. **Tool configuration UI**: Users see which tools are available for the selected agent and can toggle them on/off before starting a session.
3. **New tools**: At least one new tool (city time) to demonstrate multi-tool agents.
4. **Provider parity**: Both providers support the same tool set, with the same event protocol.

## Scope

### In scope

- Google ADK tool integration (bridge `BaseTool` to ADK function tools)
- Tool lifecycle events from Google provider (`TOOL_STARTED`, `TOOL_COMPLETED`, `TOOL_FAILED`)
- Tool catalog in Settings tab (list of tools with toggle switches)
- `enabled_tools` override in `prompt_config` WebSocket message
- `GET /api/tools` endpoint (or extend `/api/agents` with tool metadata)
- `GetCityTimeTool` implementation (described in Phase 3 spec, built here)
- Google built-in tool integration (`google_search`)

### Out of scope

- Tool creation at runtime (tools are code-defined)
- Tool progress events from Google (ADK does not emit progress for built-in tools)
- Orchestrator tool (Phase 5)
- Tool Activity panel (Phase 3, assumed complete)

## Prerequisites

- Phase 2 (dynamic settings form) should be complete -- the tool toggle UI builds on the dynamic form pattern.
- Phase 3 (Tool Activity panel) should be complete -- users need to see tool events from the Google provider.

## Success Criteria

1. During a Google Gemini session, the model can call `getDateAndTimeTool` and `getCityTimeTool`, producing correct results and visible tool lifecycle events.
2. The Tool Activity panel shows the same card structure for Google tool invocations as for Bedrock.
3. The Settings tab shows a "Tools" section listing available tools for the selected agent, each with a toggle switch.
4. Disabling a tool removes it from the session; the model cannot call it.
5. Adding a new tool (registering in `app.py`, adding to an agent's `enabled_tools`) makes it appear in the Settings UI automatically.

## Design Documents

| Document | Contents |
|----------|----------|
| [summary.md](summary.md) | Design intuition, key decisions, trade-offs |
| [detailed-design.md](detailed-design.md) | Component specifications, API contracts |
| [details-google-tools.md](details-google-tools.md) | Google ADK tool bridge, event conversion, architecture |
| [details-frontend.md](details-frontend.md) | Tool catalog UI, toggle behavior, Settings tab changes |
