# Migration Inventory (Stage 1)

Decision legend:

- `EXPORT_AS_IS`: move with minimal/no changes
- `EXPORT_ADAPT`: move with structural or behavioral adaptation
- `DO_NOT_EXPORT`: intentionally excluded from stage 1

## 1) Root tooling and project files

| Source | Decision | Target | Rationale |
|---|---|---|---|
| `pyproject.toml` | `EXPORT_ADAPT` | `pyproject.toml` | Keep quality stack; remove PoC-only dependencies and align package paths. |
| `tox.ini` | `EXPORT_ADAPT` | `tox.ini` | Keep environment structure; align package/test targets. |
| `.github/workflows/ci.yml` | `EXPORT_ADAPT` | `.github/workflows/ci.yml` | Preserve CI stage model with project path/image updates. |
| `.pre-commit-config.yaml` | `EXPORT_AS_IS` | `.pre-commit-config.yaml` | Baseline hook set remains valid. |
| `check_code.sh` | `EXPORT_ADAPT` | `check_code.sh` | Keep workflow and update package paths. |
| `Dockerfile` | `EXPORT_ADAPT` | `Dockerfile` | Keep multi-stage/non-root approach, update runtime entrypoint. |
| `docker/entrypoint.sh` | `EXPORT_AS_IS` | `docker/entrypoint.sh` | Simple wrapper remains appropriate. |
| `docker/healthcheck.sh` | `EXPORT_ADAPT` | `docker/healthcheck.sh` | Keep `/health` check and align port env if needed. |
| `.dockerignore` | `EXPORT_AS_IS` | `.dockerignore` | Existing patterns remain useful. |
| `.gitignore` | `EXPORT_ADAPT` | `.gitignore` | Align generated paths/artifacts. |
| `.env.example` | `EXPORT_ADAPT` | `.env.example` | Reflect stage 1 env contracts and profile controls. |
| `uv.lock` | `EXPORT_ADAPT` | `uv.lock` | Regenerate after dependency curation. |
| `.env` | `DO_NOT_EXPORT` | - | Local secret file must not migrate. |

## 2) Documentation

### 2.1 Preserve recursively

| Source | Decision | Target | Rationale |
|---|---|---|---|
| `docs/ai-assistance/**` | `EXPORT_AS_IS` | `docs/ai-assistance/**` | Explicit preservation requirement. |

### 2.2 Guides and tutorials

| Source | Decision | Target | Rationale |
|---|---|---|---|
| `docs/guides/about-avature.md` | `EXPORT_AS_IS` | same | Domain context remains relevant. |
| `docs/guides/technical-writing-style-guide.md` | `EXPORT_AS_IS` | same | Writing standards remain valid. |
| `docs/guides/code-style-guide.md` | `EXPORT_ADAPT` | same | Update examples to new architecture and boundaries. |
| `docs/guides/test-development-guide.md` | `EXPORT_ADAPT` | same | Align to websocket/provider/profile testing patterns. |
| `docs/guides/commit-message-guide.md` | `EXPORT_ADAPT` | same | Align scopes with target package modules. |
| `docs/tutorials/voice-interview-agent-web-demo.md` | `EXPORT_ADAPT` | `docs/tutorials/run-web-demo.md` | Preserve behavior with updated commands/paths. |
| `docs/tutorials/voice-interview-agent-cli-demo.md` | `DO_NOT_EXPORT` | - | CLI path is out of stage 1 scope. |

## 3) Runtime code - web and providers

### 3.1 `src/livoia_web`

| Source | Decision | Target | Rationale |
|---|---|---|---|
| `src/livoia_web/app.py` | `EXPORT_ADAPT` | `src/livoia/app/{create_app.py,routes_http.py,routes_ws.py}` | Split transport and delegate orchestration. |
| `src/livoia_web/prompts.py` | `EXPORT_ADAPT` | `src/livoia/services/prompt_rendering_service.py` + `domain/prompt_config.py` | Keep prompt behavior with typed contracts. |
| `src/livoia_web/adapters/bedrock_adapter.py` | `EXPORT_ADAPT` | `src/livoia/providers/bedrock/adapter.py` | Keep Bedrock bridge under provider boundary. |
| `src/livoia_web/static/index.html` | `EXPORT_ADAPT` | `src/livoia/web/static/index.html` | Keep UX baseline; remove camera controls. |
| `src/livoia_web/static/css/style.css` | `EXPORT_ADAPT` | `src/livoia/web/static/css/style.css` | Remove camera-specific styling. |
| `src/livoia_web/static/js/app.js` | `EXPORT_ADAPT` | `src/livoia/web/static/js/app.js` | Keep session/event flow; remove image capture/send logic; add `agent_id` bootstrap field. |
| `src/livoia_web/static/js/audio-player.js` | `EXPORT_AS_IS` | `src/livoia/web/static/js/audio-player.js` | Required audio playback path. |
| `src/livoia_web/static/js/audio-recorder.js` | `EXPORT_AS_IS` | `src/livoia/web/static/js/audio-recorder.js` | Required microphone capture path. |
| `src/livoia_web/static/js/pcm-player-processor.js` | `EXPORT_AS_IS` | `src/livoia/web/static/js/pcm-player-processor.js` | Required worklet. |
| `src/livoia_web/static/js/pcm-recorder-processor.js` | `EXPORT_AS_IS` | `src/livoia/web/static/js/pcm-recorder-processor.js` | Required worklet. |
| `src/livoia_web/__init__.py` | `EXPORT_ADAPT` | `src/livoia/__init__.py` | Adjust package exports to new structure. |
| `src/livoia_web/py.typed` | `EXPORT_AS_IS` | `src/livoia/py.typed` | Keep typing marker. |

