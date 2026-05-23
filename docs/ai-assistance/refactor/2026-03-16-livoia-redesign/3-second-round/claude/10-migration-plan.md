# 10. Migration Plan

## Pre-Migration: Inventory Audit

Before writing any code, classify every file in the current PoC into one of three categories:

| Category | Meaning |
|----------|---------|
| `EXPORT_AS_IS` | Copy to new repo without changes |
| `EXPORT_ADAPT` | Port to new repo with modifications |
| `DO_NOT_EXPORT` | Intentionally excluded from new repo |

### EXPORT_AS_IS

| File/Directory | Destination |
|---------------|-------------|
| `.pre-commit-config.yaml` | Root (add commitizen hook) |
| `.dockerignore` | Root |
| `docs/ai-assistance/` | `docs/ai-assistance/` |
| `docs/guides/about-avature.md` | `docs/guides/about-avature.md` |
| `src/livoia_web/static/audio/audio-processor.js` | `src/livoia/static/audio/audio-processor.js` |

### EXPORT_ADAPT

| Source | Destination | Changes |
|--------|-------------|---------|
| `pyproject.toml` | `pyproject.toml` | New package name, reduced dependencies, updated config |
| `tox.ini` | `tox.ini` | Updated paths (`src/livoia`) |
| `.gitlab-ci.yml` | `.gitlab-ci.yml` | Updated image name, removed portaudio |
| `Dockerfile` | `Dockerfile` | Simplified, single worker, no portaudio |
| `src/livoia_web/app.py` | `src/livoia/app.py` + `src/livoia/session/manager.py` | Split: factory in app.py, session logic in manager.py |
| `src/livoia_web/prompts.py` | `src/livoia/agents/interviewer.py` + `agents/templates/interviewer.j2` | Refactor: extract template, create AgentDefinition |
| `src/livoia_web/adapters/bedrock_adapter.py` | `src/livoia/providers/bedrock/provider.py` | Merge with SpeechCaller logic, emit SessionEvents |
| `src/livoia_google/agent.py` | `src/livoia/providers/google.py` | Consolidate agent creation + ADK runner logic |
| `src/livoia_google/config.py` | `src/livoia/config.py` (GoogleProviderConfig) | Merge into unified config |
| `src/livoia/clients/speech/bedrock_sonic.py` | `src/livoia/providers/bedrock/client.py` | Rename, simplify interface |
| `src/livoia/tools/base.py` | `src/livoia/tools/base.py` | Add ToolState, ToolResult; update execute() signature |
| `src/livoia/tools/processor.py` | `src/livoia/tools/processor.py` | Add provider-specific formatting, progress callback |
| `src/livoia/tools/implementations/date_time.py` | `src/livoia/tools/implementations/date_time.py` | Return ToolResult instead of dict |
| `src/livoia/utils/logging.py` | `src/livoia/observability/logging.py` | Replace with structlog-based implementation |
| `src/livoia_web/static/` | `src/livoia/static/` | Update WebSocket URL to unified endpoint |
| `docs/guides/code-style-guide.md` | `docs/guides/code-style-guide.md` | Update for new package structure |
| `docs/guides/test-development-guide.md` | `docs/guides/test-development-guide.md` | Update for new test patterns |
| `docs/guides/commit-message-guide.md` | `docs/guides/commit-message-guide.md` | Add commitizen section |

### DO_NOT_EXPORT

| File/Directory | Reason |
|---------------|--------|
| `src/livoia/clients/llm/` | General ML library, not voice agent |
| `src/livoia/clients/embedding/` | General ML library, not voice agent |
| `src/livoia/modules/llm_caller.py` | General ML library, not voice agent |
| `src/livoia/modules/encoder_caller.py` | General ML library, not voice agent |
| `src/livoia/modules/base.py` (cache logic) | No caching needed |
| `src/livoia/modules/speech_caller.py` | Absorbed into BedrockProvider |
| `src/livoia/cache/` | No Redis/file caching |
| `src/livoia/audio/` | CLI audio, not browser |
| `src/livoia/api/` | PoC HTTP API, replaced by new app.py |
| `src/livoia/agent/` | PoC agent orchestration, replaced by agents/ |
| `scripts/` | CLI demo scripts |
| `.env` | Secrets, never committed |

---

## Phased Execution

### Phase 0: Repository Scaffold

**Goal**: Empty project that passes all quality checks.

