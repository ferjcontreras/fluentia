# Frontend Details

## HTML Changes

### Toolbar Addition

Add a third toolbar button in the conversation toolbar, between Transcript and Console:

```html
<div class="conversation-toolbar">
  <button class="toolbar-toggle" id="toggleTranscript" title="Show transcript">
    <span class="toolbar-icon">&#x1F4AC;</span>
    <span class="toolbar-label">Transcript</span>
  </button>
  <button class="toolbar-toggle" id="toggleToolActivity" title="Show tool activity">
    <span class="toolbar-icon">&#x1F527;</span>
    <span class="toolbar-label">Tools</span>
  </button>
  <button class="toolbar-toggle" id="toggleConsole" title="Show event console">
    <span class="toolbar-icon">&#x2699;</span>
    <span class="toolbar-label">Console</span>
  </button>
</div>
```

### Tool Activity Panel

New panel inside the `main-layout` div, between the conversation center and the console panel:

```html
<div class="tool-activity-panel hidden" id="toolActivityPanel">
  <div class="panel-header">
    <span>Tool Activity</span>
    <button class="panel-close" id="closeToolActivity">&times;</button>
  </div>
  <div class="tool-activity-content" id="toolActivityContent"></div>
</div>
```

### Conversation-Center Notification

Inside the `conversation-center` div, after the state label:

```html
<div class="tool-notification hidden" id="toolNotification">
  <span class="tool-notification-spinner"></span>
  <span class="tool-notification-text" id="toolNotificationText"></span>
</div>
```

---

## Tool Card Design

Each tool invocation renders as a card. The card has three visual states.

### Running State

```
┌──────────────────────────────────────────┐
│  ⟳  getDateAndTimeTool          1.2s ... │
└──────────────────────────────────────────┘
```

- Spinner icon (CSS animation).
- Tool name in bold.
- Live elapsed time counter (updated via `requestAnimationFrame` or `setInterval`).

### Completed State

```
┌──────────────────────────────────────────┐
│  ✓  getDateAndTimeTool            152ms  │
│                                          │
│  current_time: "14:30:00"                │
│  current_date: "2026-03-17"              │
│  day_of_week: "Tuesday"                  │
│  timezone: "UTC"                          │
│                                    ▼ More │
└──────────────────────────────────────────┘
```

- Green checkmark icon.
- Tool name in bold.
- Duration badge (e.g., "152ms" or "2.3s").
- Result summary: key-value pairs from `result`, shown directly.
- "More" toggle to expand full JSON (inputs and raw result).

### Failed State

```
┌──────────────────────────────────────────┐
│  ✗  getDateAndTimeTool            5.0s   │
│                                          │
│  Tool execution failed: timeout          │
└──────────────────────────────────────────┘
```

- Red X icon.
- Tool name in bold.
- Duration badge.
- Error message from `error` field.

### Card DOM Structure

```javascript
function createToolCard(invocation) {
  const card = document.createElement("div");
  card.className = `tool-card tool-${invocation.state}`;
  card.dataset.toolId = invocation.toolId;

  // Header row: icon + name + duration
  const header = document.createElement("div");
  header.className = "tool-card-header";

  const icon = document.createElement("span");
  icon.className = "tool-card-icon";

  const name = document.createElement("span");
  name.className = "tool-card-name";
  name.textContent = invocation.toolName;

  const duration = document.createElement("span");
  duration.className = "tool-card-duration";

  header.appendChild(icon);
  header.appendChild(name);
  header.appendChild(duration);
  card.appendChild(header);

  // Body: result or error
  if (invocation.state === "completed" && invocation.result) {
    card.appendChild(createResultSummary(invocation.result));
  } else if (invocation.state === "failed" && invocation.error) {
    const errorDiv = document.createElement("div");
    errorDiv.className = "tool-card-error";
    errorDiv.textContent = invocation.error;
    card.appendChild(errorDiv);
  } else if (invocation.state === "running") {
    // Start elapsed time counter
    startElapsedCounter(duration, invocation.startTime);
  }

  if (invocation.state !== "running" && invocation.duration != null) {
    duration.textContent = formatDuration(invocation.duration);
  }

  return card;
}
```

### Result Summary Rendering

For completed tools, the result object is rendered as a compact key-value list:

```javascript
function createResultSummary(result) {
  const body = document.createElement("div");
  body.className = "tool-card-body";

  const entries = Object.entries(result);
  for (const [key, value] of entries) {
    const row = document.createElement("div");
    row.className = "tool-result-row";

    const keySpan = document.createElement("span");
    keySpan.className = "tool-result-key";
    keySpan.textContent = key + ":";

    const valueSpan = document.createElement("span");
    valueSpan.className = "tool-result-value";
    valueSpan.textContent = typeof value === "object" ? JSON.stringify(value) : String(value);

    row.appendChild(keySpan);
    row.appendChild(valueSpan);
    body.appendChild(row);
  }

  return body;
}
```

### Duration Formatting

```javascript
function formatDuration(ms) {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}
```

### Elapsed Time Counter

While a tool is running, the duration badge updates live:

```javascript
function startElapsedCounter(durationElement, startTime) {
  const intervalId = setInterval(() => {
    const elapsed = Math.round(performance.now() - startTime);
    durationElement.textContent = formatDuration(elapsed) + "...";
  }, 100);

  // Store interval ID on the element so it can be cleared on completion
  durationElement.dataset.intervalId = intervalId;
}

function stopElapsedCounter(durationElement) {
  const intervalId = durationElement.dataset.intervalId;
  if (intervalId) {
    clearInterval(Number(intervalId));
    delete durationElement.dataset.intervalId;
  }
}
```

