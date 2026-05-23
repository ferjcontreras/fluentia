# Detailed Design: Component Specifications

## No Backend Changes

Phase 3 requires zero backend modifications. The Bedrock provider already emits all four tool lifecycle events (`TOOL_STARTED`, `TOOL_PROGRESS`, `TOOL_COMPLETED`, `TOOL_FAILED`) with structured payloads. The WebSocket protocol already defines these event types. The frontend currently logs them to the Event Console but does not render them as a dedicated UI.

All work is in `static/js/app.js`, `static/css/styles.css`, and `static/index.html`.

---

## Event Payloads (existing, no changes)

These are the events the frontend already receives. Documented here for reference.

### tool_started

```json
{
  "v": 1,
  "type": "tool_started",
  "payload": {
    "tool_id": "abc-123",
    "tool_name": "getDateAndTimeTool"
  },
  "ts": "2026-03-17T14:30:00+00:00"
}
```

### tool_progress

```json
{
  "v": 1,
  "type": "tool_progress",
  "payload": {
    "tool_name": "getDateAndTimeTool",
    "message": "Processing..."
  },
  "ts": "2026-03-17T14:30:01+00:00"
}
```

### tool_completed

```json
{
  "v": 1,
  "type": "tool_completed",
  "payload": {
    "tool_id": "abc-123",
    "tool_name": "getDateAndTimeTool",
    "result": {
      "current_time": "14:30:00",
      "current_date": "2026-03-17",
      "day_of_week": "Tuesday",
      "timezone": "UTC"
    }
  },
  "ts": "2026-03-17T14:30:00.150+00:00"
}
```

### tool_failed

```json
{
  "v": 1,
  "type": "tool_failed",
  "payload": {
    "tool_id": "abc-123",
    "tool_name": "getDateAndTimeTool",
    "error": "Tool execution failed: timeout"
  },
  "ts": "2026-03-17T14:30:05+00:00"
}
```

---

## Client-Side State Model

### Tool Invocation Record

Each tool invocation is tracked as a JavaScript object:

```javascript
{
  toolId: "abc-123",           // From tool_started payload
  toolName: "getDateAndTimeTool",
  state: "running",            // "running" | "completed" | "failed"
  startTime: 1742219400000,    // performance.now() at tool_started
  endTime: null,               // performance.now() at completion/failure
  duration: null,              // endTime - startTime (ms)
  progressMessage: null,       // Latest tool_progress message
  result: null,                // From tool_completed payload
  error: null,                 // From tool_failed payload
  cardElement: null,           // DOM reference for in-place updates
}
```

### Invocation Buffer

```javascript
let toolInvocations = [];       // All invocations in current session
let activeToolId = null;        // Currently running tool (for notification)
```

The buffer is cleared on `session_end` event (same as transcript clearing).

---

## Event Handling (additions to app.js switch statement)

### tool_started

```javascript
case "tool_started": {
  const invocation = {
    toolId: payload.tool_id,
    toolName: payload.tool_name,
    state: "running",
    startTime: performance.now(),
    endTime: null,
    duration: null,
    progressMessage: null,
    result: null,
    error: null,
    cardElement: null,
  };
  toolInvocations.push(invocation);
  activeToolId = payload.tool_id;

  // Render card if panel is visible
  if (toolActivityVisible) {
    invocation.cardElement = createToolCard(invocation);
    toolActivityContent.appendChild(invocation.cardElement);
    toolActivityContent.scrollTop = toolActivityContent.scrollHeight;
  }

  // Show conversation-center notification
  showToolNotification(payload.tool_name);

  addConsoleEntry('incoming', `Tool started: ${payload.tool_name}`, payload);
  break;
}
```

### tool_progress

```javascript
case "tool_progress": {
  // Find the active invocation (tool_progress does not carry tool_id,
  // so match by tool_name against the latest running invocation)
  const invocation = findRunningInvocation(payload.tool_name);
  if (invocation) {
    invocation.progressMessage = payload.message;
    if (invocation.cardElement) {
      updateToolCardProgress(invocation.cardElement, payload.message);
    }
  }
  addConsoleEntry('incoming', `Tool progress: ${payload.message}`, payload);
  break;
}
```

