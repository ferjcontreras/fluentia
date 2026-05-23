# 7. Frontend

## Approach

The frontend is a **vanilla HTML/CSS/JS** application with no framework and no build step. It is served as static files by FastAPI directly from `src/livoia/static/`.

This approach is chosen because:
- The UI is a thin control surface over WebSocket and Web Audio APIs.
- A build step adds complexity (Node.js, bundler config, source maps) without proportional benefit.
- Static files inside the Python package create a single deployment artifact.
- The team's expertise is in Python/ML, not frontend frameworks.

If the frontend grows significantly in complexity (multiple pages, complex state management, component reuse), a lightweight framework can be introduced later without affecting the backend.

## File Structure

```
static/
    index.html                  # Main page
    css/
        styles.css              # All styles
    js/
        app.js                  # Application logic: WebSocket, UI state, event handling
        audio-worklet.js        # AudioWorklet registration and management
    audio/
        audio-processor.js      # AudioWorklet processor (runs in audio thread)
```

## Serving

FastAPI mounts the static directory at the root path:

```python
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
```

The `html=True` flag enables serving `index.html` for the root path `/`.

API and WebSocket routes are registered before the static mount, so they take priority:
- `/ws/{provider}/{user_id}/{session_id}` -- WebSocket
- `/health`, `/ready` -- Health endpoints
- `/api/agents` -- Agent metadata (future)

## UI Layout

### Stage 1

The UI has two panels:

**Left Panel: Settings**
- Provider selector (Google / Bedrock)
- Agent name, company name, questions, guidelines (customizable per session)
- Connect / Disconnect button
- Connection status indicator

**Right Panel: Conversation**
- Message log with timestamps (user transcriptions, agent transcriptions)
- Audio level indicator (optional)
- Barge-in status indicator

### Future Stages

| Tab | Stage | Description |
|-----|-------|-------------|
| **Settings** | 1 | Prompt customization, provider selection |
| **Agent Selector** | 2 | Choose agent type (interviewer, scheduler, assistant). Settings form adapts dynamically based on agent's `config_fields`. |
| **Prompt Preview** | 2 | Read-only view of the rendered system prompt |
| **Tool Activity** | 3 | Live feed of tool invocations and results during a session |

## WebSocket Communication

### Connection

```javascript
const ws = new WebSocket(
    `ws://${host}/ws/${provider}/${userId}/${sessionId}?agent=${agentName}`
);
```

### First Message: Prompt Configuration

```javascript
ws.send(JSON.stringify({
    type: "prompt_config",
    agent_name: agentNameInput.value,
    company_name: companyNameInput.value,
    questions: questionsInput.value,
    guidelines: guidelinesInput.value,
}));
```

### Audio Streaming

Audio capture uses the **AudioWorklet API** for low-latency, off-main-thread audio processing:

1. `getUserMedia()` captures microphone input.
2. An `AudioWorkletProcessor` (in `audio/audio-processor.js`) runs in the audio thread, collecting PCM samples into chunks.
3. The worklet posts audio chunks to the main thread via `MessagePort`.
4. The main thread sends chunks as binary WebSocket frames.

Audio playback:
1. Receive `audio` events from the WebSocket.
2. Decode base64 payload to PCM samples.
3. Create `AudioBuffer`, schedule playback via `AudioBufferSourceNode`.
4. Queue buffers for gapless playback.

### Event Handling

```javascript
ws.onmessage = (event) => {
    if (typeof event.data === "string") {
        const msg = JSON.parse(event.data);
        switch (msg.type) {
            case "audio":
                playAudio(msg.payload.data, msg.payload.sample_rate);
                break;
            case "input_transcription":
                displayTranscription("user", msg.payload.text, msg.payload.is_partial);
                break;
            case "output_transcription":
                displayTranscription("agent", msg.payload.text, msg.payload.is_partial);
                break;
            case "turn_complete":
                onTurnComplete();
                break;
            case "interrupted":
                onInterrupted();
                break;
            case "error":
                displayError(msg.payload.message, msg.payload.recoverable);
                break;
            case "session_start":
                onSessionStart();
                break;
            case "session_end":
                onSessionEnd();
                break;
            // Unknown types are silently ignored (forward compatibility)
        }
    }
};
```

### Reconnection

If the WebSocket disconnects unexpectedly, the client attempts to reconnect:

- **Delay**: 5 seconds between attempts
- **Max attempts**: 3
- **Behavior**: Each reconnection starts a fresh session (new session ID). There is no session resumption.

## Browser Compatibility

The frontend requires:
- **Web Audio API** with AudioWorklet support
- **WebSocket API**
- **getUserMedia** (microphone access)

This covers all modern browsers (Chrome, Firefox, Safari, Edge). No polyfills needed.

## No Frontend Build or Test

Stage 1 does not include:
- A JavaScript build step (no webpack, vite, rollup)
- Frontend unit tests
- CSS preprocessing

The JS is small enough to maintain as plain scripts. If the frontend grows to warrant these, they can be added without backend changes.
