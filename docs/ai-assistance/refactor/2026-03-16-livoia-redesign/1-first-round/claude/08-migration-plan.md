# Migration Plan

## Overview

This document describes the step-by-step process to create the new production repository from the PoC. The migration is organized into phases that can be executed sequentially.

## Phase 0: Repository Bootstrap

**Goal**: Create the new repository with project scaffolding.

### Steps

1. Create new GitLab repository `livoia`
2. Initialize with:
   - `pyproject.toml` (as designed in [06-ci-cd.md](06-ci-cd.md))
   - `tox.ini`
   - `.pre-commit-config.yaml`
   - `.github/workflows/ci.yml`
   - `.gitignore`
   - `.env.example`
   - `check_code.sh`
   - `README.md` (minimal, with project name and description)
3. Create directory structure:
   ```
   src/livoia/
   tests/unit/
   tests/integration/
   tests/e2e/
   docs/guides/
   docs/references/
   docs/tutorials/
   docs/ai-assistance/ (with HELP.md files)
   docker/
   .claude/
   ```
4. Verify: `uv sync --group dev && uv run tox` passes (with empty test suite)

### Validation
- `uv run ruff check .` passes
- `uv run mypy src/livoia tests` passes
- `uv run pytest` passes (0 tests collected)
- `uv run tox` passes all environments

## Phase 1: Tool Framework

**Goal**: Migrate the tool framework (independent, no provider dependencies).

### Source -> Destination Mapping

| PoC File | New File |
|----------|----------|
| `src/livoia/tools/base.py` | `src/livoia/tools/base.py` |
| `src/livoia/tools/processor.py` | `src/livoia/tools/processor.py` |
| `src/livoia/tools/implementations/date_time.py` | `src/livoia/tools/builtin/date_time.py` |
| `src/livoia/tools/__init__.py` | `src/livoia/tools/__init__.py` |

### Changes Required
- Update import paths (e.g., `from livoia.tools.implementations` -> `from livoia.tools.builtin`)
- Update `__init__.py` re-exports

### Tests to Migrate

| PoC Test | New Test |
|----------|----------|
| `tests/unit/tools/test_tools.py` | `tests/unit/tools/test_processor.py` |
| `tests/unit/tools/implementations/test_date_time.py` | `tests/unit/tools/builtin/test_date_time.py` |

### Validation
- All tool unit tests pass
- `uv run tox` passes

## Phase 2: Bedrock Provider

**Goal**: Migrate Bedrock speech client, adapter, and speech events.

### Source -> Destination Mapping

| PoC File | New File |
|----------|----------|
| `src/livoia/clients/speech/base.py` (SpeechEvents only) | `src/livoia/providers/bedrock/__init__.py` (SpeechEvents) |
| `src/livoia/clients/speech/bedrock_sonic.py` | `src/livoia/providers/bedrock/client.py` |
| `src/livoia_web/adapters/bedrock_adapter.py` | `src/livoia/providers/bedrock/provider.py` |
| (new) | `src/livoia/providers/bedrock/config.py` |
| (new) | `src/livoia/providers/base.py` |

### Changes Required

1. **Create `providers/base.py`**: Define `BaseProvider` ABC
2. **Extract SpeechEvents**: Move from `clients/speech/base.py` into `providers/bedrock/`
3. **Merge SpeechCaller into BedrockProvider**: The SpeechCaller module wrapped the client with tool handling. In the new design, tool handling moves into the BedrockProvider, eliminating the intermediate module layer.
4. **Rename classes**:
   - `BedrockSonicClient` -> `NovaSonicClient`
   - `BedrockSonicClientConfig` -> `NovaSonicClientConfig`
   - `BedrockWebSocketAdapter` -> `BedrockProvider`
   - `BedrockAdapterConfig` -> `BedrockProviderConfig`
5. **Remove BaseSpeechClient ABC**: Only one speech client exists, and the provider ABC serves as the abstraction point instead
6. **Implement `BaseProvider.handle_session()`**: Combine the adapter's `connect/send_audio/receive_events/close` into a single session handler