### tool_completed

```javascript
case "tool_completed": {
  const invocation = findInvocationById(payload.tool_id);
  if (invocation) {
    invocation.state = "completed";
    invocation.endTime = performance.now();
    invocation.duration = Math.round(invocation.endTime - invocation.startTime);
    invocation.result = payload.result;

    if (invocation.cardElement) {
      updateToolCardCompleted(invocation);
    } else if (toolActivityVisible) {
      // Panel was opened after tool started; render the complete card
      invocation.cardElement = createToolCard(invocation);
      toolActivityContent.appendChild(invocation.cardElement);
    }
  }

  if (activeToolId === payload.tool_id) {
    activeToolId = null;
    hideToolNotification();
  }

  addConsoleEntry('incoming', `Tool completed: ${payload.tool_name}`, payload);
  break;
}
```

### tool_failed

```javascript
case "tool_failed": {
  const invocation = findInvocationById(payload.tool_id);
  if (invocation) {
    invocation.state = "failed";
    invocation.endTime = performance.now();
    invocation.duration = Math.round(invocation.endTime - invocation.startTime);
    invocation.error = payload.error;

    if (invocation.cardElement) {
      updateToolCardFailed(invocation);
    } else if (toolActivityVisible) {
      invocation.cardElement = createToolCard(invocation);
      toolActivityContent.appendChild(invocation.cardElement);
    }
  }

  if (activeToolId === payload.tool_id) {
    activeToolId = null;
    hideToolNotification();
  }

  addConsoleEntry('incoming', `Tool failed: ${payload.tool_name} - ${payload.error}`, payload);
  break;
}
```

### Helper Functions

```javascript
function findInvocationById(toolId) {
  return toolInvocations.find(inv => inv.toolId === toolId) || null;
}

function findRunningInvocation(toolName) {
  // Find the most recent running invocation matching the tool name
  for (let i = toolInvocations.length - 1; i >= 0; i--) {
    if (toolInvocations[i].toolName === toolName && toolInvocations[i].state === "running") {
      return toolInvocations[i];
    }
  }
  return null;
}
```

---

## Panel Lifecycle

### Opening the Tool Activity Panel

When the user toggles the panel open:

1. Show the `toolActivityPanel` element.
2. If `toolInvocations` contains entries that have no `cardElement` (buffered while panel was closed), render cards for each and append to the panel.
3. Scroll to bottom.

```javascript
function setToolActivityVisible(visible) {
  toolActivityVisible = visible;
  toolActivityPanel.classList.toggle("hidden", !visible);
  toggleToolActivityBtn.classList.toggle("active", visible);

  if (visible) {
    // Render any buffered invocations
    for (const inv of toolInvocations) {
      if (!inv.cardElement) {
        inv.cardElement = createToolCard(inv);
        toolActivityContent.appendChild(inv.cardElement);
      }
    }
    toolActivityContent.scrollTop = toolActivityContent.scrollHeight;
  }
}
```

### Session End

On `session_end` event:
- Clear `toolInvocations` array.
- Clear `toolActivityContent` innerHTML.
- Reset `activeToolId`.
- Hide any active notification.

---

## Conversation-Center Notification

A small notification element sits below the state label in the conversation center. It is hidden by default and shown only during tool execution.

```html
<div class="tool-notification hidden" id="toolNotification">
  <span class="tool-notification-spinner"></span>
  <span class="tool-notification-text" id="toolNotificationText"></span>
</div>
```

```javascript
function showToolNotification(toolName) {
  toolNotificationText.textContent = `Using ${toolName}...`;
  toolNotification.classList.remove("hidden");
}

function hideToolNotification() {
  toolNotification.classList.add("hidden");
}
```

The notification auto-hides when `tool_completed` or `tool_failed` is received for the active tool. If a new tool starts while the previous is still running (unlikely but possible), the notification updates to show the new tool name.
