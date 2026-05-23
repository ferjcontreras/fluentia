# Backend Design

## Application Factory (`app.py`)

The entry point is `create_app() -> FastAPI`, following the same factory pattern as the PoC.

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Serve `index.html` |
| GET | `/favicon.ico` | Return 204 (no favicon) |
| GET | `/health` | Health check (`{"status": "healthy"}`) |
| WS | `/ws/{provider}/{user_id}/{session_id}` | Voice conversation WebSocket |

### Key Change: Unified WebSocket Endpoint

The PoC has separate endpoints per provider (`/ws/google/...` and `/ws/bedrock/...`). The new design uses a **single parameterized endpoint**:

```
/ws/{provider}/{user_id}/{session_id}?proactivity=true&affective_dialog=true
```

The `provider` path parameter selects the provider implementation. This is cleaner and makes adding providers trivial.

### Request Flow

```
1. Client connects to /ws/{provider}/{user_id}/{session_id}
2. Server accepts WebSocket
3. Server receives first text message: prompt_config JSON
4. Server renders system prompt from prompt_config
5. Server looks up provider by name and delegates the session
6. Provider handles bidirectional audio/text/events
7. On disconnect, provider cleans up resources
```

### Application Startup

```python
def create_app() -> FastAPI:
    app = FastAPI(title="Livoia", description="Live Voice Agent")

    # Load configuration
    config = AppConfig()

    # Initialize providers
    providers: dict[str, BaseProvider] = {
        "google": GoogleProvider(config.google),
        "bedrock": BedrockProvider(config.bedrock),
    }

    # Mount static files
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    async def root() -> FileResponse: ...

    @app.get("/health")
    async def health() -> dict[str, str]: ...

    @app.websocket("/ws/{provider}/{user_id}/{session_id}")
    async def websocket_endpoint(
        websocket: WebSocket,
        provider: str,
        user_id: str,
        session_id: str,
    ) -> None:
        if provider not in providers:
            await websocket.close(code=4000, reason=f"Unknown provider: {provider}")
            return

        await websocket.accept()
        system_prompt = await receive_prompt_config(websocket)
        await providers[provider].handle_session(websocket, user_id, session_id, system_prompt)

    return app
```

## Provider ABC (`providers/base.py`)

```python
class BaseProvider(abc.ABC):
    """Base class for voice conversation providers.

    Each provider encapsulates the complete lifecycle of a voice
    conversation session over WebSocket.
    """

    @abc.abstractmethod
    async def handle_session(
        self,
        websocket: WebSocket,
        user_id: str,
        session_id: str,
        system_prompt: str,
    ) -> None:
        """Handle a complete WebSocket voice conversation session.

        This method is responsible for:
        - Setting up the provider-specific connection
        - Running upstream (client -> provider) and downstream (provider -> client) tasks
        - Cleaning up resources on disconnect

        Args:
            websocket: The accepted WebSocket connection.
            user_id: User identifier for the session.
            session_id: Session identifier.
            system_prompt: The rendered system prompt for the conversation.
        """
        raise NotImplementedError
```

## Google Provider (`providers/google.py`)

Encapsulates all Google ADK logic that currently lives inline in `app.py`.

### Responsibilities
- Create Google ADK `Agent` with the system prompt
- Create `Runner` and `LiveRequestQueue` per session
- Handle WebSocket query parameters: `proactivity`, `affective_dialog`
- Run upstream task (WebSocket -> LiveRequestQueue) and downstream task (Runner -> WebSocket)
- Support both native audio and text response modalities

### Configuration

```python
class GoogleProviderConfig(BaseSettings):
    model: str = "gemini-2.5-flash-native-audio-preview-09-2025"
    use_vertex_ai: bool = False
    api_key: str | None = None
    cloud_project: str | None = None
    cloud_location: str = "us-central1"

    model_config = {"env_prefix": "GOOGLE_"}

    @property
    def is_native_audio(self) -> bool:
        return "native-audio" in self.model.lower()
```

### Design Notes
- The `InMemorySessionService` is shared across connections (created once at provider init)
- The `Agent` is created per connection (since the system prompt varies)
- The `Runner` is created per connection (tied to the per-connection agent)

## Bedrock Provider (`providers/bedrock/`)

This is the most complex provider, split into multiple files:

### `provider.py` - BedrockProvider

The WebSocket adapter (currently `bedrock_adapter.py`). Bridges between WebSocket and the Nova Sonic client.

Responsibilities:
- Create and configure the Nova Sonic client
- Convert WebSocket binary frames to audio input
- Convert Nova Sonic events to WebSocket JSON events
- Handle barge-in detection
- Manage connection lifecycle

