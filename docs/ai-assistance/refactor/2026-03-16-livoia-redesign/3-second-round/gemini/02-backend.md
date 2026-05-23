# Backend & Protocol Design

## Application Initialization

The FastAPI application is dynamically assembled using a factory pattern (`create_app()`). This ensures configuration is loaded deterministically at startup and facilitates clean testing environments.

### Unified Endpoint Structure

The core voice interface is a single parameterized WebSocket endpoint:

```
/ws/{provider_name}/{agent_profile}/{user_id}/{session_id}
```

- `provider_name`: Resolves to the specific LLM integration (e.g., `google`, `bedrock`).
- `agent_profile`: Resolves against the `AgentRegistry` to determine the system prompt structure, behavior rules, and allowed tools (e.g., `interviewer`, `scheduler`, `assistant`).
- `user_id` & `session_id`: Tracking and tracing identifiers.

## The WebSocket Protocol (v1)

The communication protocol between the frontend client and the backend server relies on a structured, provider-agnostic JSON/Binary hybrid design.

### Client -> Server (Upstream)

1. **Session Configuration (First Message Only)**
   Sent immediately after the WebSocket connection opens.
   ```json
   {
     "type": "prompt_config",
     "variables": {
       "user_name": "Alice",
       "company_name": "Avature",
       "custom_instructions": "Focus on python skills."
     }
   }
   ```
   *Note: Tools are determined entirely by the `agent_profile` path parameter and backend configuration, preventing client-side spoofing of unauthorized tool usage.*

2. **Continuous Audio Stream**
   Raw PCM 16-bit, 16kHz audio sent as pure binary WebSocket frames.

3. **Text Fallback / Injection**
   ```json
   {
     "type": "text_input",
     "text": "Hello there"
   }
   ```

### Server -> Client (Downstream)

The server emits JSON frames. The `SessionOrchestrator` normalizes all provider-specific SDK responses into these standard types:

1. **Audio Playback**
   ```json
   {
     "type": "audio_output",
     "mimeType": "audio/pcm;rate=24000",
     "data": "<base64_encoded_audio>"
   }
   ```

2. **Transcription Updates**
   Used to render the conversation UI.
   ```json
   {
     "type": "transcription",
     "source": "user", // or "agent"
     "text": "Hello there",
     "is_final": true
   }
   ```

3. **Turn & Interruption Semantics**
   ```json
   {
     "type": "turn_status",
     "status": "completed" // or "interrupted"
   }
   ```

4. **Tool Transparency (Crucial for UI Extensions)**
   Emitted when the LLM decides to use a tool, and when that tool completes. Allows the frontend to display spinners or status messages independent of the voice stream.
   ```json
   {
     "type": "tool_event",
     "event": "started", // "progress", "completed", "failed"
     "tool_name": "schedule_interview",
     "context": { "candidate": "Alice", "time": "Tomorrow 10 AM" }
   }
   ```

## Provider Adapter Contracts

To support multiple LLMs seamlessly, every provider must implement the `BaseProvider` ABC.

```python
class BaseProvider(abc.ABC):

    @abc.abstractmethod
    async def initialize_session(self, system_prompt: str, enabled_tools: list[dict]) -> None:
        """Connect to the LLM backend with the rendered prompt and tool schemas."""
        pass

    @abc.abstractmethod
    async def send_audio(self, pcm_data: bytes) -> None:
        """Stream client audio to the LLM."""
        pass

    @abc.abstractmethod
    async def send_text(self, text: str) -> None:
        """Send a text utterance to the LLM."""
        pass

    @abc.abstractmethod
    async def send_tool_result(self, tool_id: str, result: dict) -> None:
        """Provide the output of an executed tool back to the LLM."""
        pass

    @abc.abstractmethod
    async def receive_events(self) -> AsyncGenerator[SystemEvent, None]:
        """
        Yield normalized SystemEvents (AudioOutput, TextTranscription,
        ToolInvocationRequest, etc.) as they arrive from the LLM.
        """
        pass
```

### The Orchestration Loop

Inside `app.py`'s websocket handler, the `SessionOrchestrator` runs two concurrent `asyncio.Task`s:

1. **The Upstream Task**: Constantly reads frames from the WebSocket. Converts binary to `send_audio`, and JSON to `send_text`.
2. **The Downstream Task**: Iterates over `provider.receive_events()`. If it receives an `AudioOutput`, it forwards it to the frontend. If it receives a `ToolInvocationRequest`, it triggers the tool execution pipeline (described in the Tools & Agents spec), while allowing the audio stream to continue unimpeded.
