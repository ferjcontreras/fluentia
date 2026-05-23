# Frontend Design

## Overview

The frontend is a single-page application built with vanilla HTML, CSS, and JavaScript (no framework). It communicates with the backend exclusively via WebSocket.

The current frontend is carried forward with minimal changes for the initial release, but the architecture is designed for future extensibility (new tabs, tool visibility, prompt preview).

## Architecture

```
static/
├── index.html                    # Main HTML structure
├── css/
│   └── style.css                 # All styles
└── js/
    ├── app.js                    # Main application logic
    ├── audio-player.js           # Audio playback (AudioWorklet)
    ├── audio-recorder.js         # Audio recording (AudioWorklet)
    ├── pcm-player-processor.js   # Playback AudioWorklet processor
    └── pcm-recorder-processor.js # Recording AudioWorklet processor
```

## Tab System

### Current Tabs (v1)
1. **Conversation**: Main chat interface with audio controls
2. **Settings**: Prompt customization form

### Future Tabs (designed for but not implemented in v1)
3. **Prompt**: Read-only view of the rendered system prompt
4. **Tool Use**: Real-time log of tool invocations and results

The tab system uses a simple show/hide pattern:

```html
<div class="tab-bar">
  <button class="tab-button active" data-tab="conversation">Conversation</button>
  <button class="tab-button" data-tab="settings">Settings</button>
  <!-- Future: -->
  <!-- <button class="tab-button" data-tab="prompt">Prompt</button> -->
  <!-- <button class="tab-button" data-tab="tools">Tool Use</button> -->
</div>

<div id="tab-conversation" class="tab-content active">...</div>
<div id="tab-settings" class="tab-content">...</div>
```

Adding a tab requires only:
1. A new button in the tab bar
2. A new `<div class="tab-content">` section
3. No JS changes needed (the existing tab switching code handles it)

## Conversation Tab

### Layout
```
┌─────────────────────────────────────────────────────┐
│ Header: Title | Provider Selector | Options         │
├───────────────────────────────┬─────────────────────┤
│                               │                     │
│  Chat Messages Area           │  Event Console      │
│  (scrollable)                 │  (scrollable)       │
│                               │                     │
│  - Agent bubbles (gray)       │  - Upstream events   │
│  - User bubbles (blue)        │  - Downstream events │
│  - System messages            │  - Errors            │
│  - Speak-first banner         │                     │
│                               │  [ ] Show audio     │
│                               │  [Clear Console]    │
├───────────────────────────────┴─────────────────────┤
│ [Start Conversation] [Camera] | Text input | [Send] │
└─────────────────────────────────────────────────────┘
```

### Features
- **Provider selector**: Dropdown to choose Google Gemini or AWS Bedrock
- **Option checkboxes**: Proactivity, Affective Dialog (Google-only)
- **Message bubbles**: User (blue, right-aligned), Agent (gray, left-aligned)
- **Transcription display**: Real-time transcription of both sides
- **Start/New Conversation button**: Toggle audio, reset session
- **Camera button**: Capture and send image (Google-only)
- **Text input**: Type messages as alternative to voice
- **Event console**: Expandable JSON events for debugging

## Settings Tab

### Layout
```
┌─────────────────────────────────────────────────────┐
│ Customization Layer                                  │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Agent Name: [Taylor________________________]    │ │
│ │ Guidelines: [________________________________]  │ │
│ │            [________________________________]   │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ Use Case                                            │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Company Name: [Avature_____________________]    │ │
│ │ Interview Questions: [______________________]   │ │
│ │                     [______________________]    │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

Settings are sent as a `prompt_config` message when the WebSocket connects. Changing settings requires reconnecting (which happens automatically when the provider or options change).

### How Settings Flow to the Backend
1. User modifies settings in the form
2. User starts or restarts a conversation (or changes provider/options)
3. WebSocket connects
4. `app.js` sends `prompt_config` as the first text message
5. Backend renders the system prompt using the provided values
6. System prompt is passed to the provider

## Future: Prompt Tab

This tab will display a read-only, formatted view of the rendered system prompt. This requires:

1. A new REST endpoint: `GET /api/prompt/preview` that accepts the same fields as `prompt_config` and returns the rendered prompt
2. The frontend calls this endpoint whenever settings change and displays the result
3. Alternative: render the prompt client-side (simpler, but duplicates the template)

Recommendation: **server-side rendering** to ensure the preview matches exactly what the agent sees.

## Future: Tool Use Tab

This tab will show real-time tool invocations during conversation:

```
┌─────────────────────────────────────────────────────┐
│ Tool Use Log                                         │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 14:32:05  getDateAndTime                        │ │
│ │ Input: {}                                       │ │
│ │ Output: {"date": "2026-03-16", "time": "14:32"} │ │
│ │ Duration: 12ms                                  │ │
│ ├─────────────────────────────────────────────────┤ │
│ │ 14:32:15  searchWeb                             │ │
│ │ Input: {"query": "latest news about AI"}        │ │
│ │ Output: {"results": [...]}                      │ │
│ │ Duration: 1.2s                                  │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

This requires:
1. A new WebSocket event type for tool use (e.g., `{"toolUse": {"name": "...", "input": {...}, "output": {...}}}`)
2. Frontend handler to display tool events in the Tool Use tab
3. The Bedrock provider already handles tools internally; it needs to also emit these events to the WebSocket

## Audio Architecture

### Recording (Browser -> Server)
1. `getUserMedia()` captures microphone at 16kHz
2. `AudioWorklet` (`pcm-recorder-processor.js`) converts Float32 to 16-bit PCM
3. PCM data sent as binary WebSocket frames

### Playback (Server -> Browser)
1. Server sends base64-encoded PCM audio in JSON events
2. `app.js` decodes base64 to ArrayBuffer
3. `AudioWorklet` (`pcm-player-processor.js`) plays at 24kHz

### No Changes Needed
The audio pipeline is well-implemented and works correctly. Carry it forward as-is.

## Design Constraints

1. **No JavaScript framework**: Vanilla JS keeps the frontend simple and dependency-free
2. **No build step**: JS files are served directly (no webpack, no bundling)
3. **CSS variables for theming**: Easy to customize colors later
4. **Responsive layout**: Works on desktop browsers (mobile not a priority)
5. **Browser support**: Modern browsers (Chrome, Firefox, Edge) with AudioWorklet support

## Changes from PoC

### Minimal changes for v1
1. Update WebSocket URL construction to use unified `/ws/{provider}/...` endpoint (instead of `/ws/google/...` and `/ws/bedrock/...`)
2. That's it. The frontend is functionally identical.

### Future changes (not v1)
- Add Prompt and Tool Use tabs
- Add tool configuration UI in Settings
- Add visual indicators for tool execution in the conversation
- Add prompt preview rendering
