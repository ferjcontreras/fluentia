# 3. Session Management and Event Protocol

## Session Manager

The session manager (`session/manager.py`) orchestrates WebSocket sessions. It is the bridge between the client (browser) and the provider (Google, Bedrock).

### Responsibilities

1. **Accept the WebSocket connection** and extract path parameters (`provider`, `user_id`, `session_id`).
2. **Resolve the agent definition** from the agent registry (default: interviewer). In stage 1, the agent is determined by a query parameter or defaults to the interviewer. Future stages may support agent selection via UI.
3. **Receive prompt configuration** from the client's first WebSocket message (agent name, company name, custom questions, etc.). Apply it to the agent definition's prompt template.
4. **Instantiate the provider** based on the `provider` path parameter.
5. **Create a `SessionContext`** with the rendered agent definition and an `emit` callback.
6. **Call `provider.handle_session()`**, which runs until the session ends.
7. **Relay normalized events** to the client WebSocket via the `emit` callback.
8. **Handle disconnections and errors** gracefully: log, clean up, close.

### WebSocket Endpoint

Single unified endpoint:

```
/ws/{provider}/{user_id}/{session_id}
```

- `provider`: `"google"` or `"bedrock"` (extensible to future providers)
- `user_id`: Client-provided user identifier
- `session_id`: Client-provided session identifier (UUID recommended)

Query parameters are provider-specific (e.g., `?proactivity=true&affective_dialog=true` for Google). The session manager passes the raw WebSocket to the provider, which extracts what it needs.

Additional query parameters for agent selection:

- `agent`: Agent definition name (default: `"interviewer"`). Maps to a registered `AgentDefinition`.

### Session Lifecycle

```
Client connects to /ws/{provider}/{user_id}/{session_id}
    |
    v
Session manager accepts WebSocket
    |
    v
Wait for prompt_config message (5s timeout, use defaults if missing)
    |
    v
Resolve AgentDefinition from registry
    |
    v
Render prompt with prompt_config variables
    |
    v
Create SessionContext (user_id, session_id, agent_definition, emit)
    |
    v
Emit SESSION_START event to client
    |
    v
Call provider.handle_session(websocket, session_context)
    |   (provider streams audio, handles tool calls, emits events)
    |
    v
On disconnect/error: emit SESSION_END, cleanup
```

---

## Event Protocol

### Protocol Versioning

Every server-to-client message includes a protocol version field:

```json
{
    "v": 1,
    "type": "audio",
    "payload": { ... },
    "ts": "2026-03-17T14:30:00.000Z"
}
```

The version number (`"v": 1`) is incremented only for breaking changes. Non-breaking additions (new event types, new optional payload fields) do not require a version bump. Clients should ignore unknown event types and unknown payload fields for forward compatibility.

### Event Types

```python
class SessionEventType(str, Enum):
    """Normalized event types emitted by providers."""

    # Content delivery
    AUDIO = "audio"                             # Base64-encoded audio chunk
    TEXT = "text"                                # Text content

    # Transcription
    INPUT_TRANSCRIPTION = "input_transcription"   # What the user said
    OUTPUT_TRANSCRIPTION = "output_transcription"  # What the agent said

    # Session control
    SESSION_START = "session_start"              # Session initialized
    SESSION_END = "session_end"                  # Session terminated
    TURN_COMPLETE = "turn_complete"              # Agent finished speaking
    INTERRUPTED = "interrupted"                  # User barged in

    # Tool lifecycle
    TOOL_STARTED = "tool_started"               # Tool execution began
    TOOL_PROGRESS = "tool_progress"             # Intermediate update
    TOOL_COMPLETED = "tool_completed"           # Tool finished successfully
    TOOL_FAILED = "tool_failed"                 # Tool execution failed

    # Errors
    ERROR = "error"                             # Recoverable error
```

### Event Payload Schemas

