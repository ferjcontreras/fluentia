# WebSocket Protocol Reference

This document describes the WebSocket communication protocol between the Fluentia frontend and backend. All voice sessions use a single WebSocket connection for bidirectional real-time communication.

## Connection

### Endpoint

```
ws://{host}:{port}/ws/{provider}/{user_id}/{session_id}
```

| Parameter | Description |
|-----------|-------------|
| `provider` | Voice provider to use: `google` or `bedrock` |
| `user_id` | Client-generated user identifier |
| `session_id` | Client-generated session identifier (UUID recommended) |

### Query Parameters

| Parameter | Provider | Description |
|-----------|----------|-------------|
| `agent` | All | Agent to use (default: configured default agent) |
| `proactivity` | Google | Enable proactive responses (`true`/`false`) |
| `affective_dialog` | Google | Enable emotional cue detection (`true`/`false`) |

### Example

```
ws://localhost:8000/ws/google/user-123/550e8400-e29b-41d4-a716-446655440000?proactivity=true
```

## Session Lifecycle

```
Client                                          Server
  |                                               |
  |  1. WebSocket connect                         |
  |---------------------------------------------->|
  |                                               |
  |  2. Connection accepted                       |
  |<----------------------------------------------|
  |                                               |
  |  3. prompt_config (client -> server)          |
  |---------------------------------------------->|
  |                                               |
  |  4. session_start event                       |
  |<----------------------------------------------|
  |                                               |
  |  5. Audio/text frames (bidirectional)         |
  |<--------------------------------------------->|
  |                                               |
  |  6. session_end event                         |
  |<----------------------------------------------|
  |                                               |
  |  7. WebSocket close                           |
  |<--------------------------------------------->|
```

### Step 3: Prompt Configuration

After the connection is accepted, the client has 5 seconds to send a `prompt_config` message. This message customizes the agent's system prompt. If no message arrives within 5 seconds, the server uses the agent's default configuration.

**Client-to-server message:**

```json
{
  "type": "prompt_config",
  "agent_name": "Taylor",
  "company_name": "Acme Corp",
  "questions": "Tell me about your experience.\nWhy do you want this role?",
  "guidelines": "Be concise. Focus on technical skills."
}
```

All fields except `type` are optional. Empty strings are ignored.

| Field | Description |
|-------|-------------|
| `agent_name` | Name the agent uses to introduce itself |
| `company_name` | Company name mentioned in the interview |
| `questions` | Interview questions (newline-separated) |
| `guidelines` | Additional behavior instructions |

## Server-to-Client Messages

Every message from the server follows this envelope format:

