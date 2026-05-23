# Plan: Tool Transparency (Phase 3)

## Context

When a voice model invokes a tool during conversation, users see an unexplained silence. The backend already emits `TOOL_STARTED`, `TOOL_PROGRESS`, `TOOL_COMPLETED`, and `TOOL_FAILED` events over WebSocket. Currently these are only logged as raw lines in the Event Console. This feature adds a dedicated Tool Activity panel with structured cards and a conversation-center notification to make tool usage visible. **No backend changes required.**

## Files to Modify

1. `src/fluentia/static/index.html` — HTML additions
2. `src/fluentia/static/js/app.js` — JS logic for tool state, cards, notifications
3. `src/fluentia/static/css/styles.css` — Styles for panel, cards, notification

## Implementation Steps

### Step 1: HTML Changes (`index.html`)

1. **Toolbar button** — Add "Tools" button between Transcript and Console buttons (line 56-59):
   ```html
   <button class="toolbar-toggle" id="toggleToolActivity" title="Show tool activity">
     <span class="toolbar-icon">&#x1F527;</span>
     <span class="toolbar-label">Tools</span>
   </button>
   ```

2. **Tool Activity panel** — Add between `.conversation-center` and `.console-panel` (after line 95):
   ```html
   <div class="tool-activity-panel hidden" id="toolActivityPanel">
     <div class="panel-header">
       <span>Tool Activity</span>
       <button class="panel-close" id="closeToolActivity">&times;</button>
     </div>
     <div class="tool-activity-content" id="toolActivityContent">
       <div class="tool-activity-empty" id="toolActivityEmpty">
         <p>No tool activity yet.</p>
         <p>Tools will appear here when the agent uses them during conversation.</p>
       </div>
     </div>
   </div>
   ```

3. **Notification element** — Inside `.conversation-center`, after `.state-label` (after line 78):
   ```html
   <div class="tool-notification hidden" id="toolNotification">
     <span class="tool-notification-spinner"></span>
     <span class="tool-notification-text" id="toolNotificationText"></span>
   </div>
   ```

### Step 2: JavaScript Changes (`app.js`)

**State variables** (near panel toggle section ~line 367):
- `let toolActivityVisible = false;`
- `let toolInvocations = [];`
- `let activeToolId = null;`

**DOM references** (near existing DOM refs):
- `toggleToolActivityBtn`, `toolActivityPanel`, `toolActivityContent`, `toolActivityEmpty`
- `toolNotification`, `toolNotificationText`

**Panel toggle** — Follow exact pattern of `setTranscriptVisible`/`setConsoleVisible`:
- `setToolActivityVisible(visible)` — toggles panel, renders buffered cards when opening
- Wire up toggle button click and close button

**Event handling** — Replace the current combined `tool_started`/`tool_progress`/`tool_completed`/`tool_failed` case (lines 741-746) with individual cases per the spec's detailed-design.md:

- `tool_started`: Create invocation record, push to buffer, render card if panel visible, show notification
- `tool_progress`: Find running invocation by name, update progress message
- `tool_completed`: Update invocation state/duration/result, update or create card, hide notification
- `tool_failed`: Same as completed but with error state

**Helper functions** (per details-frontend.md):
- `createToolCard(invocation)` — Creates card DOM element with header (icon + name + duration) and body
- `createResultSummary(result)` — Key-value rows from result object
- `updateToolCardCompleted(invocation)` — Updates running card to completed state
- `updateToolCardFailed(invocation)` — Updates running card to failed state
- `updateToolCardProgress(cardElement, message)` — Updates progress message
- `formatDuration(ms)` — "152ms" or "2.3s"
- `startElapsedCounter(durationElement, startTime)` — setInterval updating duration badge
- `stopElapsedCounter(durationElement)` — clearInterval
- `findInvocationById(toolId)` / `findRunningInvocation(toolName)` — buffer lookups
- `showToolNotification(toolName)` / `hideToolNotification()` — notification control
- `updateToolActivityEmpty()` — show/hide empty state based on invocations length

**Session reset** — In `resetConversationState()` (line 855) and `session_end` handler (line 738):
- Clear `toolInvocations = []`, `activeToolId = null`
- Clear `toolActivityContent` innerHTML (but preserve empty state element)
- Hide notification

**Console entries** — Keep existing `addConsoleEntry` calls for tool events (the spec says Console still shows them).

### Step 3: CSS Changes (`styles.css`)

**Tool Activity Panel** — Same pattern as `.transcript-panel`:
- `.tool-activity-panel` — flex column, border-left, background, hidden/visible transitions
- `.tool-activity-content` — flex: 1, overflow-y: auto, padding, gap
- `.tool-activity-empty` — centered muted text for empty state

**Tool Cards** — Per details-frontend.md:
- `.tool-card` — border, border-radius, padding, background
- `.tool-card-header` — flex row: icon + name + duration
- `.tool-card-icon`, `.tool-card-name`, `.tool-card-duration`
- `.tool-running .tool-card-icon::before` — spinner animation (reuse `@keyframes tool-spin`)
- `.tool-completed .tool-card-icon::before` — green checkmark
- `.tool-failed .tool-card-icon::before` — red X, red border accent
- `.tool-card-body` — result rows with monospace key-value
- `.tool-result-row`, `.tool-result-key`, `.tool-result-value`
- `.tool-card-error` — red error text

**Conversation-Center Notification**:
- `.tool-notification` — pill shape, blue tint background, flex row
- `.tool-notification-spinner` — small spinner (same animation as card)
- `.tool-notification-text` — font-weight 500
- `.tool-notification.hidden` — display: none
- `@keyframes tool-notification-in` — fade+slide entrance

**Responsive** — Add `.tool-activity-panel:not(.hidden)` rules for mobile in existing `@media (max-width: 768px)`.

## Verification

1. Run `./check_code.sh` (not applicable for pure frontend JS/CSS/HTML, but run anyway to confirm no regressions)
2. Manual test: Start a Bedrock session, ask "what time is it?" — verify:
   - Tool notification appears in conversation center ("Using getDateAndTimeTool...")
   - If Tools panel is open, a running card with spinner appears, then transitions to completed with results
   - Duration badge shows elapsed time
   - Console still shows tool events
3. Toggle Tools panel off/on — buffered invocations render when panel opens
4. "New Conversation" — tool state clears
5. Open all 3 panels (Transcript + Tools + Console) — layout doesn't break