---

## CSS

### Tool Activity Panel

The panel follows the same pattern as the Transcript panel (left-aligned, scrollable):

```css
.tool-activity-panel {
  width: 320px;
  min-width: 280px;
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  background: var(--card-bg);
  overflow: hidden;
}

.tool-activity-panel .panel-header {
  /* Reuse existing .panel-header styles */
}

.tool-activity-content {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
```

### Tool Cards

```css
.tool-card {
  border: 1px solid var(--border-color);
  border-radius: 0.5rem;
  padding: 0.75rem;
  background: var(--card-bg);
  font-size: 0.85rem;
}

.tool-card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.tool-card-icon {
  width: 1.25rem;
  text-align: center;
  flex-shrink: 0;
}

.tool-card-name {
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tool-card-duration {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

/* State-specific styling */

.tool-running .tool-card-icon::before {
  content: "";
  display: inline-block;
  width: 0.75rem;
  height: 0.75rem;
  border: 2px solid var(--avature-blue);
  border-top-color: transparent;
  border-radius: 50%;
  animation: tool-spin 0.8s linear infinite;
}

@keyframes tool-spin {
  to { transform: rotate(360deg); }
}

.tool-completed .tool-card-icon {
  color: #16a34a;
}

.tool-completed .tool-card-icon::before {
  content: "\2713";  /* checkmark */
}

.tool-failed .tool-card-icon {
  color: #dc2626;
}

.tool-failed .tool-card-icon::before {
  content: "\2717";  /* X mark */
}

.tool-failed {
  border-color: rgba(220, 38, 38, 0.3);
}

/* Card body */

.tool-card-body {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--border-color);
}

.tool-result-row {
  display: flex;
  gap: 0.5rem;
  padding: 0.125rem 0;
  font-family: "SF Mono", "Fira Code", monospace;
  font-size: 0.8rem;
}

.tool-result-key {
  color: var(--text-secondary);
  flex-shrink: 0;
}

.tool-result-value {
  color: var(--text-primary);
  word-break: break-all;
}

.tool-card-error {
  margin-top: 0.5rem;
  color: #dc2626;
  font-size: 0.8rem;
}
```

### Conversation-Center Notification

```css
.tool-notification {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  margin-top: 0.75rem;
  background: rgba(0, 84, 185, 0.08);
  border-radius: 2rem;
  font-size: 0.8rem;
  color: var(--avature-blue);
  animation: tool-notification-in 0.3s ease;
}

.tool-notification.hidden {
  display: none;
}

@keyframes tool-notification-in {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

.tool-notification-spinner {
  width: 0.75rem;
  height: 0.75rem;
  border: 2px solid var(--avature-blue);
  border-top-color: transparent;
  border-radius: 50%;
  animation: tool-spin 0.8s linear infinite;
}

.tool-notification-text {
  font-weight: 500;
}
```

---

## Panel Layout

### Three-Panel Scenario

When all three panels are open, the layout uses CSS flexbox:

```
┌────────────┬──────────────────┬────────────┬────────────┐
│ Transcript │ Conversation     │   Tool     │  Console   │
│   Panel    │    Center        │  Activity  │   Panel    │
│  (320px)   │   (flex: 1)      │  (320px)   │  (360px)   │
└────────────┴──────────────────┴────────────┴────────────┘
```

The conversation center has `flex: 1` with a minimum width, so it compresses as panels open. On narrow viewports, having all three open will be cramped, but this is an advanced use case.

The Tool Activity panel sits between the conversation center and the console panel. This groups the two "activity" panels (tool + console) on the right side, with the "content" panels (transcript + conversation) on the left.

### Panel Order in HTML

```html
<div class="main-layout">
  <div class="transcript-panel hidden">...</div>
  <div class="conversation-center">...</div>
  <div class="tool-activity-panel hidden">...</div>
  <div class="console-panel hidden">...</div>
</div>
```

---

## Interaction Details

### Tool Invocation During Conversation

Timeline of a typical tool use:

```
1. User asks: "What time is it?"
2. Model decides to call getDateAndTimeTool
3. Bedrock sends tool_use request to server

4. Server receives tool request
5. Server emits tool_started event
6. Frontend receives tool_started:
   - Creates "running" card (if panel open) or buffers invocation
   - Shows conversation-center notification: "Using getDateAndTimeTool..."
   - Starts elapsed counter on card

7. Server executes GetDateAndTimeTool
8. Server sends result back to Bedrock
9. Server emits tool_completed event
10. Frontend receives tool_completed:
    - Updates card to "completed" state with result and duration
    - Stops elapsed counter
    - Hides conversation-center notification

11. Bedrock incorporates result into model response
12. Model speaks: "It's currently 2:30 PM UTC on Tuesday, March 17th."
```

Total visible duration: typically 100-300ms. The notification and card provide immediate feedback during this gap.

### Empty State

When the Tool Activity panel is open but no tools have been invoked, show a centered message:

```
┌──────────────────────────────────────────┐
│                                          │
│        No tool activity yet.             │
│   Tools will appear here when the        │
│   agent uses them during conversation.   │
│                                          │
└──────────────────────────────────────────┘
```

### Multiple Tools in Sequence

If the model calls multiple tools (possible with future agents), cards stack vertically in chronological order. Each card tracks its own duration independently.
