# Detailed Design: Conversation Tab Redesign

## Current Structure (Before)

```
tab-conversation
  main-layout (flex row)
    container (flex: 2)          <- always visible
      #messages                  <- transcription bubbles
      input-container            <- text input + buttons
    console-panel (flex: 1)      <- always visible
```

## Proposed Structure (After)

```
tab-conversation
  conversation-toolbar           <- NEW: toggle buttons
  conversation-area (flex row)
    transcript-panel             <- MOVED: hidden by default, slides from left
    conversation-center          <- NEW: state indicator + controls
      state-indicator
      speak-first-message
      input-container            <- MOVED from container
    console-panel                <- EXISTING: hidden by default, slides from right
```

## HTML Changes (index.html)

### Conversation toolbar

Add between the tab bar and the tab content, inside `tab-conversation`:

```html
<div class="conversation-toolbar">
  <button class="toolbar-toggle" id="toggleTranscript"
          title="Show transcript">
    <!-- Text/chat icon (Unicode or inline SVG) -->
    <span class="toolbar-icon">&#x1F4AC;</span>
    <span class="toolbar-label">Transcript</span>
  </button>
  <button class="toolbar-toggle" id="toggleConsole"
          title="Show event console">
    <span class="toolbar-icon">&#x2699;</span>
    <span class="toolbar-label">Console</span>
  </button>
</div>
```

### Conversation center

Replace the current `container` div content:

```html
<div class="conversation-center">
  <div class="state-indicator" id="stateIndicator">
    <div class="indicator-circle"></div>
    <div class="indicator-ripple ripple-1"></div>
    <div class="indicator-ripple ripple-2"></div>
    <div class="indicator-ripple ripple-3"></div>
  </div>
  <div class="state-label" id="stateLabel"></div>
  <!-- speak-first-banner is injected here by JS (existing logic) -->

  <div class="input-container">
    <!-- existing form, unchanged -->
  </div>
</div>
```

### Transcript panel

Wrap the existing `#messages` div:

```html
<div class="transcript-panel" id="transcriptPanel">
  <div class="panel-header">
    <span>Transcript</span>
    <button class="panel-close" id="closeTranscript">&times;</button>
  </div>
  <div id="messages"></div>
</div>
```

### Console panel

No structural changes. Add a close button to the existing console header.

## CSS Changes (styles.css)

### Conversation toolbar

```css
.conversation-toolbar {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem 2rem;
  background-color: #f8f9fa;
  border-bottom: 1px solid var(--border-color);
}

.toolbar-toggle {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 1rem;
  background: white;
  color: #5f6368;
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toolbar-toggle:hover {
  background-color: #e8eaed;
}

.toolbar-toggle.active {
  background-color: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}
```

### Conversation center

```css
.conversation-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
  padding: 2rem;
  min-width: 0;
}
```

### State indicator

```css
.state-indicator {
  position: relative;
  width: 100px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.indicator-circle {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  z-index: 1;
  transition: transform 0.3s ease;
}

.indicator-ripple {
  position: absolute;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 2px solid transparent;
  opacity: 0;
}

/* State: idle - no animation */
.state-indicator.idle .indicator-circle {
  transform: scale(1);
}

/* State: waiting - gentle pulse */
.state-indicator.waiting .indicator-circle {
  animation: waitingPulse 2s ease-in-out infinite;
}

@keyframes waitingPulse {
  0%, 100% { transform: scale(1); opacity: 0.85; }
  50% { transform: scale(1.06); opacity: 1; }
}

/* State: user-speaking - blue ripples */
.state-indicator.user-speaking .indicator-ripple {
  border-color: var(--user-bubble-bg);
  animation: rippleOut 2s ease-out infinite;
}

.state-indicator.user-speaking .ripple-1 { animation-delay: 0s; }
.state-indicator.user-speaking .ripple-2 { animation-delay: 0.6s; }
.state-indicator.user-speaking .ripple-3 { animation-delay: 1.2s; }

@keyframes rippleOut {
  0% { transform: scale(1); opacity: 0.6; }
  100% { transform: scale(2.2); opacity: 0; }
}

/* State: agent-speaking - green glow pulse */
.state-indicator.agent-speaking .indicator-circle {
  animation: agentPulse 1s ease-in-out infinite;
  box-shadow: 0 0 0 0 rgba(52, 168, 83, 0.4);
}

@keyframes agentPulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(52, 168, 83, 0.4);
    transform: scale(1);
  }
  50% {
    box-shadow: 0 0 20px 10px rgba(52, 168, 83, 0.15);
    transform: scale(1.04);
  }
}

.state-indicator.agent-speaking .indicator-ripple {
  border-color: #34a853;
  animation: rippleOut 2.4s ease-out infinite;
}

.state-indicator.agent-speaking .ripple-1 { animation-delay: 0s; }
.state-indicator.agent-speaking .ripple-2 { animation-delay: 0.8s; }
.state-indicator.agent-speaking .ripple-3 { animation-delay: 1.6s; }
```

### State label

```css
.state-label {
  font-size: 0.9375rem;
  color: #5f6368;
  text-align: center;
  min-height: 1.5em;
}
```

