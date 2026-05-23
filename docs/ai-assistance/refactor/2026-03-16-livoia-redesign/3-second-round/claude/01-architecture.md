# 1. Architecture

## Design Principles

1. **Single package, clear domains.** One installable package (`livoia`) with internal domains separated by responsibility, not by deployment boundary.
2. **Providers own their lifecycle.** Each voice provider (Google, Bedrock) manages its own connection to the external service. The session layer coordinates but does not micro-manage.
3. **Agents are configuration, not code.** An "agent" (interviewer, scheduler, assistant) is defined by a prompt template, a set of enabled tools, and provider-specific settings -- not by a separate code path.
4. **Normalize at boundaries.** Provider-specific data stays inside provider code. Everything else works with normalized event types.
5. **No dead code.** Every module has at least one consumer and a test. Interfaces are designed for extensibility but not implemented until needed.

## Package Structure

```
src/livoia/
    __init__.py
    app.py                          # FastAPI application factory
    config.py                       # Pydantic BaseSettings hierarchy

    session/                        # WebSocket session lifecycle
        __init__.py
        manager.py                  # Session orchestration: accept WS, route to provider, relay events
        events.py                   # Normalized event types (SessionEvent, SessionEventType)
        protocol.py                 # WebSocket message serialization, protocol version

    providers/                      # Voice provider adapters
        __init__.py
        base.py                     # BaseProvider ABC
        google.py                   # Google ADK (Gemini) adapter
        bedrock/                    # AWS Bedrock Nova Sonic adapter
            __init__.py
            provider.py             # BedrockProvider (implements BaseProvider)
            client.py               # Low-level Nova Sonic streaming client
            config.py               # Bedrock-specific configuration

    agents/                         # Agent definitions (prompt + tools + settings)
        __init__.py
        registry.py                 # AgentRegistry: lookup agent definitions by name
        base.py                     # AgentDefinition dataclass
        interviewer.py              # Interviewer agent definition
        templates/                  # Jinja2 prompt templates
            interviewer.j2

    tools/                          # Tool framework
        __init__.py
        base.py                     # BaseTool ABC
        processor.py                # ToolProcessor registry and dispatch
        state.py                    # ToolState enum, ToolResult dataclass
        implementations/            # Built-in tool implementations
            __init__.py
            date_time.py            # GetDateAndTimeTool

    observability/                  # Logging, health, metrics
        __init__.py
        logging.py                  # Structured JSON logging with correlation IDs
        health.py                   # /health and /ready endpoint handlers
        metrics.py                  # MetricsCollector protocol and logging-based implementation

    static/                         # Frontend assets (served by FastAPI)
        index.html
        css/
            styles.css
        js/
            app.js
            audio-worklet.js
        audio/
            audio-processor.js      # AudioWorklet processor
```

## Layer Responsibilities

| Layer | Package | Responsibility | Depends On |
|-------|---------|---------------|------------|
| **Application** | `app.py` | FastAPI factory, route registration, static file mount, lifespan | `config`, `session`, `observability` |
| **Session** | `session/` | WebSocket connection lifecycle, provider routing, event normalization and relay | `providers/base`, `agents/registry`, `session/events` |
| **Providers** | `providers/` | SDK-specific connection management, audio streaming, tool execution, emitting normalized events | `session/events`, `tools/`, `agents/base` |
| **Agents** | `agents/` | Agent definitions (prompt template + tool list + settings), prompt rendering | `tools/base` (for tool references) |
| **Tools** | `tools/` | Tool registration, dispatch, execution, result types | Nothing (leaf dependency) |
| **Observability** | `observability/` | Structured logging, health endpoints, metrics collection | Nothing (leaf dependency) |
| **Configuration** | `config.py` | Environment variable loading, validation, typed settings | Nothing (leaf dependency) |

## Dependency Flow

```
app.py
 +-- config.py
 +-- observability/
 +-- session/manager.py
      +-- session/events.py
      +-- session/protocol.py
      +-- providers/base.py (ABC)
      +-- agents/registry.py
           +-- agents/base.py
           +-- agents/interviewer.py
                +-- agents/templates/interviewer.j2
 +-- providers/google.py
      +-- session/events.py (to emit normalized events)
      +-- agents/base.py (to read agent definition)
 +-- providers/bedrock/
      +-- session/events.py (to emit normalized events)
      +-- agents/base.py (to read agent definition)
      +-- tools/processor.py (Bedrock handles tool execution)
```

**Key constraint**: No circular dependencies. Providers depend on `session/events.py` (to emit events), and the session manager depends on `providers/base.py` (the ABC). This is resolved by dependency inversion: the session manager holds a `BaseProvider` reference; concrete providers implement it.

## What Is Excluded

The following PoC features are intentionally not carried forward:

| Feature | Reason |
|---------|--------|
| LLM text generation clients (OpenAI, Skynet, Bedrock chat) | General ML library, not voice agent |
| Embedding clients and EncoderCaller | General ML library, not voice agent |
| Two-tier caching (file + Redis) | No caching needed for stateless voice sessions |
| CLI audio (PyAudio, AudioStreamer) | Browser-only deployment |
| Camera/image capture | Out of scope for stage 1 |
| Rate limiting (slowapi) | Handled at infrastructure level |
| Prometheus metrics endpoint | Replaced by metrics hook pattern |
| Agent orchestration (langchain-based) | Replaced by agents/ framework |