**AUDIO**
```json
{
    "v": 1,
    "type": "audio",
    "payload": {
        "data": "<base64-encoded PCM audio>",
        "sample_rate": 24000
    }
}
```

**TEXT**
```json
{
    "v": 1,
    "type": "text",
    "payload": {
        "content": "Hello, welcome to the interview."
    }
}
```

**INPUT_TRANSCRIPTION / OUTPUT_TRANSCRIPTION**
```json
{
    "v": 1,
    "type": "input_transcription",
    "payload": {
        "text": "Tell me about your experience.",
        "is_partial": false
    }
}
```

**TURN_COMPLETE**
```json
{
    "v": 1,
    "type": "turn_complete",
    "payload": {}
}
```

**INTERRUPTED**
```json
{
    "v": 1,
    "type": "interrupted",
    "payload": {}
}
```

**TOOL_STARTED / TOOL_PROGRESS / TOOL_COMPLETED / TOOL_FAILED**
```json
{
    "v": 1,
    "type": "tool_started",
    "payload": {
        "tool_id": "uuid-correlation-id",
        "tool_name": "getDateAndTimeTool",
        "message": "Looking up the current time..."
    }
}
```

**ERROR**
```json
{
    "v": 1,
    "type": "error",
    "payload": {
        "code": "provider_connection_failed",
        "message": "Failed to connect to Bedrock. Retrying...",
        "recoverable": true
    }
}
```

### Reserved Payload Fields

The following fields are reserved for future use. They may appear in any event payload without requiring a protocol version bump:

- `media_type`: For future image/video support
- `metadata`: Arbitrary key-value pairs for provider-specific or agent-specific data

### Client-to-Server Messages

**Audio data** (binary WebSocket frames):
Raw PCM audio bytes. No JSON wrapper for audio to minimize latency.

**Prompt configuration** (text WebSocket frame, sent once at session start):
```json
{
    "type": "prompt_config",
    "agent_name": "Taylor",
    "company_name": "Avature",
    "questions": "Question 1: ...\nQuestion 2: ...",
    "guidelines": "Guideline 1: ..."
}
```

The prompt_config message is agent-specific. The session manager passes it to the agent definition's prompt renderer, which extracts the fields it needs and ignores the rest. Different agents define different prompt_config fields.

---

## Session State

Sessions are **in-memory and ephemeral**. All per-session state (audio buffers, conversation context, tool execution state) lives only for the duration of the WebSocket connection. When the connection closes, all state is discarded.

This design enables:
- **Horizontal scaling**: Any pod can handle any session. No sticky sessions needed for session state.
- **Simple failure recovery**: If a pod crashes, clients reconnect and start a new session. No state to recover.
- **Zero external dependencies**: No Redis, no database, no shared state.

The tradeoff is that reconnection starts a fresh conversation. This is acceptable for the current use cases (short-lived interview sessions). If session persistence is needed in the future, a session store can be added behind the `SessionContext` without changing the provider interface.

---

## Error Handling

### Provider Errors

If a provider encounters an error during a session:

1. **Recoverable** (transient network issues, temporary service unavailability): Emit an `ERROR` event with `"recoverable": true`. The provider may retry internally with bounded backoff.
2. **Unrecoverable** (authentication failure, unsupported operation): Emit an `ERROR` event with `"recoverable": false`, followed by `SESSION_END`. Close the WebSocket.

### Client Disconnection

If the WebSocket closes unexpectedly:

1. The provider's `handle_session()` raises a `WebSocketDisconnect` exception.
2. The session manager catches it, logs the disconnection, and cleans up.
3. No `SESSION_END` is emitted (the client is gone).

### Provider Disconnection

If the external service (Google, Bedrock) disconnects:

1. The provider emits an `ERROR` event with details.
2. The provider may attempt reconnection (bounded retries with exponential backoff).
3. If reconnection fails, emit `SESSION_END` and close the WebSocket.
