# 2. Providers

## Provider Abstraction

Each voice provider adapts an external SDK (Google ADK, AWS Bedrock) into a uniform session interface. Providers own their full session lifecycle -- connecting to the external service, streaming audio, handling tool calls, and translating SDK events into normalized `SessionEvent` objects.

### BaseProvider ABC

```python
class BaseProvider(abc.ABC):
    """Abstract base class for voice conversation providers."""

    @abc.abstractmethod
    async def handle_session(
        self,
        websocket: WebSocket,
        session_context: SessionContext,
    ) -> None:
        """Run a complete voice session over the given WebSocket.

        The provider:
        1. Connects to its external service using the agent definition's prompt
        2. Streams audio from the WebSocket to the external service
        3. Receives audio/text/events from the external service
        4. Emits normalized SessionEvents via session_context.emit()
        5. Handles tool calls if the agent definition includes tools
        6. Cleans up on disconnect or error

        Args:
            websocket: The client WebSocket connection (already accepted).
            session_context: Shared context including user/session IDs,
                agent definition, and the emit callback for normalized events.
        """
        raise NotImplementedError("Subclasses must implement `handle_session()`")
```

### SessionContext

```python
@dataclass(frozen=True)
class SessionContext:
    """Shared context passed to a provider during a voice session."""

    user_id: str
    session_id: str
    agent_definition: AgentDefinition       # Prompt, tools, settings
    emit: Callable[[SessionEvent], Awaitable[None]]  # Emit normalized events
```

The `SessionContext` is the seam between the session layer and the provider. The session manager creates it; the provider consumes it. The `emit` callback allows the session manager to intercept, log, and relay events without the provider knowing how they are delivered.

### Why Providers Own Their Lifecycle

Google ADK and Bedrock have fundamentally different session models:

- **Google ADK**: The SDK's `Runner` manages the session lifecycle, including connection, streaming, and event dispatch. The provider wraps this with minimal intervention.
- **Bedrock Nova Sonic**: The session is built from lower-level primitives (HTTP/2 streaming, event framing). The provider manages connection, audio encoding, event parsing, and tool execution explicitly.

A fine-grained interface (separate `connect()`, `send_audio()`, `receive_events()`, `close()` methods) would force Google ADK into a lifecycle model it doesn't natively support. Letting each provider own its lifecycle avoids fighting the SDK.

---

## Google Provider

**File**: `providers/google.py` (single file -- complexity is managed by the ADK SDK)

### Responsibilities

1. Create a Google ADK `Agent` with the agent definition's rendered prompt
2. Configure response modalities based on model capabilities:
   - Native audio models (`*-native-audio-*`): `response_modalities=["AUDIO"]`
   - Half-cascade models: `response_modalities=["TEXT"]`
3. Create a `Runner` and `LiveRequestQueue` per session
4. Receive audio from WebSocket, forward to the live request queue
5. Receive events from the Runner, emit as normalized `SessionEvent` objects
6. Handle provider-specific query parameters (`proactivity`, `affective_dialog`) extracted from the WebSocket request

### Event Mapping

| Google ADK Event | SessionEventType |
|-----------------|-----------------|
| Audio content part | `AUDIO` |
| Text content part | `TEXT` |
| Partial/complete user transcript | `INPUT_TRANSCRIPTION` |
| Partial/complete agent transcript | `OUTPUT_TRANSCRIPTION` |
| Turn complete signal | `TURN_COMPLETE` |
| Interrupted signal | `INTERRUPTED` |

### Provider-Specific Settings

Google ADK supports features not available on Bedrock:

- `proactivity`: Agent can speak unprompted (native audio models only)
- `affective_dialog`: Emotional awareness in responses (native audio models only)

These are extracted from WebSocket query parameters by the provider itself. The `BaseProvider` interface does not expose them -- they are an internal concern of the Google provider.

---

## Bedrock Provider

**File**: `providers/bedrock/` (multi-file -- higher complexity due to low-level streaming)

### Module Structure

```
providers/bedrock/
    __init__.py             # Exports BedrockProvider
    provider.py             # BedrockProvider (implements BaseProvider)
    client.py               # NovaSonicClient: HTTP/2 streaming, event framing
    config.py               # BedrockProviderConfig
```

### Responsibilities

**BedrockProvider** (`provider.py`):
1. Create a `NovaSonicClient` with Bedrock credentials from config
2. Render the agent definition's prompt and format tool specs for Nova Sonic
3. Connect to Bedrock Nova Sonic, passing system prompt and tool configuration
4. Forward audio from WebSocket to `NovaSonicClient.send_audio()`
5. Process events from `NovaSonicClient.receive_events()`:
   - Audio output: Emit as `AUDIO` event
   - Transcriptions: Emit as `INPUT_TRANSCRIPTION` or `OUTPUT_TRANSCRIPTION`
   - Tool use requests: Execute via `ToolProcessor`, send results back to Bedrock
   - Content end: Emit as `TURN_COMPLETE`
   - Barge-in: Emit as `INTERRUPTED`
6. Clean up on disconnect

**NovaSonicClient** (`client.py`):
- Low-level HTTP/2 bidirectional streaming to Bedrock
- AWS SigV4 authentication
- Event framing (content blocks, audio chunks, tool use events)
- Audio format: 16 kHz PCM input, 24 kHz output

### Tool Execution

Bedrock is currently the only provider that supports tool execution during voice sessions. When Nova Sonic requests a tool call:

1. The provider extracts the tool name and input from the event
2. It dispatches to `ToolProcessor.execute(tool_name, input_data)`
3. It sends the `ToolResult` back to the Bedrock stream
4. Nova Sonic incorporates the result into its response

Google ADK tool support can be added later by wiring the same `ToolProcessor` into the Google provider.

### Tool Spec Formatting

Nova Sonic requires a specific JSON format for tool specifications:

```json
{
    "toolSpec": {
        "name": "getDateAndTimeTool",
        "description": "Get the current date and time",
        "inputSchema": {
            "json": "{\"type\": \"object\", \"properties\": {}, \"required\": []}"
        }
    }
}
```

Note that `inputSchema.json` is a **JSON string**, not a nested object. This formatting is Bedrock-specific and is handled inside the Bedrock provider, not in the tool framework. The `BaseTool.input_schema` property returns a plain `dict`; the provider serializes it as needed.

When Google ADK tool support is added, the Google provider will format tool specs according to Google's API requirements, using the same `BaseTool.input_schema` as input.

---

## Adding a New Provider

To add a new voice provider (e.g., Azure Speech, Eleven Labs):

1. **Create the provider file** (or directory if complex) under `providers/`.
2. **Implement `BaseProvider`**: The `handle_session()` method connects to the service, streams audio, and emits `SessionEvent` objects.
3. **Add configuration**: Add a provider-specific config class to `config.py`.
4. **Register the route**: The session manager routes based on the `provider` path parameter. Adding a new provider name to the routing map is a one-line change.
5. **Write tests**: Unit tests with mocked SDK, integration test with real service.

No changes are needed to the session layer, agent framework, tool framework, or frontend.