### 3.2 `src/livoia_google`

| Source | Decision | Target | Rationale |
|---|---|---|---|
| `src/livoia_google/config.py` | `EXPORT_ADAPT` | `src/livoia/config/settings.py` + `providers/google/adapter.py` | Keep config behavior with centralized settings. |
| `src/livoia_google/agent.py` | `EXPORT_ADAPT` | `src/livoia/providers/google/adapter.py` | Move provider setup behind adapter interface. |
| `src/livoia_google/__init__.py` | `EXPORT_ADAPT` | `src/livoia/providers/google/__init__.py` | Re-export in target namespace. |
| `src/livoia_google/py.typed` | `EXPORT_AS_IS` | `src/livoia/py.typed` | Package typing marker retained. |

### 3.3 Bedrock internals from `src/livoia`

| Source | Decision | Target | Rationale |
|---|---|---|---|
| `src/livoia/modules/speech_caller.py` | `EXPORT_ADAPT` | `services/realtime_session_service.py` + `providers/bedrock/adapter.py` internals | Keep session coordination semantics with cleaner boundaries. |
| `src/livoia/clients/speech/bedrock_sonic.py` | `EXPORT_ADAPT` | `src/livoia/providers/bedrock/client.py` | Keep Bedrock streaming behavior. |
| `src/livoia/clients/speech/base.py` (`SpeechEvents`) | `EXPORT_ADAPT` | `src/livoia/domain/events.py` or `providers/bedrock` internals | Normalize event model for UI-facing contract. |

## 4) Runtime code intentionally excluded in stage 1

| Source area | Decision | Rationale |
|---|---|---|
| Camera/image path in `src/livoia_web/app.py` and `src/livoia_web/static/js/app.js` | `DO_NOT_EXPORT` | Explicit stage 1 exclusion. |
| `src/livoia/audio/**` | `DO_NOT_EXPORT` | Browser-based audio path makes this unnecessary. |
| `src/livoia/agent/**` | `DO_NOT_EXPORT` | Legacy orchestration superseded by session service. |
| `src/livoia/api/**` | `DO_NOT_EXPORT` | Not needed in stage 1 web product path. |
| `src/livoia/clients/embedding/**` | `DO_NOT_EXPORT` | Not needed for stage 1 parity. |
| `src/livoia/clients/llm/**` | `DO_NOT_EXPORT` | Not needed for stage 1 parity. |
| `src/livoia/modules/encoder_caller.py` | `DO_NOT_EXPORT` | Not needed in stage 1. |
| `src/livoia/modules/llm_caller.py` | `DO_NOT_EXPORT` | Not needed in stage 1. |
| `src/livoia/modules/cache_store.py` | `DO_NOT_EXPORT` | Not required for baseline. |
| `src/livoia/tools/processor.py` and `src/livoia/tools/implementations/**` | `DO_NOT_EXPORT` | Runtime tool execution deferred beyond stage 1. |

## 5) Resources and scripts

| Source | Decision | Target | Rationale |
|---|---|---|---|
| `resources/prompts/interview_agent.txt` | `EXPORT_ADAPT` | `resources/prompts/interviewer.md` | Keep canonical Interviewer prompt seed. |
| `resources/prompts/interview_agent_b.txt` | `DO_NOT_EXPORT` | - | Variant prompt not required for baseline. |
| `resources/prompts/test/**` | `DO_NOT_EXPORT` | - | Non-essential for stage 1 seed. |
| `resources/examples/**` | `DO_NOT_EXPORT` | - | Optional references only. |
| `scripts/**` | `DO_NOT_EXPORT` | - | CLI/manual scripts outside productized stage 1 scope. |

## 6) Tests migration

| Source | Decision | Target | Rationale |
|---|---|---|---|
| `tests/unit/**` | `EXPORT_ADAPT` | `tests/unit/**` | Keep and rewrite around target module boundaries. |
| `tests/integration/**` | `EXPORT_ADAPT` | `tests/integration/**` | Keep provider/websocket integration strategy. |
| `tests/e2e/**` | `EXPORT_ADAPT` | `tests/e2e/**` | Keep critical health/session behavior checks. |
| `tests/fixtures/**` | `EXPORT_ADAPT` | `tests/fixtures/**` | Reuse fixture patterns; adapt builders. |
| `tests/conftest.py` | `EXPORT_ADAPT` | `tests/conftest.py` | Update app import path and bootstrap fixtures. |

## 7) Stage 1 validation checklist

- Conversation + Settings behavior parity works on both providers.
- Bootstrap message includes valid `agent_id` and prompt config.
- Only Interviewer profile is enabled and accepted.
- No camera/image code path remains in frontend or backend.
- CI pipeline runs lint/type/test/build successfully.
- Docker image runs with env-var-injected credentials and healthy status.
