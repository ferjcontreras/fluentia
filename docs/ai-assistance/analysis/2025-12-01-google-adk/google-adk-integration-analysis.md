# Google ADK Integration Analysis

## Goal

Integrate Google ADK-based voice agent functionality from `/home/federico/temp/avature-bidi-demo` into this repository. Enable demos of both AWS Bedrock and Google ADK implementations, including the web UI from the alternative repository.

## Current State

### This Repository (livoia)

- Real-time voice agent using AWS Bedrock Nova Sonic
- Three-layer architecture: Clients → Modules → Agent
- Audio I/O via PyAudio (local microphone/speaker)
- CLI demo script: `scripts/voice_interview_agent_demo.py`
- Custom event system (`SpeechEvents`) for text output, audio output, tool use
- Tool framework with `BaseTool` and `ToolProcessor`

### Alternative Repository (avature-bidi-demo)

- Real-time voice agent using Google ADK with Gemini models
- Google ADK handles streaming, session management, and event serialization
- Audio I/O via Web Audio API (browser-based)
- Web UI with WebSocket communication
- FastAPI backend (~250 lines) with two concurrent async tasks (upstream/downstream)
- AudioWorklet processors for low-latency audio in browser

## Architecture Differences

| Aspect | livoia (Bedrock) | avature-bidi-demo (Google ADK) |
|--------|------------------|-------------------------------|
| LLM Provider | AWS Bedrock Nova Sonic | Google Gemini |
| Abstraction | Custom Python clients | Google ADK library |
| Audio Transport | PyAudio callbacks | WebSocket binary frames |
| Demo Interface | Command-line | Browser-based UI |
| Session Management | VoiceAgent state | ADK SessionService |
| Backend Complexity | ~1500 lines | ~250 lines |

## Technical Observations

### Audio Pipeline Differences

**Bedrock (this repo):**
- PyAudio input callback runs in audio thread
- Uses `asyncio.run_coroutine_threadsafe()` to bridge threads
- Output via PyAudio stream write

**Google ADK (alternative):**
- Browser captures audio via `getUserMedia()`
- AudioWorklet converts Float32 → PCM 16-bit
- Binary WebSocket frames sent to server
- Server wraps in ADK `Blob` type and sends to `LiveRequestQueue`

### Event Models

**Bedrock events:**
- `SpeechEvents.TextOutput` (role, content)
- `SpeechEvents.AudioOutput` (audio_bytes)
- `SpeechEvents.ToolUse` (tool_use_id, tool_name, tool_input)
- `SpeechEvents.ContentEnd` (content_type)

**Google ADK events:**
- `Content` with `Part` objects (text, inline_data)
- `InputTranscription` / `OutputTranscription`
- `TurnComplete`, `Interrupted`
- `UsageMetadata`

### Web UI Components (from alternative repo)

Located in `app/static/`:
- `index.html` - Main UI layout
- `js/app.js` (~987 lines) - WebSocket handling, message rendering, event console
- `js/audio-recorder.js` - Microphone capture setup
- `js/audio-player.js` - Speaker playback setup
- `js/pcm-recorder-processor.js` - AudioWorklet for input (16kHz)
- `js/pcm-player-processor.js` - AudioWorklet for output (24kHz, ring buffer)

### Dependencies Required for Google ADK

From alternative repo's `pyproject.toml`:
- `google-genai` - Google ADK package
- `fastapi` - Already present in this repo
- `uvicorn` - Already present in this repo

### Configuration (Google ADK)

Environment variables:
- `GOOGLE_GENAI_USE_VERTEXAI` - TRUE for Vertex AI, FALSE for Gemini API
- `GOOGLE_API_KEY` - API key for Gemini API
- `GOOGLE_CLOUD_PROJECT` / `GOOGLE_CLOUD_LOCATION` - For Vertex AI

## Integration Challenges

1. **Audio transport mismatch**: Bedrock uses PyAudio (local), web UI uses WebSocket (remote)
2. **Event model mapping**: Different event structures between providers
3. **Session semantics**: ADK has built-in session resumption; Bedrock implementation does not
4. **Dual demo modes**: Supporting both CLI (existing) and web UI (new)

## References

- Bedrock client: `src/livoia/clients/speech/bedrock_sonic.py`
- Voice agent: `src/livoia/agent/voice_agent.py`
- CLI demo: `scripts/voice_interview_agent_demo.py`
- Alternative repo: `/home/federico/temp/avature-bidi-demo`
- Alternative backend: `/home/federico/temp/avature-bidi-demo/app/main.py`
- Alternative UI: `/home/federico/temp/avature-bidi-demo/app/static/`
