# File-Level Migration Inventory (Stage 1)

Decision legend:

- `KEEP_AS_IS`: carry with minimal/no changes
- `ADAPT`: migrate with structural or behavioral updates
- `DROP_STAGE_1`: intentionally excluded from stage 1

## 1) Root project files

| Source | Decision | Target | Notes |
|---|---|---|---|
| `pyproject.toml` | `ADAPT` | `pyproject.toml` | Keep quality stack; prune PoC-only deps and align package paths. |
| `tox.ini` | `ADAPT` | `tox.ini` | Update package/test paths for new module layout. |
| `.github/workflows/ci.yml` | `ADAPT` | `.github/workflows/ci.yml` | Preserve stage structure; update image/app naming as needed. |
| `.pre-commit-config.yaml` | `KEEP_AS_IS` | `.pre-commit-config.yaml` | Hook baseline remains valid. |
| `check_code.sh` | `ADAPT` | `check_code.sh` | Keep workflow; update import paths and package targets. |
| `Dockerfile` | `ADAPT` | `Dockerfile` | Keep multi-stage/non-root pattern; update entrypoint module path. |
| `.dockerignore` | `KEEP_AS_IS` | `.dockerignore` | Baseline rules still useful. |
| `.gitignore` | `ADAPT` | `.gitignore` | Align generated artifacts and package names. |
| `.env.example` | `ADAPT` | `.env.example` | Keep only relevant env vars for stage 1. |
| `uv.lock` | `ADAPT` | `uv.lock` | Regenerate after dependency curation. |
| `docker/entrypoint.sh` | `KEEP_AS_IS` | `docker/entrypoint.sh` | Shell wrapper remains sufficient. |
| `docker/healthcheck.sh` | `ADAPT` | `docker/healthcheck.sh` | Keep `/health` check with app port env. |

## 2) Documentation

| Source | Decision | Target | Notes |
|---|---|---|---|
| `docs/ai-assistance/**` | `KEEP_AS_IS` | `docs/ai-assistance/**` | Preserve recursively. |
| `docs/guides/about-avature.md` | `KEEP_AS_IS` | same | Domain context unchanged. |
| `docs/guides/technical-writing-style-guide.md` | `KEEP_AS_IS` | same | Reusable across repos. |
| `docs/guides/code-style-guide.md` | `ADAPT` | same | Update architecture/path examples. |
| `docs/guides/test-development-guide.md` | `ADAPT` | same | Update websocket/provider testing guidance. |
| `docs/guides/commit-message-guide.md` | `ADAPT` | same | Scope names aligned to new modules. |
| `docs/tutorials/voice-interview-agent-web-demo.md` | `ADAPT` | `docs/tutorials/run-web-demo.md` | Keep behavior docs with new commands/paths. |
| `docs/tutorials/voice-interview-agent-cli-demo.md` | `DROP_STAGE_1` | - | CLI path out of scope. |

## 3) Runtime code: web + providers

