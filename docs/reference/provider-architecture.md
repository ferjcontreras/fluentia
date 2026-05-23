# Provider Architecture Reference

This document describes the provider abstraction that allows Fluentia to support multiple voice AI backends through a common interface.

## Overview

Fluentia supports two voice providers:

- **Google Gemini**: Uses the Google Agent Development Kit (ADK) with native audio models
- **AWS Bedrock Nova Sonic**: Uses Amazon's Nova Sonic model via HTTP/2 bidirectional streaming

Both providers implement the same `BaseProvider` interface and emit normalized `SessionEvent` objects, so the rest of the application (session manager, frontend, observability) is provider-agnostic.

## BaseProvider Interface

All providers implement the abstract base class defined in `src/fluentia/providers/base.py`:

```python
class BaseProvider(abc.ABC):
    @abc.abstractmethod
    async def handle_session(
        self, websocket: WebSocket, session_context: SessionContext
    ) -> None:
        """Run a complete voice session over the given WebSocket."""
```

A provider receives:

- **`websocket`**: The FastAPI WebSocket connection for reading client audio/text and detecting disconnections
- **`session_context`**: A frozen dataclass containing session metadata and an `emit` callback

### SessionContext

```python
@dataclass(frozen=True)
class SessionContext:
    user_id: str
    session_id: str
    agent_definition: AgentDefinition
    emit: Callable[[SessionEvent], Awaitable[None]]
```

The `emit` callback serializes a `SessionEvent` and sends it to the client over the WebSocket. Providers call `context.emit()` to send events without needing direct WebSocket access for output.

## Google Provider

**File**: `src/fluentia/providers/google.py`

### Dependencies

- `google-genai`: Google Generative AI SDK
- `google-adk`: Google Agent Development Kit

### Session Flow

1. **Initialization**: Creates a Google `Agent` with the rendered system prompt and tool declarations
2. **Connection**: Opens a bidirectional ADK `LiveRequestQueue` session
3. **Upstream task**: Reads binary frames (audio) and text frames from the WebSocket, forwards them to the ADK session
4. **Downstream task**: Reads ADK events, converts them to `SessionEvent` objects, and calls `emit()`
5. **Concurrency**: Upstream and downstream run as concurrent `asyncio` tasks via `asyncio.gather()`

### Event Conversion

The `_convert_adk_event()` method maps ADK event structures to normalized `SessionEvent` types:

| ADK Event | SessionEventType |
|-----------|-----------------|
| `turn_complete: True` | `TURN_COMPLETE` |
| `interrupted: True` | `INTERRUPTED` |
| `server_content.input_transcription` | `INPUT_TRANSCRIPTION` |
| `server_content.output_transcription` | `OUTPUT_TRANSCRIPTION` |
| `server_content.model_turn` with `audio/pcm` | `AUDIO` |
| `server_content.model_turn` with text | `TEXT` |

### Native Audio Features

When the configured model includes "native-audio" in its name, the provider enables two optional features via `LiveConnectConfig`:

- **Proactivity**: The model can initiate responses without an explicit user prompt
- **Affective Dialog**: The model detects and adapts to emotional cues in speech

These features are controlled by WebSocket query parameters (`proactivity`, `affective_dialog`).

### Run Configuration

The `_build_run_config()` method constructs the ADK `RunConfig` with:

- Model name and API key from `GoogleProviderConfig`
- Response modality (`AUDIO` for native audio models, `TEXT` otherwise)
- Speech configuration with voice name and language
- Optional proactivity and affective dialog settings

## Bedrock Provider

**Files**: `src/fluentia/providers/bedrock/provider.py`, `src/fluentia/providers/bedrock/client.py`, `src/fluentia/providers/bedrock/config.py`

### Dependencies

- `aws-sdk-bedrock-runtime`: AWS Bedrock Runtime SDK (HTTP/2 streaming)
- `smithy-aws-core`: AWS credential resolution

### Session Flow

1. **Initialization**: Creates a `NovaSonicClient` with a `BedrockSessionConfig`
2. **Connection**: Opens an HTTP/2 bidirectional stream with Bedrock, sends session start, prompt start, system prompt, and audio content start events
3. **Upstream task**: Reads binary audio frames from the WebSocket, queues them in the client's audio input queue
4. **Downstream task**: Iterates over events from the client's `receive_events()` async iterator, emits `SessionEvent` objects, and handles tool-use events
5. **Tool handling**: When the model requests a tool, the provider executes it via `ToolProcessor` and sends the result back to the Bedrock stream
6. **Cleanup**: Sends closing events (content end, prompt end, session end) and shuts down background tasks

### NovaSonicClient

The low-level client (`src/fluentia/providers/bedrock/client.py`) manages:

- **Stream lifecycle**: HTTP/2 bidirectional stream setup and teardown
- **Audio encoding**: Base64-encodes PCM audio for the Bedrock API
- **Event parsing**: Parses JSON response frames and emits `SessionEvent` objects
- **Tool use state**: Accumulates tool-use data across multiple frames before emitting a complete `_InternalToolUseEvent`
- **Background tasks**: Separate `asyncio` tasks for processing audio input (queue → stream) and responses (stream → event queue)

### BedrockSessionConfig

A Pydantic model (`src/fluentia/providers/bedrock/config.py`) with session-level parameters:

| Field | Default | Description |
|-------|---------|-------------|
| `model_id` | `amazon.nova-2-sonic-v1:0` | Bedrock model identifier |
| `region` | `us-east-1` | AWS region |
| `voice_id` | `matthew` | Voice for speech synthesis |
| `input_sample_rate` | `16000` | Input audio sample rate (Hz) |
| `output_sample_rate` | `24000` | Output audio sample rate (Hz) |
| `language` | `None` | Language code (auto-detect if not set) |
| `temperature` | `0.7` | Sampling temperature (0.0-1.0) |
| `top_p` | `0.9` | Top-p sampling (0.0-1.0) |
| `max_tokens` | `1024` | Maximum response tokens |

### Tool Integration

The Bedrock provider handles tool use through this sequence:

1. The model emits a `toolUse` event with `toolName` and `toolUseId`
2. A `contentEnd` event with `type: "TOOL"` signals the complete tool request
3. The provider emits a `TOOL_STARTED` session event
4. `ToolProcessor.execute()` runs the tool
5. The result is sent back to Bedrock via `NovaSonicClient.send_tool_result()`
6. The provider emits `TOOL_COMPLETED` or `TOOL_FAILED`

## Adding a New Provider

To add a new voice provider:

1. Create a new module under `src/fluentia/providers/` (e.g., `src/fluentia/providers/azure.py`)
2. Implement `BaseProvider` with a `handle_session()` method
3. Add a configuration class to `src/fluentia/config.py` using Pydantic `BaseSettings`
4. Register the provider in the `create_app()` factory (`src/fluentia/app.py`) by adding it to the `providers` dictionary
5. The frontend automatically includes the new provider in its dropdown when the WebSocket URL pattern matches

The provider must:

- Accept audio and text from the WebSocket
- Forward them to the external service
- Emit normalized `SessionEvent` objects via `context.emit()`
- Handle tool-use requests if the external service supports function calling
