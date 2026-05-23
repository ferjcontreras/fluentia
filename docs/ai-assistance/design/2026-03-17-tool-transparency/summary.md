# Summary: Design Intuition and Key Decisions

## Core Insight

The infrastructure for tool transparency already exists. The backend emits structured tool lifecycle events (`TOOL_STARTED`, `TOOL_PROGRESS`, `TOOL_COMPLETED`, `TOOL_FAILED`) with tool name, ID, inputs, and results. The WebSocket protocol already defines these event types. Phase 3 is purely a frontend project: consuming events that the backend already sends and rendering them in a user-friendly way.

No backend changes are required.

## Key Decisions

### 1. Tool Activity is a third toggleable panel, not a new tab

The Conversation tab already has two toggleable panels (Transcript and Console) controlled by toolbar buttons. Tool Activity follows the same pattern: a toolbar button that opens a panel alongside the conversation center.

Alternatives considered:
- **A new top-level tab** (like Settings): Rejected because tool activity is conversation-scoped and makes no sense outside a session. Navigating away from the Conversation tab during a live session would feel wrong.
- **Inline in the transcript**: Rejected because tool events have structured data (inputs, outputs, duration) that would look cluttered between speech bubbles.
- **Inside the Event Console**: The Console already shows tool events as raw log lines. But the Console is a developer tool showing all events. Tool Activity is a focused, user-friendly view. They serve different audiences.

The three panels (Transcript, Tool Activity, Console) can be open simultaneously. The conversation center compresses to accommodate them.

### 2. Tool cards, not log lines

Each tool invocation is rendered as a "card" with distinct states:

- **Running**: Tool name, spinner, elapsed time counter.
- **Completed**: Tool name, result summary, duration badge, expandable details (inputs, full result JSON).
- **Failed**: Tool name, error message, duration badge, red accent.

This is more informative than a log line and more scannable when multiple tools fire in sequence.

### 3. Duration is computed client-side

The frontend records `performance.now()` when it receives `tool_started` and computes the delta when `tool_completed` or `tool_failed` arrives. This measures wall-clock time as perceived by the user (including network latency), which is more useful than server-side execution time.

The server-side execution time could also be sent in the event payload (future enhancement), but the client-side measurement is sufficient for Phase 3 and requires no backend changes.

### 4. A subtle conversation-center notification bridges the gap

Most users will not have the Tool Activity panel open. When a tool executes, a small notification appears below the state indicator in the conversation center: "Using getDateAndTimeTool..." with a subtle animation. It disappears when the tool completes.

This gives all users awareness of tool use without requiring the panel to be open. It explains the brief silence during tool execution.

### 5. Tool events are buffered even when the panel is hidden

If the Tool Activity panel is closed during a tool invocation, the events are still captured in a JavaScript array. When the user opens the panel, all past tool cards are rendered immediately. This ensures no information is lost.

The buffer is cleared when the session ends (same lifecycle as transcript messages).

### 6. Input parameters are shown but can be sanitized

Tool inputs are displayed in the expanded card view. For Phase 3, all inputs are shown as-is (the only tool is `getDateAndTimeTool` with no sensitive inputs). The design anticipates a future `sensitive_fields` property on tools that the frontend could use to redact values, but this is not implemented in Phase 3.

## Trade-offs

| Decision | Benefit | Cost |
|----------|---------|------|
| Third toggleable panel | Consistent with existing UI pattern | Screen space with 3 panels open is tight |
| Card-based rendering | Structured, scannable, expandable | More CSS/JS than simple log lines |
| Client-side duration | No backend changes, user-perceived timing | Includes network latency (feature, not bug) |
| Conversation-center notification | All users see tool activity | Another visual element in the center area |
| Event buffering | No lost information | Memory use grows with tool invocations per session |

## Risks

1. **Screen space**: With Transcript, Tool Activity, and Console all open, the conversation center becomes narrow. Mitigation: the conversation center has a minimum width; panels scroll vertically. Users are unlikely to have all three open simultaneously.

2. **Rapid tool invocations**: If a model calls multiple tools in quick succession, the panel could fill rapidly. Mitigation: cards are compact in their collapsed state; the panel scrolls. Not a concern for Phase 3 (one tool, called at most once per session).

3. **Tool progress events**: The `TOOL_PROGRESS` event type exists but no current tool emits it. The card design includes a progress state, but it is untestable until a long-running tool exists (Phase 5, Orchestrator). Mitigation: implement the rendering now, test it with a mock when Phase 5 arrives.