| Source | Decision | Target | Notes |
|---|---|---|---|
| `src/livoia_web/app.py` | `ADAPT` | `src/livoia/app/{create_app.py,routes_http.py,routes_ws.py}` | Split transport concerns and delegate runtime orchestration. |
| `src/livoia_web/prompts.py` | `ADAPT` | `src/livoia/services/prompt_rendering_service.py` + `src/livoia/domain/prompt_config.py` | Typed prompt config + renderer service. |
| `src/livoia_web/adapters/bedrock_adapter.py` | `ADAPT` | `src/livoia/providers/bedrock/adapter.py` | Keep bridge logic; align to provider adapter interface. |
| `src/livoia_web/static/index.html` | `ADAPT` | `src/livoia/web/static/index.html` | Remove camera controls in stage 1. |
| `src/livoia_web/static/css/style.css` | `ADAPT` | `src/livoia/web/static/css/style.css` | Remove camera-related styles and dead selectors. |
| `src/livoia_web/static/js/app.js` | `ADAPT` | `src/livoia/web/static/js/app.js` | Keep session/event flow; remove image capture/send path. |
| `src/livoia_web/static/js/audio-player.js` | `KEEP_AS_IS` | `src/livoia/web/static/js/audio-player.js` | Core playback pipeline retained. |
| `src/livoia_web/static/js/audio-recorder.js` | `KEEP_AS_IS` | `src/livoia/web/static/js/audio-recorder.js` | Core capture pipeline retained. |
| `src/livoia_web/static/js/pcm-player-processor.js` | `KEEP_AS_IS` | `src/livoia/web/static/js/pcm-player-processor.js` | Worklet retained. |
| `src/livoia_web/static/js/pcm-recorder-processor.js` | `KEEP_AS_IS` | `src/livoia/web/static/js/pcm-recorder-processor.js` | Worklet retained. |
| `src/livoia_google/agent.py` | `ADAPT` | `src/livoia/providers/google/adapter.py` | Move ADK lifecycle under provider boundary. |
| `src/livoia_google/config.py` | `ADAPT` | `src/livoia/config/settings.py` + google adapter | Keep behavior, centralize typed env settings. |
| `src/livoia/clients/speech/bedrock_sonic.py` | `ADAPT` | `src/livoia/providers/bedrock/client.py` | Preserve streaming implementation with boundary cleanup. |
| `src/livoia/modules/speech_caller.py` | `ADAPT` | `src/livoia/services/realtime_session_service.py` + bedrock adapter internals | Keep coordination behavior, simplify layering. |

## 4) Runtime code: intentionally excluded in stage 1

| Source area | Decision | Reason |
|---|---|---|
| `src/livoia/audio/**` | `DROP_STAGE_1` | Browser handles audio I/O. |
| `src/livoia/agent/**` | `DROP_STAGE_1` | Legacy orchestration superseded by websocket session service. |
| `src/livoia/api/**` | `DROP_STAGE_1` | PoC API surface not required for stage 1 product path. |
| `src/livoia/clients/llm/**` | `DROP_STAGE_1` | Not needed for web parity scope. |
| `src/livoia/clients/embedding/**` | `DROP_STAGE_1` | Not needed for web parity scope. |
| `src/livoia/modules/llm_caller.py` | `DROP_STAGE_1` | Not needed in stage 1. |
| `src/livoia/modules/encoder_caller.py` | `DROP_STAGE_1` | Not needed in stage 1. |
| `src/livoia/modules/cache_store.py` | `DROP_STAGE_1` | No stage 1 requirement for shared cache layer. |
| `src/livoia_web` camera/image flow in `app.py` and `static/js/app.js` | `DROP_STAGE_1` | Explicitly excluded by scope. |

## 5) Resources and scripts

| Source | Decision | Target | Notes |
|---|---|---|---|
| `resources/prompts/interview_agent.txt` | `ADAPT` | `resources/prompts/interview_agent.txt` | Keep as optional canonical prompt seed. |
| `resources/prompts/interview_agent_b.txt` | `DROP_STAGE_1` | - | Alternate prompt variant not required. |
| `resources/prompts/test/**` | `DROP_STAGE_1` | - | Non-essential for baseline migration. |
| `resources/examples/**` | `DROP_STAGE_1` | - | Optional references, not baseline. |
| `scripts/**` | `DROP_STAGE_1` | - | CLI/manual PoC scripts out of scope. |

## 6) Tests

| Source | Decision | Target | Notes |
|---|---|---|---|
| `tests/unit/**` | `ADAPT` | `tests/unit/**` | Rewrite around new module boundaries. |
| `tests/integration/**` | `ADAPT` | `tests/integration/**` | Preserve provider/websocket integration focus. |
| `tests/e2e/**` | `ADAPT` | `tests/e2e/**` | Keep health and critical conversation checks. |
| `tests/fixtures/**` | `ADAPT` | `tests/fixtures/**` | Reuse builders where possible. |
| `tests/conftest.py` | `ADAPT` | `tests/conftest.py` | Update app import and session bootstrap fixtures. |

## 7) Validation checks for migrated baseline

- Conversation + Settings behavior parity works on both providers.
- No camera/image path remains in backend routes or frontend controls.
- Prompt settings are applied at session start through `prompt_config`.
- CI quality + tests pass with updated paths.
- Docker image starts with env-injected credentials and healthy status.