**Actions**:
1. Create new repository
2. Set up `pyproject.toml` with dependencies, tool configs (ruff, mypy, pylint)
3. Set up `tox.ini` with `py313`, `lint`, `typecheck` environments
4. Set up `.pre-commit-config.yaml` with all hooks
5. Set up `.gitlab-ci.yml` with all stages
6. Create `src/livoia/__init__.py` (empty package)
7. Create `tests/` directory with `conftest.py`

**Validation**: `uv sync && uv run tox` passes with 0 tests collected.

---

### Phase 1: Configuration and Observability

**Goal**: App can start, load config, log, and respond to health checks.

**Actions**:
1. Create `src/livoia/config.py` with `AppConfig`, `GoogleProviderConfig`, `BedrockProviderConfig`
2. Create `src/livoia/observability/logging.py` with structlog setup
3. Create `src/livoia/observability/health.py` with `/health` and `/ready` handlers
4. Create `src/livoia/observability/metrics.py` with `MetricsCollector` protocol and `LoggingMetricsCollector`
5. Create `src/livoia/app.py` with FastAPI factory (health routes only)
6. Write unit tests for config loading, health endpoints, logging

**Validation**: `uv run uvicorn livoia.app:create_app --factory` starts, `curl localhost:8000/health` returns 200.

---

### Phase 2a: Tool Framework (parallel with 2b, 2c)

**Goal**: Tool registration, dispatch, and built-in tools work.

**Source**: Port from `src/livoia/tools/`

**Actions**:
1. Create `src/livoia/tools/base.py` with `BaseTool`, `ToolState`, `ToolResult`
2. Create `src/livoia/tools/processor.py` with `ToolProcessor`
3. Create `src/livoia/tools/state.py` (if separated from base)
4. Port `GetDateAndTimeTool` to `src/livoia/tools/implementations/date_time.py`
5. Write unit tests for registration, dispatch, tool execution

**Validation**: Unit tests pass. `ToolProcessor` can register and execute `GetDateAndTimeTool`.

---

### Phase 2b: Agent Framework (parallel with 2a, 2c)

**Goal**: Agent definitions, registry, and prompt rendering work.

**Source**: Refactor from `src/livoia_web/prompts.py`

**Actions**:
1. Create `src/livoia/agents/base.py` with `AgentDefinition`
2. Create `src/livoia/agents/registry.py` with `AgentRegistry`
3. Create `src/livoia/agents/templates/interviewer.j2`
4. Create `src/livoia/agents/interviewer.py` with interviewer definition
5. Write unit tests for prompt rendering with default and custom variables

**Validation**: Unit tests pass. Rendering interviewer prompt with custom variables produces expected output.

---

### Phase 2c: Session Framework (parallel with 2a, 2b)

**Goal**: Session events, protocol serialization, and session manager skeleton work.

**Actions**:
1. Create `src/livoia/session/events.py` with `SessionEvent`, `SessionEventType`
2. Create `src/livoia/session/protocol.py` with serialization (event -> JSON with version)
3. Create `src/livoia/session/manager.py` skeleton (WebSocket accept, prompt_config receive, provider dispatch)
4. Create `src/livoia/providers/base.py` with `BaseProvider` ABC and `SessionContext`
5. Write unit tests for event serialization, protocol versioning

**Validation**: Unit tests pass. Events serialize to correct JSON with `"v": 1`.

---

### Phase 3a: Bedrock Provider (parallel with 3b)

**Goal**: Bedrock voice sessions work end-to-end.

**Source**: Port from `src/livoia/clients/speech/bedrock_sonic.py` + `src/livoia_web/adapters/bedrock_adapter.py` + `src/livoia/modules/speech_caller.py`

**Actions**:
1. Create `src/livoia/providers/bedrock/client.py` (port NovaSonicClient)
2. Create `src/livoia/providers/bedrock/config.py` (Bedrock-specific config)
3. Create `src/livoia/providers/bedrock/provider.py` (implement `BaseProvider`, merge adapter + SpeechCaller logic)
4. Wire tool execution: provider uses `ToolProcessor` for tool calls
5. Port and adapt unit tests (mock Bedrock streaming)
6. Write integration test (manual, requires real AWS credentials)

**Validation**: Unit tests pass. Integration test with real Bedrock confirms voice conversation works.

---

### Phase 3b: Google Provider (parallel with 3a)

**Goal**: Google Gemini voice sessions work end-to-end.

**Source**: Port from `src/livoia_google/agent.py` + `src/livoia_google/config.py` + relevant parts of `src/livoia_web/app.py`