### `client.py` - NovaSonicClient

The streaming client (currently `bedrock_sonic.py`). Direct integration with AWS Bedrock.

Responsibilities:
- Initialize bidirectional stream with Bedrock
- Send session, prompt, system prompt, and audio events
- Process response events (text, audio, tool use, content end)
- Tool result submission

### `config.py` - BedrockProviderConfig

```python
class BedrockProviderConfig(BaseModel):
    region: str = "us-east-1"
    model_id: str = "amazon.nova-2-sonic-v1:0"
    voice_id: str = "matthew"
    input_sample_rate: int = 16000
    output_sample_rate: int = 24000
    language: str | None = None
```

### Speech Events

The `SpeechEvents` namespace (currently in `clients/speech/base.py`) moves into `providers/bedrock/` since it's Bedrock-specific. Google ADK has its own event format.

```python
class SpeechEvents:
    class Base(BaseModel):
        event_type: str

    class TextOutput(Base): ...
    class AudioOutput(Base): ...
    class ToolUse(Base): ...
    class ContentEnd(Base): ...
```

### WebSocket Event Format

The `WebSocketEvent` model (currently in `bedrock_adapter.py`) is the wire format sent to the frontend:

```python
class WebSocketEvent(BaseModel):
    content: dict[str, Any] | None = None
    input_transcription: dict[str, Any] | None = Field(default=None, alias="inputTranscription")
    output_transcription: dict[str, Any] | None = Field(default=None, alias="outputTranscription")
    turn_complete: bool | None = Field(default=None, alias="turnComplete")
    interrupted: bool | None = None
    author: str | None = None
```

This format is designed to be compatible with Google ADK's event format, so the frontend handles both providers uniformly.

## Prompt Management (`prompts/interview.py`)

The prompt module is straightforward:

```python
DEFAULT_AGENT_NAME: str = "Taylor"
DEFAULT_COMPANY_NAME: str = "Avature"
DEFAULT_QUESTIONS: str = ...
DEFAULT_GUIDELINES: str = ...

def render_interview_prompt(
    agent_name: str = DEFAULT_AGENT_NAME,
    company_name: str = DEFAULT_COMPANY_NAME,
    questions: str = DEFAULT_QUESTIONS,
    guidelines: str = DEFAULT_GUIDELINES,
) -> str:
    """Render the interview agent system prompt."""
    ...
```

### Future Extension Points
- Additional prompt types (general assistant, customer support, etc.)
- Prompt rendering from Jinja2 templates
- Prompt preview endpoint for the "Prompt" tab

## WebSocket Protocol

### Connection
```
ws://{host}/ws/{provider}/{user_id}/{session_id}?proactivity=true&affective_dialog=true
```

### First Message (Client -> Server)
```json
{
  "type": "prompt_config",
  "agent_name": "Taylor",
  "company_name": "Avature",
  "questions": "Question 1: ...\n\nQuestion 2: ...",
  "guidelines": "- Ask questions naturally..."
}
```

### Audio (Client -> Server)
Binary WebSocket frames containing raw PCM audio (16-bit, mono, 16kHz).

### Text (Client -> Server)
```json
{"type": "text", "text": "Hello"}
```

### Image (Client -> Server, Google only)
```json
{"type": "image", "data": "<base64>", "mimeType": "image/jpeg"}
```

### Events (Server -> Client)
JSON text frames. The format is shared between providers:

```json
// Audio chunk
{"content": {"parts": [{"inlineData": {"mimeType": "audio/pcm;rate=24000", "data": "<base64>"}}]}, "author": "agent"}

// Input transcription
{"inputTranscription": {"text": "Hello", "finished": true}, "author": "user"}

// Output transcription
{"outputTranscription": {"text": "Hi there!", "finished": true}, "author": "agent"}

// Turn complete
{"turnComplete": true, "author": "system"}

// Interrupted (barge-in)
{"interrupted": true, "author": "system"}
```

## Logging

Simple Python logging (as in the current web demo):

```python
_log_level_name: str = os.environ.get("LIVOIA_LOG_LEVEL", "WARNING").upper()
logging.basicConfig(level=_log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
```

Cap noisy third-party loggers to WARNING. No Logstash formatter, no structured logging (can be added later if needed).

## Error Handling

- Provider not found: Close WebSocket with code 4000 and reason
- Prompt config timeout/malformed: Use defaults (graceful degradation)
- Provider connection failure: Log error, close WebSocket
- Mid-session errors: Log, attempt cleanup, close WebSocket
- All errors in streaming tasks are caught and logged (no unhandled exceptions crashing the server)
