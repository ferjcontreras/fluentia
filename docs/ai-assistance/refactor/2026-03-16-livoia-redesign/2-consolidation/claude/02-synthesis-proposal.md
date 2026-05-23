# Synthesis Proposal: Consolidated Production Design

## 1. Guiding Principles

These principles resolve conflicts between the three variants:

1. **Ship simple, extend deliberately.** Prefer Claude's minimalism for stage 1, but incorporate structural decisions from GPT and Gemini that prevent costly refactors later.
2. **Normalize at boundaries, not everywhere.** Provider-specific complexity stays inside providers. Shared contracts exist at the edges (events, config, tool specs).
3. **No dead code, but leave clear seams.** Don't export unused frameworks. Instead, design interfaces that naturally accommodate future features without premature implementation.
4. **Production means observable.** Unlike all three variants, this synthesis treats observability as a stage-1 requirement, not a future phase.

---

## 2. Architecture

### Package Structure

Adopt Gemini's three-package layout with refinements:

```
src/livoia/
    __init__.py
    app.py                      # FastAPI factory (from Claude)
    config.py                   # Pydantic BaseSettings (from Claude)

    session/                    # Session orchestration (from GPT insight)
        __init__.py
        manager.py              # WebSocket session lifecycle
        events.py               # Normalized event types (from GPT)
        protocol.py             # WebSocket message serialization, protocol version

    providers/                  # Provider adapters (all three agree)
        __init__.py
        base.py                 # BaseProvider ABC
        google.py               # Google ADK adapter (single file, from Claude)
        bedrock/                # Bedrock adapter (multi-file, from Claude)
            __init__.py
            provider.py
            client.py
            config.py

    prompts/                    # Prompt management (from Claude)
        __init__.py
        renderer.py             # Jinja2 template rendering
        templates/              # Prompt template files

    tools/                      # Tool framework (from Claude + Gemini)
        __init__.py
        base.py                 # BaseTool ABC with async support
        processor.py            # ToolProcessor registry
        state.py                # Tool state machine: STARTED/PROGRESS/COMPLETED/FAILED (from Gemini)

    observability/              # Observability (gap filled)
        __init__.py
        logging.py              # Structured logging with correlation IDs
        health.py               # /health and /ready endpoints

    static/                     # Frontend assets (from Claude)
        index.html
        css/
        js/
        audio/                  # AudioWorklet processors
```

### Why This Structure

| Decision | Source | Rationale |
|----------|--------|-----------|
| Three top-level domains (`session/`, `providers/`, `tools/`) | Gemini's app/core/providers adapted | Clear responsibility boundaries without excessive nesting |
| Explicit `session/` package | GPT's "session orchestration layer" | Prevents duplicating session lifecycle logic across providers |
| Flat provider layout (Google=1 file, Bedrock=directory) | Claude | Matches actual complexity per provider |
| `events.py` with normalized event types | GPT's event taxonomy | Providers emit normalized events; session manager consumes them |
| `tools/state.py` with state machine | Gemini | Structured lifecycle for async tools, ready for vocal narration |
| `observability/` as package, not layer | GPT adapted | Observability code needs a home, but doesn't need to be an architectural layer |
| `config.py` at root, not in `config/` | Claude | Single file is sufficient; a directory is premature |

### Dependency Flow

```
app.py
  -> config.py
  -> session/manager.py
       -> providers/base.py (ABC)
       -> session/events.py
       -> session/protocol.py
  -> providers/google.py, providers/bedrock/
       -> session/events.py (emit normalized events)
       -> tools/ (Bedrock only, for now)
  -> prompts/renderer.py
  -> observability/
```

Key rule (from Claude): **no circular dependencies**. Providers depend on `session/events.py` (to emit events) but session depends on `providers/base.py` (to call providers). This is resolved by the ABC -- session holds a `BaseProvider` reference, providers implement it.

---

## 3. Provider Abstraction

### Hybrid Approach (Claude's simplicity + GPT's normalization)

```python
class BaseProvider(abc.ABC):
    """Base class for voice conversation providers."""

    @abc.abstractmethod
    async def handle_session(
        self,
        websocket: WebSocket,
        session_context: SessionContext,
    ) -> None:
        """Run a full voice session over the given WebSocket.

        Providers own their session lifecycle (connect to external service,
        stream audio, handle tool calls). They emit normalized SessionEvents
        via session_context.emit() for the session manager to relay to the client.
        """
        raise NotImplementedError("Subclasses must implement `handle_session()`")
```

