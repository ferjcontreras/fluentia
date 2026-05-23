# Phase 3: Tool Transparency

## Problem Statement

When a voice model invokes a tool during a conversation (e.g., checking the current date and time), the user has no visibility into what happened. The model pauses briefly, the tool executes server-side, and the model resumes speaking -- but from the user's perspective, there is an unexplained silence or delay.

The backend already emits `TOOL_STARTED`, `TOOL_COMPLETED`, and `TOOL_FAILED` events over the WebSocket. The Event Console displays them as raw log lines if the user happens to have it open. But there is no dedicated, user-friendly representation of tool activity.

This matters because:
- Users cannot distinguish a tool-use pause from a model hesitation or network lag.
- Developers and prompt authors debugging agent behavior need to see what tools were called, with what inputs, and what they returned.
- As the platform gains more tools (Phase 4-5), opaque tool execution will become increasingly confusing.

## Objectives

1. **Visible tool activity**: Users see when a tool is invoked, what it is doing, and what it returned, in a dedicated UI element.
2. **Non-intrusive by default**: Tool activity is visible but does not dominate the conversation experience. It integrates naturally with the existing conversation-center layout.
3. **Real-time feedback**: Tool events are displayed as they arrive, not retroactively.
4. **Duration tracking**: Users see how long each tool execution took.

## Scope

### In scope

- Tool Activity panel in the Conversation tab (toggleable, like Transcript and Console)
- Rendering of `tool_started`, `tool_completed`, `tool_failed` events with structured display
- Duration calculation (time between `tool_started` and completion/failure)
- Tool input parameters display (sanitized)
- Tool result display
- Inline notification in the conversation center during tool execution (subtle indicator near the state indicator)

### Out of scope

- Tool configuration or toggle UI (Phase 4)
- New tool implementations (separate work; though we discuss a city-time tool as a concrete example)
- Changes to the tool framework or provider code (the events already exist)
- Prompt preview (Phase 2)

## Success Criteria

1. During a Bedrock session where the model calls `getDateAndTimeTool`, the user sees a tool activity card appear showing the tool name, a spinner, and then the result with duration.
2. The Tool Activity panel can be toggled on/off independently of the Transcript and Console panels.
3. Tool events that arrive while the panel is hidden are buffered and displayed when the panel is opened.
4. A conversation center notification briefly appears during tool execution (e.g., "Using getDateAndTimeTool...") and disappears when the tool completes.

## Design Documents

| Document | Contents |
|----------|----------|
| [summary.md](summary.md) | Design intuition, key decisions, trade-offs |
| [detailed-design.md](detailed-design.md) | Component specifications, event handling, state management |
| [details-frontend.md](details-frontend.md) | UI layout, tool card design, CSS, interaction details |
| [details-tool-example.md](details-tool-example.md) | City time tool: a concrete example to validate the design |