### Architecture Change

Current PoC flow:
```
app.py -> BedrockWebSocketAdapter -> SpeechCaller -> BedrockSonicClient
```

New flow:
```
app.py -> BedrockProvider -> NovaSonicClient
                          -> ToolProcessor
```

The BedrockProvider absorbs the SpeechCaller's responsibility of coordinating tool execution.

### Tests to Migrate

| PoC Test | New Test |
|----------|----------|
| `tests/unit/clients/speech/test_bedrock_sonic.py` | `tests/unit/providers/bedrock/test_client.py` |
| `tests/unit/modules/test_speech_caller.py` | `tests/unit/providers/bedrock/test_provider.py` |

### Validation
- All Bedrock unit tests pass
- `uv run tox` passes

## Phase 3: Google Provider

**Goal**: Migrate Google ADK integration.

### Source -> Destination Mapping

| PoC File | New File |
|----------|----------|
| `src/livoia_google/agent.py` | `src/livoia/providers/google.py` (partial) |
| `src/livoia_google/config.py` | `src/livoia/providers/google.py` (partial) |
| Google handler from `src/livoia_web/app.py` | `src/livoia/providers/google.py` |

### Changes Required

1. **Consolidate into single file**: `providers/google.py` contains config, agent factory, and `GoogleProvider` class
2. **Implement `BaseProvider.handle_session()`**: Move the inline Google WebSocket logic from `app.py` into `GoogleProvider`
3. **Handle query parameters**: `proactivity` and `affective_dialog` need to be passed through the provider interface (either via `handle_session` kwargs or a separate method)

### Provider Interface Extension for Query Parameters

The Google provider needs WebSocket query parameters. Options:

**Option A: Pass raw WebSocket** (let provider extract params)
```python
async def handle_session(self, websocket: WebSocket, ...) -> None:
    # Provider extracts query params from websocket.query_params
```

**Option B: Pass params explicitly**
```python
async def handle_session(self, websocket: WebSocket, ..., params: dict[str, Any]) -> None:
```

**Recommendation**: Option A. The provider receives the full WebSocket and handles provider-specific parameter extraction. This keeps the base interface simple and avoids encoding every provider's unique parameters.

### Tests to Create

| New Test | Description |
|----------|-------------|
| `tests/unit/providers/test_google.py` | Config properties, agent creation |

### Validation
- Google provider unit tests pass
- `uv run tox` passes

## Phase 4: Prompt Management

**Goal**: Migrate prompt rendering.

### Source -> Destination Mapping

| PoC File | New File |
|----------|----------|
| `src/livoia_web/prompts.py` | `src/livoia/prompts/interview.py` |

### Changes Required
- Move into `prompts/` subpackage
- Update imports throughout the codebase
- No functional changes needed

### Tests to Migrate/Create

| New Test | Description |
|----------|-------------|
| `tests/unit/prompts/test_interview.py` | Rendering with all parameter combinations |

### Validation
- Prompt tests pass
- `uv run tox` passes

## Phase 5: Application Factory

**Goal**: Create the unified FastAPI application.

### Source -> Destination Mapping

| PoC File | New File |
|----------|----------|
| `src/livoia_web/app.py` | `src/livoia/app.py` |
| (new) | `src/livoia/config.py` |

### Changes Required

1. **Create `config.py`**: AppConfig with all provider configs
2. **Simplify `app.py`**: Unified WebSocket endpoint, provider registry, static file mounting
3. **Update entry point**: `livoia.app:create_app` (not `livoia_web.app:create_app`)
4. **Remove inline provider logic**: All provider code lives in `providers/`

### Tests to Create

| New Test | Description |
|----------|-------------|
| `tests/unit/test_app.py` | App creation, endpoint existence, prompt_config parsing |
| `tests/unit/test_config.py` | Configuration defaults, env var loading |

### Validation
- App tests pass
- `uv run tox` passes

## Phase 6: Frontend

**Goal**: Migrate static frontend files.