```json
{
  "v": 1,
  "type": "<event_type>",
  "payload": {},
  "ts": "2025-03-17T14:30:00+00:00"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `v` | `int` | Protocol version (currently `1`) |
| `type` | `string` | Event type identifier |
| `payload` | `object` | Event-specific data (may be empty) |
| `ts` | `string` | ISO 8601 timestamp (UTC) |

The protocol version field (`v`) enables future format changes while maintaining backward compatibility.

## Event Types

### Content Events

#### `audio`

Audio data from the voice model.

```json
{
  "v": 1,
  "type": "audio",
  "payload": {
    "data": "<base64-encoded PCM audio>",
    "sample_rate": 24000
  },
  "ts": "..."
}
```

| Payload Field | Type | Description |
|---------------|------|-------------|
| `data` | `string` | Base64-encoded PCM audio (16-bit, mono) |
| `sample_rate` | `int` | Sample rate in Hz (typically 24000) |

#### `text`

Text content from the model (non-audio responses).

```json
{
  "v": 1,
  "type": "text",
  "payload": {
    "text": "Here is my response."
  },
  "ts": "..."
}
```

### Transcription Events

#### `input_transcription`

Transcription of the user's speech.

```json
{
  "v": 1,
  "type": "input_transcription",
  "payload": {
    "text": "Hello, my name is...",
    "is_partial": true
  },
  "ts": "..."
}
```

| Payload Field | Type | Description |
|---------------|------|-------------|
| `text` | `string` | Transcribed text |
| `is_partial` | `bool` | `true` if transcription is still in progress |

#### `output_transcription`

Transcription of the model's speech output.

```json
{
  "v": 1,
  "type": "output_transcription",
  "payload": {
    "text": "Welcome to the interview.",
    "is_partial": false
  },
  "ts": "..."
}
```

### Session Control Events

#### `session_start`

Emitted when the session is initialized, before the provider begins processing.

```json
{
  "v": 1,
  "type": "session_start",
  "payload": {},
  "ts": "..."
}
```

#### `session_end`

Emitted when the session is complete.

```json
{
  "v": 1,
  "type": "session_end",
  "payload": {},
  "ts": "..."
}
```

#### `turn_complete`

Indicates the model has finished its current response turn.

```json
{
  "v": 1,
  "type": "turn_complete",
  "payload": {},
  "ts": "..."
}
```

#### `interrupted`

The user interrupted the model while it was speaking (barge-in).

```json
{
  "v": 1,
  "type": "interrupted",
  "payload": {},
  "ts": "..."
}
```

### Tool Events

Tools are functions the model can invoke during a conversation (for example, checking the current date and time).

#### `tool_started`

A tool execution has begun.

```json
{
  "v": 1,
  "type": "tool_started",
  "payload": {
    "tool_name": "getDateAndTimeTool",
    "tool_use_id": "abc-123"
  },
  "ts": "..."
}
```

#### `tool_progress`

Intermediate progress from a long-running tool.

```json
{
  "v": 1,
  "type": "tool_progress",
  "payload": {
    "tool_name": "getDateAndTimeTool",
    "message": "Processing..."
  },
  "ts": "..."
}
```

#### `tool_completed`

A tool executed and returned a result.

```json
{
  "v": 1,
  "type": "tool_completed",
  "payload": {
    "tool_name": "getDateAndTimeTool",
    "result": {
      "current_time": "14:30:00",
      "current_date": "2025-03-17",
      "day_of_week": "Monday",
      "timezone": "UTC"
    }
  },
  "ts": "..."
}
```

#### `tool_failed`

A tool execution failed.

```json
{
  "v": 1,
  "type": "tool_failed",
  "payload": {
    "tool_name": "getDateAndTimeTool",
    "error": "Tool execution failed: timeout"
  },
  "ts": "..."
}
```

### Error Events

#### `error`

An error occurred during the session.

```json
{
  "v": 1,
  "type": "error",
  "payload": {
    "message": "Provider connection lost"
  },
  "ts": "..."
}
```

## Client-to-Server Messages

After the initial `prompt_config` message, the client sends binary and text frames:

### Audio Data

Raw PCM audio bytes sent as WebSocket binary frames. The frontend captures audio using the AudioWorklet API at 16kHz, 16-bit, mono.

### Text Messages

Text input sent as WebSocket text frames:

```json
{
  "type": "text",
  "text": "Hello"
}
```

## Audio Format

Both upstream and downstream audio use PCM encoding:

| Property | Value |
|----------|-------|
| Encoding | Linear PCM (raw bytes) |
| Sample size | 16-bit signed integer |
| Channels | 1 (mono) |
| Input sample rate | 16,000 Hz |
| Output sample rate | 24,000 Hz (provider-dependent) |
| Byte order | Little-endian |

The frontend uses the Web Audio API with AudioWorklet processors for recording and playback. Audio is captured from the microphone at the input sample rate and played back at the rate specified in each `audio` event's `sample_rate` field.

## Implementation Details

### Session Manager

The `SessionManager` class (`src/fluentia/session/manager.py`) orchestrates the session lifecycle:

1. Accepts the WebSocket connection
2. Waits for `prompt_config` (5-second timeout)
3. Resolves the provider and agent
4. Merges prompt variables into the agent's Jinja2 template
5. Creates a `SessionContext` with an `emit` callback
6. Delegates to `provider.handle_session()`
7. Emits `session_start` and `session_end` events
8. Records metrics (session duration, errors)

### Serialization

Event serialization is handled by `src/fluentia/session/protocol.py`. The `serialize_event()` function wraps each `SessionEvent` with the protocol version and UTC timestamp. The `deserialize_client_message()` function parses incoming JSON text frames.

### Provider Differences

Both providers normalize their events to the same `SessionEventType` enum, but their internal streaming mechanisms differ:

- **Google**: Uses the ADK (Agent Development Kit) `LiveRequestQueue` for bidirectional streaming. Audio and text are sent as ADK-specific content objects. Events are converted from ADK event format to `SessionEvent`.
- **Bedrock**: Uses HTTP/2 bidirectional streaming via the AWS SDK. Audio is base64-encoded in JSON event frames. The `NovaSonicClient` handles low-level stream management and emits `SessionEvent` objects and internal tool-use events.

These differences are hidden from the frontend, which interacts only with the normalized event protocol.