```python
@dataclass(frozen=True)
class SessionContext:
    """Shared context passed to providers during a session."""
    user_id: str
    session_id: str
    system_prompt: str
    emit: Callable[[SessionEvent], Awaitable[None]]  # Emit normalized events
```

```python
class SessionEvent:
    """Normalized event emitted by providers. Protocol version included."""
    protocol_version: str = "v1"
    type: SessionEventType  # Enum: TEXT, AUDIO, TRANSCRIPTION, TURN_COMPLETE, etc.
    payload: dict[str, Any]
    timestamp: datetime
```

**Why this hybrid works:**
- Providers own their session lifecycle (Claude's insight: Google ADK needs this freedom).
- Providers emit normalized events through `session_context.emit()` (GPT's insight: the session layer shouldn't know provider internals).
- The `SessionContext` is the seam between session management and provider logic.

### WebSocket Endpoint

Single unified endpoint (from Claude):

```
/ws/{provider}/{user_id}/{session_id}
```

Query parameters are provider-specific (Claude's pragmatic acknowledgment) -- each provider extracts what it needs from the raw WebSocket request.

---

## 4. WebSocket Protocol

Adopt GPT's protocol versioning and event taxonomy, implemented with Claude's simplicity.

### Protocol Version

Every server-to-client message includes `"v": 1`. If the protocol changes incompatibly, the version increments. Clients can check the version and warn/adapt.

### Event Types (from GPT, refined)

```python
class SessionEventType(str, Enum):
    # Content delivery
    AUDIO = "audio"                           # Base64 audio chunk
    TEXT = "text"                              # Text content

    # Transcription
    INPUT_TRANSCRIPTION = "input_transcription"     # What the user said
    OUTPUT_TRANSCRIPTION = "output_transcription"   # What the agent said

    # Session control
    TURN_COMPLETE = "turn_complete"
    INTERRUPTED = "interrupted"
    SESSION_START = "session_start"
    SESSION_END = "session_end"

    # Tool lifecycle (from Gemini's state machine)
    TOOL_STARTED = "tool_started"
    TOOL_PROGRESS = "tool_progress"
    TOOL_COMPLETED = "tool_completed"
    TOOL_FAILED = "tool_failed"

    # Errors
    ERROR = "error"
```

### Reserved Fields (from GPT)

The event payload schema reserves but does not require:
- `media_type`: For future image/video support
- `tool_id`: Correlation ID for tool lifecycle events
- `metadata`: Arbitrary key-value pairs for provider-specific data

---

## 5. Tool Framework

### Stage 1: Foundation (from Claude)

```python
class BaseTool(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str: ...

    @property
    @abc.abstractmethod
    def description(self) -> str: ...

    @property
    @abc.abstractmethod
    def input_schema(self) -> dict[str, Any]: ...

    @abc.abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult: ...
```

```python
class ToolProcessor:
    """Registry for tools. Dispatches tool calls by name."""

    def register(self, tool: BaseTool) -> None: ...
    async def execute(self, tool_name: str, **kwargs: Any) -> ToolResult: ...
    def get_tool_specs(self, provider: str) -> list[dict[str, Any]]: ...
```

Note `get_tool_specs(provider)` -- from Claude's observation that tool spec format is provider-specific (Nova Sonic uses a different schema than Google ADK).

### Stage 2: Async State Machine (from Gemini)

For long-running tools (e.g., Orchestrator integration), the tool emits state transitions:

```python
class ToolState(str, Enum):
    STARTED = "started"
    PROGRESS = "progress"
    COMPLETED = "completed"
    FAILED = "failed"

class ToolResult:
    state: ToolState
    data: Any | None = None
    message: str | None = None  # Human-readable progress message
```

The provider can inject progress messages as system messages to the LLM, enabling Gemini's vocal narration pattern: the agent says "I've started looking that up for you" while the tool runs.

**Stage 2 is not implemented in stage 1** -- but the `ToolResult` and `ToolState` types are defined so the interface doesn't need to change.

---

## 6. Configuration

### Hierarchy (GPT's three-layer model + Claude's concrete implementation)

**Layer 1: Environment Variables** (production source of truth)

Injected by Kubernetes. Never baked into Docker images. Secret values redacted in startup logs (GPT's policy).

**Layer 2: Typed Settings** (Pydantic BaseSettings)

```python
class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LIVOIA_",
        env_nested_delimiter="__",
    )

    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    default_provider: str = "google"

    google: GoogleProviderConfig = GoogleProviderConfig()
    bedrock: BedrockProviderConfig = BedrockProviderConfig()

class GoogleProviderConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GOOGLE_")
    api_key: str = ""
    model_id: str = "gemini-2.0-flash-live-001"

class BedrockProviderConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BEDROCK_")
    region: str = "us-east-1"
    model_id: str = "amazon.nova-sonic-v1:0"
    # AWS credentials optional -- IRSA provides them in production (Gemini's insight)
    access_key_id: str | None = None
    secret_access_key: str | None = None
```

**Layer 3: Per-Session Runtime Config** (GPT's insight)

Prompt settings sent by the UI at session start (agent name, company, language, custom instructions). These are non-secret, per-session values that don't belong in environment variables.

### Secret Handling Policy (from GPT)

1. Never log raw API keys or credentials.
2. Redact sensitive values in startup configuration dump.
3. Zero baked credentials in Docker images.
4. AWS credentials optional in config (IRSA in production, explicit in dev).

---

## 7. CI/CD & Docker

### Pipeline (consensus across all three, refined)

```yaml
stages:
  - quality       # ruff check, ruff format --check, mypy, pylint
  - tests         # tox (unit + integration), Cobertura coverage
  - dependency    # manual: internal dependency analysis
  - build         # tag-triggered: Docker build + ECR push
```

Note: **pylint is included in quality** (all three agree it's required; Gemini accidentally omitted it from CI).

### Docker (Claude's simplifications + Gemini's IRSA awareness)

```dockerfile
FROM python:3.13-slim AS builder
# Build wheel with uv

FROM python:3.13-slim AS production
# Non-root user, single uvicorn worker (NOT 4 -- WebSocket affinity)
# No portaudio19-dev (CLI audio removed)
# Health check against /health endpoint
CMD ["uvicorn", "livoia.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

Single uvicorn worker because:
- WebSocket connections are long-lived and stateful.
- Multiple workers require sticky session routing, adding infrastructure complexity.
- Async concurrency within a single worker handles the expected load.
- Scale horizontally via Kubernetes replicas, not uvicorn workers.

### Pre-Commit Hooks

```yaml
hooks:
  - trailing-whitespace, end-of-file-fixer, check-ast, check-merge-conflict
  - ruff (lint + format)
  - commitizen (conventional commits)  # from Gemini
```

Commitizen enforces `type(scope): description` format. Jira ticket numbers in scope are **recommended but not enforced** -- the PoC doesn't have a Jira board yet, and mandatory ticket numbers before one exists would slow development.

---

## 8. Observability (Gap Filled)

None of the three variants adequately addressed observability. This synthesis treats it as a stage-1 requirement.

### Structured Logging

- JSON-formatted logs with `structlog` or `python-json-logger`.
- Every log entry includes: `timestamp`, `level`, `message`, `session_id` (if in session context), `provider`, `correlation_id`.
- Sensitive values (API keys, tokens) redacted via a log processor.
- `/health` endpoint logs suppressed to reduce noise.

### Health Endpoints

```
GET /health    # Liveness: returns 200 if process is running
GET /ready     # Readiness: returns 200 if providers can be initialized
```

Both endpoints return JSON with version info and uptime.

### Metrics Interface (Hook Pattern)

Define a `MetricsCollector` protocol that can be implemented for Prometheus, StatsD, or no-op:

```python
class MetricsCollector(Protocol):
    def session_started(self, provider: str) -> None: ...
    def session_ended(self, provider: str, duration_seconds: float) -> None: ...
    def session_error(self, provider: str, error_type: str) -> None: ...
    def tool_executed(self, tool_name: str, duration_seconds: float, success: bool) -> None: ...
```

Stage 1 ships with a logging-based implementation (metrics emitted as structured log events). A Prometheus implementation can be added later without changing any call sites.

---

## 9. Frontend

Adopt Claude's pragmatic approach:

- **Vanilla HTML/CSS/JS** with no framework and no build step.
- **AudioWorklet API** for real-time audio processing.
- **Static files inside `src/livoia/static/`** -- single deployment artifact.
- **Single WebSocket connection** to `/ws/{provider}/{user_id}/{session_id}`.

### UI Tabs (Gemini's vision, staged)

- **Stage 1**: Settings tab (prompt customization) + Conversation tab (message log).
- **Stage 2**: Prompt tab (shows rendered system prompt, from GPT's roadmap).
- **Stage 3**: Tool Use tab (shows tool invocations and results, from Gemini's transparency idea).

No frontend testing in stage 1. The JS is thin glue between Web Audio APIs and WebSocket -- test via e2e browser tests when complexity warrants it.

---

## 10. Testing Strategy

### Structure (from Claude)

```
tests/
    unit/               # Fast, mocked, 90%+ coverage target (Gemini)
        providers/
        session/
        tools/
        prompts/
    integration/        # Real provider connections, @pytest.mark.integration
    e2e/                # Full WebSocket flows, @pytest.mark.e2e
    fixtures/
        builders.py     # Fluent mock builders (from PoC via Claude)
    conftest.py         # Global fixtures, auto-mocked env
```

### WebSocket Testing (gap addressed)

None of the three variants discussed how to test real-time WebSocket flows. This is critical:

- **Unit tests**: Mock `WebSocket` object. Test that providers emit correct `SessionEvent` sequences for simulated inputs.
- **Integration tests**: Use `httpx.AsyncClient` with FastAPI's `TestClient` WebSocket support. Send audio frames, assert event sequences.
- **E2e tests**: Playwright or similar browser automation if UI testing is needed.

### Test Containers (from Gemini)

For integration tests that need external services (Redis, mock APIs), use `testcontainers-python` to spin up ephemeral containers. This avoids relying on shared test infrastructure.

### Migration Test Plan (from Claude)

Each migration phase has:
1. Source-to-destination file mapping
2. Tests to port
3. Validation command (`uv run tox` must pass)
4. Phase-specific smoke test

---

## 11. Migration Plan

### Pre-Migration: Inventory Audit (from GPT)

Classify every file in the current repo:

| Category | Meaning | Examples |
|----------|---------|---------|
| `EXPORT_AS_IS` | Copy without changes | `.pre-commit-config.yaml`, audio worklets, `docs/ai-assistance/` |
| `EXPORT_ADAPT` | Port with modifications | `livoia_web` routes, Google adapter, Bedrock client |
| `DO_NOT_EXPORT` | Intentionally excluded | Camera code, CLI scripts, LLM clients, embedding clients, cache store |

### Phased Execution (from Claude, streamlined to 7 phases)

| Phase | Content | Parallel? | Validation |
|-------|---------|-----------|------------|
| **0** | Repository scaffold: `pyproject.toml`, `tox.ini`, `.gitlab-ci.yml`, `.pre-commit-config.yaml`, empty package structure | No | `uv sync && uv run tox` passes with 0 tests |
| **1** | Configuration: `config.py`, observability, health endpoints | No | Health endpoint responds, structured logs emit |
| **2a** | Tool framework: `tools/base.py`, `tools/processor.py`, `tools/state.py` | Yes (parallel with 2b, 2c) | Unit tests pass |
| **2b** | Prompt management: `prompts/renderer.py`, templates | Yes | Unit tests pass |
| **2c** | Session framework: `session/events.py`, `session/protocol.py`, `session/manager.py` | Yes | Unit tests pass |
| **3a** | Bedrock provider: port from `livoia` + `livoia_web` adapters | Yes (parallel with 3b) | Integration test with real Bedrock |
| **3b** | Google provider: port from `livoia_google` + `livoia_web` | Yes | Integration test with real Google |
| **4** | Application factory: `app.py`, WebSocket endpoint, static file serving | No (depends on 3a, 3b) | Full e2e: browser connects, voice works |
| **5** | Frontend: port static assets, update WebSocket URL | No (depends on 4) | Manual browser test |
| **6** | Docker, CI/CD: Dockerfile, `.gitlab-ci.yml`, deployment scripts | No | `docker build` succeeds, pipeline green |
| **7** | Documentation: guides, references, README with Mermaid diagram | No | Human review |

### Validation Checklist (from GPT)

After all phases:
- [ ] `uv run tox` passes (all linters, type checks, tests)
- [ ] Docker image builds and runs
- [ ] Google voice session works end-to-end in browser
- [ ] Bedrock voice session works end-to-end in browser
- [ ] Health endpoint responds correctly
- [ ] Structured logs emit with session correlation IDs
- [ ] No PoC-only dependencies remain (`langchain`, `openai`, `numpy`, `redis`, `pyaudio`)
- [ ] All `DO_NOT_EXPORT` files confirmed absent

---

## 12. Dependency Reduction

Adopt Claude's aggressive dependency trimming:

### Dropped (PoC-only)
- `langchain-core`, `langchain-openai`, `langchain-aws` (ML library features)
- `openai` (not used by voice agent directly)
- `numpy` (no numerical processing needed)
- `redis` (no caching in stage 1; re-add if needed)
- `prometheus-client`, `slowapi` (replaced by metrics hook pattern)
- `PyAudio` (CLI audio removed)
- `httpx` (not needed if no HTTP client calls)
- `python-dotenv` (Pydantic BaseSettings handles `.env`)

### Kept
- `fastapi`, `uvicorn` (web framework)
- `pydantic`, `pydantic-settings` (configuration)
- `google-adk` (Google Gemini)
- `aws-sdk-bedrock-runtime` (or equivalent Bedrock SDK)
- `jinja2` (prompt templates)
- `structlog` or `python-json-logger` (structured logging -- new addition)

### Dev Dependencies
- `ruff`, `mypy`, `pylint` (quality)
- `pytest`, `tox`, `pytest-asyncio`, `pytest-cov` (testing)
- `pre-commit`, `commitizen` (workflow)
- `factory-boy`, `faker` (test fixtures, if needed)

---

## 13. Documentation Plan

### Taxonomy (from Claude)

```
docs/
    guides/                 # How-to guides for contributors
        code-style-guide.md
        test-development-guide.md
        commit-message-guide.md
        about-avature.md
    references/             # Technical reference
        architecture.md     # With Mermaid diagrams (from Gemini)
        configuration.md    # All env vars, types, defaults
        websocket-protocol.md  # Event types, schemas, versioning
    tutorials/              # Step-by-step walkthroughs
        local-development.md   # docker-compose quickstart (from Gemini)
        adding-a-provider.md   # How to add a new voice provider
    ai-assistance/          # AI assistant context (carried from PoC)
        design/
        ...
```

### README

- Project description and purpose
- Mermaid.js architecture diagram (from Gemini)
- 3-step quickstart: `git clone`, `uv sync`, `uv run uvicorn ...` (or `docker-compose up`)
- Link to `docs/` for details

---

## 14. Roadmap (Adapted from GPT's 5-Phase Plan)

| Phase | Name | Description |
|-------|------|-------------|
| **1** | Production Parity | Voice conversations work with Google and Bedrock in a production-grade deployment. Health checks, structured logging, CI/CD pipeline, Docker. |
| **2** | Prompt Transparency | Prompt tab in UI shows rendered system prompt. Prompt template management improved. |
| **3** | Tool Transparency | Tool Use tab shows invocations and results. Tool state machine (STARTED/PROGRESS/COMPLETED) wired to UI. |
| **4** | Configurable Tools | Settings tab allows enabling/disabling tools. Tool catalog with descriptions. Web search, file search as built-in tools. |
| **5** | External Orchestrator | Avature Orchestrator integration as an async tool. Vocal narration of tool progress (Gemini's innovation). |

Each phase is independently deployable and valuable.

---

## 15. Open Questions for the Team

1. **Package name**: `livoia` (Claude) vs. `livoia_prod` (GPT)? Recommend `livoia` -- "prod" in the name is confusing.
2. **Commitizen ticket enforcement**: Require Jira tickets in commits now, or wait until a board exists?
3. **Redis in stage 1?**: Claude drops it; GPT keeps it as optional. If no caching is needed for voice sessions, drop it.
4. **Authentication**: None of the three address it. Is this handled at the infrastructure level (API gateway), or does the app need it?
5. **Uvicorn workers**: This synthesis recommends 1 worker. Does the ops team expect multiple workers behind a load balancer, or Kubernetes-level horizontal scaling?