### Source -> Destination Mapping

| PoC File | New File |
|----------|----------|
| `src/livoia_web/static/index.html` | `src/livoia/static/index.html` |
| `src/livoia_web/static/css/style.css` | `src/livoia/static/css/style.css` |
| `src/livoia_web/static/js/*.js` | `src/livoia/static/js/*.js` |

### Changes Required

1. **Update WebSocket URL**: Change from `/ws/google/...` and `/ws/bedrock/...` to unified `/ws/{provider}/...`
2. In `app.js`, update `getWebSocketUrl()`:
   ```javascript
   const baseUrl = "ws://" + window.location.host + "/ws/" + provider + "/" + userId + "/" + sessionId;
   ```
   This is actually already what the PoC does, so minimal change needed.

### Validation
- Server starts and serves static files
- WebSocket connects with both providers
- Manual testing: full conversation works

## Phase 7: Docker and Deployment

**Goal**: Set up Docker build and deployment configuration.

### Source -> Destination Mapping

| PoC File | New File |
|----------|----------|
| `Dockerfile` | `Dockerfile` (adapted) |
| `docker/entrypoint.sh` | `docker/entrypoint.sh` |
| `docker/healthcheck.sh` | `docker/healthcheck.sh` |
| `.dockerignore` | `.dockerignore` |

### Changes Required
- Update Dockerfile CMD: `livoia.app:create_app`
- Remove `resources/` copy (prompts are in Python code)
- Update `.dockerignore` for new structure

### Validation
- `docker build` succeeds
- Container starts and serves the app
- Health check passes
- Manual testing: conversation works in Docker

## Phase 8: Documentation

**Goal**: Migrate and create documentation.

### Steps

1. Copy as-is: `about-avature.md`, `technical-writing-style-guide.md`, AI assistance HELP files
2. Adapt: `code-style-guide.md`, `commit-message-guide.md`, `test-development-guide.md`
3. Create new: `getting-started.md`, `environment-variables.md`, `websocket-protocol.md`, `running-locally.md`, `deploying-with-docker.md`
4. Write `README.md`
5. Write `.claude/CLAUDE.md` and `.claude/CODEMAP.md`
6. Copy design docs: this `2026-03-16-prod-redesign/` directory

### Validation
- All markdown files render correctly
- Links between documents work
- Getting started guide works for a new developer

## Phase 9: Final Verification

**Goal**: Ensure everything works end-to-end.

### Checklist

- [ ] `uv sync --group dev` installs cleanly
- [ ] `uv run pre-commit install` succeeds
- [ ] `./check_code.sh` passes all 4 checks
- [ ] `uv run tox` passes all environments (lint, typecheck, tests)
- [ ] `uv run uvicorn livoia.app:create_app --factory --reload --port 8000` starts
- [ ] Google Gemini conversation works in browser
- [ ] AWS Bedrock conversation works in browser
- [ ] Settings tab customizes the prompt
- [ ] Event console shows events
- [ ] `docker build` succeeds
- [ ] Docker container runs and serves the app
- [ ] No unused code (every module reachable from `app.py`)
- [ ] No unused dependencies in `pyproject.toml`
- [ ] All documentation links work
- [ ] GitHub Actions pipeline passes

## Migration Timeline Summary

| Phase | Description | Dependencies |
|-------|-------------|--------------|
| 0 | Repository bootstrap | None |
| 1 | Tool framework | Phase 0 |
| 2 | Bedrock provider | Phase 0, 1 |
| 3 | Google provider | Phase 0 |
| 4 | Prompt management | Phase 0 |
| 5 | Application factory | Phase 2, 3, 4 |
| 6 | Frontend | Phase 5 |
| 7 | Docker and deployment | Phase 5, 6 |
| 8 | Documentation | Phase 5 |
| 9 | Final verification | All |

Phases 1-4 can be worked in parallel (they are independent). Phase 5 depends on 2, 3, and 4. Phases 6-8 depend on 5. Phase 9 depends on all.