### Panel slide-in

```css
/* Shared panel behavior */
.transcript-panel,
.console-panel {
  position: relative;
  overflow: hidden;
  transition: flex 0.3s ease, opacity 0.3s ease;
}

.transcript-panel.hidden,
.console-panel.hidden {
  flex: 0 !important;
  width: 0;
  opacity: 0;
  padding: 0;
  border: none;
  overflow: hidden;
}

.transcript-panel:not(.hidden) {
  flex: 1;
  border-right: 1px solid var(--border-color);
}

.console-panel:not(.hidden) {
  flex: 1;
}
```

### Panel close button

```css
.panel-close {
  background: none;
  border: none;
  color: inherit;
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  line-height: 1;
}

.panel-close:hover {
  background-color: rgba(128, 128, 128, 0.2);
}
```

## JS Changes (app.js)

### New state management

```js
// Conversation visual state
let conversationState = "idle"; // "idle" | "waiting" | "user-speaking" | "agent-speaking"

function setConversationState(newState) {
  conversationState = newState;
  const indicator = document.getElementById("stateIndicator");
  const label = document.getElementById("stateLabel");

  indicator.className = "state-indicator " + newState;

  switch (newState) {
    case "idle":
      label.textContent = "";
      break;
    case "waiting":
      // Label handled by speak-first-banner
      label.textContent = "";
      break;
    case "user-speaking":
      label.textContent = "Listening...";
      break;
    case "agent-speaking":
      label.textContent = "Speaking...";
      break;
  }
}
```

### State transitions in WebSocket handler

Add to the existing `websocket.onmessage` switch cases:

```js
case "input_transcription":
  if (conversationState === "waiting" || conversationState === "agent-speaking") {
    setConversationState("user-speaking");
    removeSpeakFirstBanner();
  }
  // ... existing transcription logic (only if panel visible) ...
  break;

case "audio":
  if (conversationState !== "agent-speaking") {
    setConversationState("agent-speaking");
  }
  // ... existing audio playback logic ...
  break;

case "turn_complete":
  setConversationState("user-speaking");
  // ... existing logic ...
  break;

case "interrupted":
  setConversationState("user-speaking");
  // ... existing logic ...
  break;
```

### Start/stop conversation updates

In the existing `startAudioButton` click handler:

```js
if (!conversationActive) {
  // ... existing start logic ...
  setConversationState("waiting");
} else {
  // ... existing stop logic ...
  setConversationState("idle");
}
```

### Panel toggle logic

```js
const toggleTranscriptBtn = document.getElementById("toggleTranscript");
const toggleConsoleBtn = document.getElementById("toggleConsole");
const transcriptPanel = document.getElementById("transcriptPanel");
// consolePanel already referenced

let transcriptVisible = false;
let consoleVisible = false;

toggleTranscriptBtn.addEventListener("click", () => {
  transcriptVisible = !transcriptVisible;
  transcriptPanel.classList.toggle("hidden", !transcriptVisible);
  toggleTranscriptBtn.classList.toggle("active", transcriptVisible);
});

toggleConsoleBtn.addEventListener("click", () => {
  consoleVisible = !consoleVisible;
  document.querySelector(".console-panel").classList.toggle("hidden", !consoleVisible);
  toggleConsoleBtn.classList.toggle("active", consoleVisible);
});
```

### Conditional transcription rendering

Wrap the existing transcription DOM manipulation in a visibility check:

```js
case "input_transcription":
  // State transition (always)
  if (conversationState === "waiting") {
    setConversationState("user-speaking");
    removeSpeakFirstBanner();
  }
  // DOM rendering (only if transcript panel visible)
  if (transcriptVisible) {
    // ... existing bubble creation/update logic ...
  }
  // Console entry (always, console handles its own visibility)
  addConsoleEntry('incoming', `Input: "${text}"`, payload);
  break;
```

## File Change Summary

| File | Changes | Estimated Lines |
|------|---------|-----------------|
| `index.html` | Add toolbar, restructure conversation area, wrap messages in transcript panel | ~25 modified |
| `styles.css` | Add toolbar, state indicator, panel toggle, state animations | ~100 new |
| `app.js` | Add state machine, toggle logic, conditional rendering guards | ~40 new, ~20 modified |

## Migration Notes

- The `#messages` div ID and all console DOM IDs remain unchanged. Existing JS references continue to work.
- The `addConsoleEntry` function continues to append to `#consoleContent` regardless of visibility. The panel's CSS `overflow: hidden` and `width: 0` handles hiding.
- The `addSpeakFirstBanner` function continues to append to `#messages`. When the transcript panel is hidden, the banner is invisible but still exists in DOM. The `removeSpeakFirstBanner` cleanup still works.
- No changes to the Settings tab.

## Testing Considerations

- Verify all four visual states render correctly.
- Verify toggling panels mid-conversation does not lose transcript history.
- Verify the "You should speak first" banner appears and disappears at the correct times.
- Verify mobile layout (panels should be full-width overlays or hidden by default).
- Verify no regressions in audio playback, text input, or WebSocket reconnection.
