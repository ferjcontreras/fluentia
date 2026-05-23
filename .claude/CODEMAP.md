# Repository Navigation Map (CODEMAP)

This document enables hierarchical exploration of the codebase. Start here, then drill into the actual source code.

## How to Use

1. **Read this file first** to identify which area of the codebase is relevant to your task.
2. **Read the actual source code** at the file references provided.

---

## Level 0: Major Areas

### 1. Configuration
**When to look here**: Application settings, provider configs, environment variables.

**Key files**:
- `src/fluentia/config.py` - `AppConfig`, `GoogleProviderConfig`, `BedrockProviderConfig` (Pydantic BaseSettings); `GoogleModelSpec`, `GOOGLE_MODEL_CATALOG` (model capability catalog)

---

### 2. Providers (Voice Session Backends)
**When to look here**: Adding a new voice provider, debugging provider-specific issues, understanding the provider lifecycle.

**Key concepts**: `BaseProvider` ABC with `handle_session()`. Each provider owns its full session lifecycle. `SessionContext` provides dependency-injected `emit()` callback.

**Key files**:
- `src/fluentia/providers/base.py` - `BaseProvider` ABC, `SessionContext` dataclass
- `src/fluentia/providers/google.py` - `GoogleProvider` (Google ADK / Gemini)
- `src/fluentia/providers/bedrock/provider.py` - `BedrockProvider` (AWS Nova Sonic)
- `src/fluentia/providers/bedrock/client.py` - `NovaSonicClient` (low-level streaming)
- `src/fluentia/providers/bedrock/config.py` - `BedrockSessionConfig`
- `src/fluentia/providers/google_tools.py` - `create_adk_tool_wrapper()` (ADK tool bridge)

---

### 3. Session & Events
**When to look here**: WebSocket orchestration, event protocol, message serialization.

**Key concepts**: Normalized `SessionEventType` enum, versioned JSON protocol (v1), `SessionManager` orchestrates WebSocket <-> Provider.

**Key files**:
- `src/fluentia/session/events.py` - `SessionEventType`, `SessionEvent`
- `src/fluentia/session/protocol.py` - `serialize_event()`, `deserialize_client_message()`
- `src/fluentia/session/manager.py` - `SessionManager`

---

### 4. Agents & Prompts
**When to look here**: Adding a new agent type, modifying prompt templates, understanding agent configuration.

**Key concepts**: `AgentDefinition` frozen dataclass with Jinja2 templates. Agents are configuration, not code. `AgentRegistry` for registration and lookup.

**Key files**:
- `src/fluentia/agents/base.py` - `FieldMetadata`, `AgentDefinition`
- `src/fluentia/agents/registry.py` - `AgentRegistry`
- `src/fluentia/agents/english_teacher.py` - `english_teacher` instance
- `src/fluentia/agents/templates/english_teacher.j2` - Jinja2 prompt template

---

### 5. Tools
**When to look here**: Adding tools that LLMs can invoke, tool execution, tool specs.

**Key concepts**: `BaseTool` ABC, `ToolProcessor` for registration/dispatch, `ToolResult` with `ToolState`. Provider-agnostic specs (each provider formats for its own API).

**Key files**:
- `src/fluentia/tools/base.py` - `BaseTool` ABC
- `src/fluentia/tools/state.py` - `ToolState`, `ToolResult`
- `src/fluentia/tools/processor.py` - `ToolProcessor`
- `src/fluentia/tools/implementations/date_time.py` - `GetDateAndTimeTool`
- `src/fluentia/tools/implementations/weather.py` - `GetWeatherTool`

---

### 6. Observability
**When to look here**: Logging, metrics, health checks.

**Key files**:
- `src/fluentia/observability/logging.py` - structlog config, `configure_logging()`, `log_config_summary()`
- `src/fluentia/observability/metrics.py` - `MetricsCollector` Protocol, `LoggingMetricsCollector`
- `src/fluentia/observability/health.py` - `get_health()`, `get_readiness()`

---

### 7. Application Entry Points
**When to look here**: FastAPI setup, WebSocket endpoint, static file serving.

**Key files**:
- `src/fluentia/app.py` - `create_app()` factory with lifespan handler
- `src/fluentia/main.py` - CLI entry point

---

### 8. Frontend
**When to look here**: Browser UI, WebSocket client, audio worklets.

**Key files**:
- `src/fluentia/static/index.html` - Main HTML page
- `src/fluentia/static/js/app.js` - WebSocket client, UI logic, v1 protocol handling
- `src/fluentia/static/js/audio-worklet.js` - Audio player/recorder worklet management
- `src/fluentia/static/audio/audio-processor.js` - PCM recorder AudioWorklet processor
- `src/fluentia/static/css/styles.css` - UI styles

---

### 9. Testing
**When to look here**: Writing tests, test fixtures, test patterns.

**Key files**:
- `tests/conftest.py` - Global fixtures
- `tests/unit/config/test_config.py` - Config tests
- `tests/unit/tools/test_processor.py` - Tool processor tests
- `tests/unit/agents/test_agents.py` - Agent and registry tests
- `tests/unit/session/test_events.py` - Event and protocol tests
- `tests/unit/observability/` - Health and metrics tests

---

### 10. DevOps & Configuration
**When to look here**: Dependencies, CI/CD, Docker, code quality.

**Key files**:
- `pyproject.toml` - Dependencies, tool config (ruff, mypy, pylint, pytest)
- `tox.ini` - Test orchestration
- `Dockerfile` - Multi-stage production build
- `docker-compose.yml` - Local development
- `.gitlab-ci.yml` - CI pipeline
- `check_code.sh` - Local quality check script
- `.pre-commit-config.yaml` - Git hooks

---

## Cross-Reference Quick Lookup

| If you need to...                          | Start at              |
|--------------------------------------------|-----------------------|
| Add a new voice provider                   | Providers             |
| Add a new agent type                       | Agents & Prompts      |
| Add a new tool                             | Tools                 |
| Add a WebSocket event type                 | Session & Events      |
| Modify the browser UI                      | Frontend              |
| Change app configuration                   | Configuration         |
| Write or modify tests                      | Testing               |
| Understand the voice session flow          | Session & Events then Providers |
| Modify CI/CD or Docker                     | DevOps                |

---

## Keeping This Map Current

**Update the codemap when you make structural changes** (new files, renamed classes, moved modules).

When to update:
- New file, class, or module added
- File moved or renamed
- New area or subsystem introduced

When not to update:
- Minor edits within existing functions
- Documentation-only changes
- Test additions following existing patterns
