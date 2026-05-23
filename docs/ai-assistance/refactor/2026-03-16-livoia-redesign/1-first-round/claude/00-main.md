# Livoia Production Redesign

## Problem Statement

The current repository (`english-teacher-assistant`) is a proof-of-concept that has grown organically to include:

1. **A general ML infrastructure library** (`src/livoia/`): LLM clients, embedding clients, caching, an API layer, and utilities
2. **A voice agent framework** (`src/livoia/clients/speech/`, `src/livoia/modules/speech_caller.py`, `src/livoia/agent/`, `src/livoia/tools/`)
3. **A Google ADK integration** (`src/livoia_google/`)
4. **A web demo application** (`src/livoia_web/`)

The web demo (item 4) is the deliverable we want to take to production. It depends on items 2, 3, and a small subset of utilities from item 1. The general ML infrastructure (LLM clients, embedding clients, caching, the REST API layer) is **not used** by the web demo and should not be carried into the new project.

## Objective

Design a new production-ready repository that:

- Supports the **exact functionality** of the current web demo (`livoia_web.app:create_app`)
- Has a clean, focused architecture with no unused code
- Is Docker-deployable with Kubernetes-friendly configuration (env vars for secrets)
- Follows the same CI/CD and code quality standards (uv, ruff, mypy, pylint, tox, pre-commit)
- Is designed for extensibility (tools, additional providers, new UI tabs)

## Current Web Demo Functionality

The web demo provides a **browser-based voice conversation interface** with two providers:

### Provider 1: Google Gemini (via Google ADK)
- Uses `google-adk` library with `Agent`, `Runner`, `LiveRequestQueue`
- Supports native audio models (bidirectional audio) and text models
- Features: proactivity, affective dialog, camera/image input
- WebSocket endpoint: `/ws/google/{user_id}/{session_id}`

### Provider 2: AWS Bedrock Nova Sonic
- Uses `aws-sdk-bedrock-runtime` for bidirectional streaming
- Audio-only (no camera/image support)
- Tool execution support (date/time tool currently implemented)
- WebSocket endpoint: `/ws/bedrock/{user_id}/{session_id}`

### Shared Features
- **Settings tab**: User-configurable prompt fields (agent name, company name, questions, guidelines)
- **Prompt config**: Sent as first WebSocket message; rendered into a system prompt server-side
- **Audio**: 16kHz PCM input from browser microphone, 24kHz PCM output to browser speakers
- **Event console**: Real-time display of upstream/downstream events
- **Transcription**: Input (user) and output (agent) transcription display
- **Text input**: Alternative to voice for testing
- **Auto-reconnect**: 5-second reconnect on disconnect
- **Barge-in detection**: Bedrock provider detects user interruption

## What to Carry Forward

### Must include (used by web demo)
| Current Location | Purpose |
|---|---|
| `src/livoia_web/app.py` | FastAPI app, WebSocket endpoints |
| `src/livoia_web/adapters/bedrock_adapter.py` | Bedrock-to-WebSocket bridge |
| `src/livoia_web/prompts.py` | Prompt rendering |
| `src/livoia_web/static/` | Frontend (HTML, CSS, JS) |
| `src/livoia_google/agent.py` | Google ADK agent factory |
| `src/livoia_google/config.py` | Google agent configuration |
| `src/livoia/clients/speech/base.py` | Speech client ABC + SpeechEvents |
| `src/livoia/clients/speech/bedrock_sonic.py` | Bedrock Nova Sonic client |
| `src/livoia/modules/speech_caller.py` | Speech module with tool handling |
| `src/livoia/tools/base.py` | BaseTool ABC, ToolConfig |
| `src/livoia/tools/processor.py` | ToolProcessor |
| `src/livoia/tools/implementations/date_time.py` | Example tool |

### Must NOT include (unused by web demo)
| Current Location | Reason |
|---|---|
| `src/livoia/clients/llm/` | Not used by web demo |
| `src/livoia/clients/embedding/` | Not used by web demo |
| `src/livoia/modules/llm_caller.py` | Not used by web demo |
| `src/livoia/modules/encoder_caller.py` | Not used by web demo |
| `src/livoia/modules/base.py` | Caching base class, not used by speech |
| `src/livoia/modules/cache_store.py` | Not used by web demo |
| `src/livoia/api/` | REST API layer, not used by web demo |
| `src/livoia/audio/` | PyAudio streamer (local-only, replaced by WebSocket) |
| `src/livoia/agent/` | VoiceAgent orchestrator (local-only) |
| `src/livoia/utils/logging.py` | Logstash formatter, not used by web demo |
| `src/livoia/utils/prompt_templates.py` | Jinja2 renderer, not used by web demo |
| `src/livoia/utils/helper.py` | Resource path helpers, not used by web demo |
| `src/livoia/utils/env.py` | dotenv loader, not used by web demo |
| `scripts/` | CLI demo scripts |

## Design Documents

| Document | Description |
|---|---|
| [01-architecture.md](01-architecture.md) | New project architecture, package layout, and layer design |
| [02-backend.md](02-backend.md) | Backend design: FastAPI app, providers, WebSocket protocol |
| [03-frontend.md](03-frontend.md) | Frontend design: UI, tabs, extensibility for future features |
| [04-tools.md](04-tools.md) | Tool framework design and future tool extensibility |
| [05-configuration.md](05-configuration.md) | Configuration, environment variables, Docker, and deployment |
| [06-ci-cd.md](06-ci-cd.md) | CI/CD pipeline, code quality, testing strategy |
| [07-documentation.md](07-documentation.md) | Documentation structure and content plan |
| [08-migration-plan.md](08-migration-plan.md) | Step-by-step migration from PoC to production |

## Future Extensions (Design Considerations)

These features are **not in scope** for the initial migration but the architecture must accommodate them:

1. **Configurable tools**: Users activate tools in the UI that the LLM can invoke during conversation
2. **Orchestrator integration**: Livoia agent calls external agents (e.g., job description writer) via an Orchestrator system
3. **Prompt tab**: UI tab showing the rendered prompt with current settings
4. **Tool use tab**: UI tab providing transparency into tool invocations and results
5. **Additional providers**: Beyond Google Gemini and AWS Bedrock
6. **Web search tool**: LLM searches the web during conversation
7. **File search tool**: LLM searches and reads files from a directory
8. **Asynchronous tool results**: Long-running tools (like Orchestrator agents) that return results while conversation continues