**Actions**:
1. Create `src/livoia/providers/google.py` (consolidate agent creation, Runner setup, event handling)
2. Emit `SessionEvent` objects instead of raw WebSocket messages
3. Handle native audio vs half-cascade model detection
4. Handle proactivity/affective_dialog query parameters
5. Port and adapt unit tests
6. Write integration test (manual, requires real Google API key)

**Validation**: Unit tests pass. Integration test with real Google confirms voice conversation works.

---

### Phase 4: Application Assembly

**Goal**: All components wired together. Full voice sessions work via WebSocket.

**Depends on**: Phases 2a, 2b, 2c, 3a, 3b

**Actions**:
1. Complete `src/livoia/session/manager.py`: wire agent registry, provider instantiation, event relay
2. Complete `src/livoia/app.py`: register WebSocket route, mount static files, lifespan handler
3. Register tools, agents, and providers in lifespan
4. Write integration tests: WebSocket connection, prompt_config, session lifecycle
5. Write e2e test: full browser-to-provider flow (manual)

**Validation**: Start server, connect via WebSocket, conduct voice conversation with both providers.

---

### Phase 5: Frontend

**Goal**: Browser UI works with the new backend.

**Source**: Port from `src/livoia_web/static/`

**Actions**:
1. Copy static files to `src/livoia/static/`
2. Update WebSocket URL from `/ws/google/{user_id}/{session_id}` to `/ws/{provider}/{user_id}/{session_id}`
3. Update event handling to match new protocol (versioned events with `type` field)
4. Test audio streaming, transcription display, barge-in

**Validation**: Manual browser test with both Google and Bedrock providers.

---

### Phase 6: Docker and Deployment

**Goal**: Docker image builds and runs in production-like environment.

**Actions**:
1. Create `Dockerfile` (multi-stage, non-root, single worker)
2. Create `docker-compose.yml` for local development
3. Create `.dockerignore`
4. Update `.gitlab-ci.yml` build stage with new image name
5. Test: build image, run container, connect browser, voice conversation works

**Validation**: `docker build -t livoia .` succeeds. Container starts and serves voice sessions.

---

### Phase 7: Documentation

**Goal**: All documentation updated for the new repository.

**Actions**:
1. Write `README.md` with Mermaid architecture diagram and quickstart
2. Port and update `docs/guides/` (code style, testing, commits, Avature context)
3. Create `docs/references/architecture.md` (detailed architecture reference)
4. Create `docs/references/configuration.md` (all env vars, types, defaults)
5. Create `docs/references/websocket-protocol.md` (event types, schemas)
6. Create `docs/tutorials/local-development.md` (docker-compose quickstart)
7. Create `.claude/CLAUDE.md` and `.claude/CODEMAP.md` for AI-assisted development
8. Copy `docs/ai-assistance/` from PoC

**Validation**: Human review of all documentation.

---

## Final Validation Checklist

After all phases are complete:

- [ ] `uv run tox` passes (all linters, type checks, unit tests)
- [ ] Docker image builds successfully
- [ ] Google voice session works end-to-end in browser
- [ ] Bedrock voice session works end-to-end in browser
- [ ] Tool execution works during Bedrock sessions (date/time tool)
- [ ] Prompt customization works (agent name, company, questions, guidelines)
- [ ] `/health` endpoint responds correctly
- [ ] `/ready` endpoint reports provider availability
- [ ] Structured JSON logs emit with session correlation IDs
- [ ] Config summary logs at startup with secrets redacted
- [ ] GitLab CI pipeline runs quality, tests, and build stages
- [ ] No PoC-only dependencies remain (langchain, openai, numpy, redis, pyaudio)
- [ ] All `DO_NOT_EXPORT` files confirmed absent
- [ ] Pre-commit hooks pass (ruff, commitizen, file hygiene)

---

## Parallelism Summary

```
Phase 0  ─────────────────────────────────>
Phase 1  ─────────────────────────────────>
Phase 2a ──────────>  (tools)    \
Phase 2b ──────────>  (agents)    } parallel
Phase 2c ──────────>  (session)  /
Phase 3a ──────────>  (bedrock)  \  parallel
Phase 3b ──────────>  (google)   /
Phase 4  ─────────────────────────────────>  (depends on 2a-3b)
Phase 5  ─────────────────────────────────>  (depends on 4)
Phase 6  ─────────────────────────────────>  (depends on 4)
Phase 7  ─────────────────────────────────>  (can start earlier for docs that don't depend on code)
```

Critical path: Phase 0 -> Phase 1 -> Phase 2c -> Phase 3a/3b -> Phase 4 -> Phase 5
