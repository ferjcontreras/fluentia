# Google ADK Integration Refactor Plan

## Objective

Add Google ADK-based voice agent functionality alongside existing AWS Bedrock implementation. Import web UI from alternative repository to enable browser-based demos of both providers.

## Current Architecture

```
src/livoia/
├── agent/voice_agent.py      # Orchestrates Bedrock voice sessions
├── clients/speech/           # Bedrock Nova Sonic client
├── modules/speech_caller.py  # Speech module with tool handling
├── audio/streamer.py         # PyAudio I/O (local only)
└── tools/                    # Tool framework

scripts/
└── voice_interview_agent_demo.py  # CLI demo
```

**Limitation**: Demo requires local execution (PyAudio). No browser-based demo capability.

## Target Architecture

```
src/livoia/
├── agent/voice_agent.py           # Existing (unchanged)
├── clients/speech/                # Existing (unchanged)
├── modules/speech_caller.py       # Existing (unchanged)
├── audio/streamer.py              # Existing (unchanged)
└── tools/                         # Existing (unchanged)

src/livoia_google/
├── agent.py                       # Google ADK agent definition
└── websocket_handler.py           # WebSocket endpoint for ADK

src/livoia_web/
├── app.py                         # FastAPI app with WebSocket routes
├── adapters/
│   ├── bedrock_adapter.py         # Bridges VoiceAgent to WebSocket
│   └── google_adapter.py          # Wraps Google ADK for WebSocket
└── static/                        # Web UI files
    ├── index.html
    ├── css/
    └── js/

scripts/
└── voice_interview_agent_demo.py  # Existing CLI demo (unchanged)
```

## Implementation Phases

### Phase 1: Import Google ADK Module

**Scope**: Port Google ADK functionality from alternative repository.

**Steps**:
1. Add `google-genai` dependency to `pyproject.toml`
2. Create `src/livoia_google/` package
3. Port agent definition from `avature-bidi-demo/app/google_search_agent/agent.py`
4. Port WebSocket handler from `avature-bidi-demo/app/main.py`
5. Add Google ADK configuration to settings

**Validation**:
- Google ADK module loads without errors
- WebSocket endpoint accepts connections
- Audio streaming works with Gemini model

### Phase 2: Import Web UI

**Scope**: Bring web UI static files and adapt for this repository.

**Steps**:
1. Create `src/livoia_web/` package
2. Copy static files from `avature-bidi-demo/app/static/`
3. Create FastAPI app that mounts static files
4. Add provider selection dropdown to UI
5. Configure WebSocket URL to use selected provider endpoint

**Validation**:
- Web UI loads in browser
- Provider selector displays both options
- Audio recording/playback works in browser

### Phase 3: Create Bedrock WebSocket Adapter

**Scope**: Bridge existing VoiceAgent to WebSocket interface for web demos.

**Steps**:
1. Create `adapters/bedrock_adapter.py`
2. Replace PyAudio input with WebSocket receive (binary audio frames)
3. Replace PyAudio output with WebSocket send (binary audio frames)
4. Map `SpeechEvents` to JSON format compatible with web UI
5. Add WebSocket endpoint `/ws/bedrock/{session_id}`

**Validation**:
- Bedrock voice agent responds via WebSocket
- Audio flows bidirectionally through browser
- Transcription callbacks work with web UI

### Phase 4: Unified Demo Application

**Scope**: Single entry point for both providers.

**Steps**:
1. Create unified FastAPI application in `src/livoia_web/app.py`
2. Mount both `/ws/bedrock/` and `/ws/google/` endpoints
3. Add environment variable configuration for provider selection
4. Update UI to handle provider-specific event formats
5. Document demo usage

**Validation**:
- Both providers accessible from same web UI
- Provider switching works without page reload
- Demo script documented in README

## Dependencies

| Phase | Depends On |
|-------|------------|
| Phase 1 | None |
| Phase 2 | None |
| Phase 3 | Phase 2 (needs UI to test) |
| Phase 4 | Phase 1, 2, 3 |

Phases 1 and 2 can proceed in parallel.

## New Dependencies

Add to `pyproject.toml`:
```toml
[project.optional-dependencies]
google = ["google-genai>=1.0.0"]
```

## Configuration

New environment variables:
```bash
# Google ADK
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=<api-key>

# Optional: Vertex AI
GOOGLE_CLOUD_PROJECT=<project>
GOOGLE_CLOUD_LOCATION=us-central1
```

## File References

- Analysis document: `docs/ai-assistance/analysis/google-adk-integration-analysis.md`
- Alternative repository: `/home/federico/temp/avature-bidi-demo`
- Existing voice agent: `src/livoia/agent/voice_agent.py`
- Existing demo: `scripts/voice_interview_agent_demo.py`
