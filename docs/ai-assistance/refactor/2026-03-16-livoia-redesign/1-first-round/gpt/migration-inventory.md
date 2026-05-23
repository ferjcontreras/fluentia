# Migration Inventory (Stage 1)

Decision legend:
- `EXPORT_AS_IS`: move with minimal or no changes
- `EXPORT_ADAPT`: move after structural/behavioral adaptation
- `DO_NOT_EXPORT`: intentionally excluded from new production repo stage 1

## 1) Root tooling and project files

| Source | Decision | Target | Rationale |
|---|---|---|---|
| `pyproject.toml` | `EXPORT_ADAPT` | `pyproject.toml` | Keep quality/tooling stack; prune PoC-only deps and rename package. |
| `tox.ini` | `EXPORT_ADAPT` | `tox.ini` | Keep env structure; update package paths and test markers if needed. |
| `.github/workflows/ci.yml` | `EXPORT_ADAPT` | `.github/workflows/ci.yml` | Preserve CI stages/jobs with path and image naming updates. |
| `.pre-commit-config.yaml` | `EXPORT_AS_IS` | `.pre-commit-config.yaml` | Same hooks baseline is valid. |
| `check_code.sh` | `EXPORT_ADAPT` | `check_code.sh` | Keep developer workflow; update package paths (`livoia_prod`). |
| `Dockerfile` | `EXPORT_ADAPT` | `Dockerfile` | Keep container path, optimize for production multi-stage if possible. |
| `docker/entrypoint.sh` | `EXPORT_ADAPT` | `docker/entrypoint.sh` | Keep startup strategy with app module path updates. |
| `docker/healthcheck.sh` | `EXPORT_ADAPT` | `docker/healthcheck.sh` | Keep health probe with endpoint/path updates if needed. |
| `.dockerignore` | `EXPORT_AS_IS` | `.dockerignore` | General patterns remain useful. |
| `.gitignore` | `EXPORT_ADAPT` | `.gitignore` | Keep baseline, align with new package and outputs. |
| `.githooks.yaml` | `EXPORT_ADAPT` | `.githooks.yaml` | Keep if used by team workflows; validate relevance. |
| `uv.lock` | `EXPORT_ADAPT` | `uv.lock` | Regenerate after dependency curation in new repo. |
| `.env.example` | `EXPORT_ADAPT` | `.env.example` | Keep as dev template, align to new env schema. |
| `.env` | `DO_NOT_EXPORT` | - | Local secret file must not be migrated. |

## 2) Documentation

### 2.1 Preserve recursively

| Source | Decision | Target | Rationale |
|---|---|---|---|
| `docs/ai-assistance/**` | `EXPORT_AS_IS` | `docs/ai-assistance/**` | Explicit requirement: preserve recursively. |

### 2.2 Guides and tutorials

| Source | Decision | Target | Rationale |
|---|---|---|---|
| `docs/guides/about-avature.md` | `EXPORT_AS_IS` | `docs/guides/about-avature.md` | Required carry-over context. |
| `docs/guides/technical-writing-style-guide.md` | `EXPORT_AS_IS` | `docs/guides/technical-writing-style-guide.md` | Required carry-over writing standard. |
| `docs/guides/code-style-guide.md` | `EXPORT_ADAPT` | `docs/guides/code-style-guide.md` | Re-version for new package structure and updated standards. |
| `docs/guides/test-development-guide.md` | `EXPORT_ADAPT` | `docs/guides/test-development-guide.md` | Re-version for new runtime boundaries and test focus. |
| `docs/guides/commit-message-guide.md` | `EXPORT_ADAPT` | `docs/guides/commit-message-guide.md` | Re-version while preserving conventions. |
| `docs/tutorials/voice-interview-agent-web-demo.md` | `EXPORT_ADAPT` | `docs/tutorials/run-web-demo.md` | Keep behavior docs but update commands and architecture references. |
| `docs/tutorials/voice-interview-agent-cli-demo.md` | `DO_NOT_EXPORT` | - | CLI demo not in stage 1 scope. |
| `docs/discussions/codemap-semantic-search-tree.md` | `DO_NOT_EXPORT` | - | Historical discussion, low value for new production repo baseline. |

### 2.3 New docs to add in new repo

- `docs/reference/architecture-overview.md`
- `docs/reference/configuration-reference.md`
- `docs/reference/websocket-event-protocol.md`
- `docs/tutorials/local-development.md`
- `docs/tutorials/provider-setup.md`

## 3) Runtime code - web/product path

### 3.1 `src/livoia_web`

| Source | Decision | Target | Rationale |
|---|---|---|---|
| `src/livoia_web/app.py` | `EXPORT_ADAPT` | `src/livoia_prod/app/{create_app.py,routes_http.py,routes_ws.py}` | Split responsibilities and harden orchestration. |
| `src/livoia_web/prompts.py` | `EXPORT_ADAPT` | `src/livoia_prod/services/prompt_rendering_service.py` + `domain/prompt_config.py` | Keep behavior with typed contract and cleaner layering. |
| `src/livoia_web/adapters/bedrock_adapter.py` | `EXPORT_ADAPT` | `src/livoia_prod/providers/bedrock_bidi_adapter.py` | Keep essential Bedrock bridge with explicit provider interface. |
| `src/livoia_web/adapters/__init__.py` | `EXPORT_ADAPT` | `src/livoia_prod/providers/__init__.py` | Re-export under new boundary. |
| `src/livoia_web/static/index.html` | `EXPORT_ADAPT` | `src/livoia_prod/web/static/index.html` | Keep Conversation/Settings UX, remove camera feature elements. |
| `src/livoia_web/static/css/style.css` | `EXPORT_ADAPT` | `src/livoia_prod/web/static/css/style.css` | Keep and clean styling to match removed camera path. |
| `src/livoia_web/static/js/app.js` | `EXPORT_ADAPT` | `src/livoia_prod/web/static/js/app.js` | Preserve event/session behavior, remove camera/image logic, modularize where possible. |
| `src/livoia_web/static/js/audio-player.js` | `EXPORT_AS_IS` | `src/livoia_prod/web/static/js/audio-player.js` | Core audio playback path required. |
| `src/livoia_web/static/js/audio-recorder.js` | `EXPORT_AS_IS` | `src/livoia_prod/web/static/js/audio-recorder.js` | Core microphone stream path required. |
| `src/livoia_web/static/js/pcm-player-processor.js` | `EXPORT_AS_IS` | `src/livoia_prod/web/static/js/pcm-player-processor.js` | Required worklet for audio playback. |
| `src/livoia_web/static/js/pcm-recorder-processor.js` | `EXPORT_AS_IS` | `src/livoia_prod/web/static/js/pcm-recorder-processor.js` | Required worklet for microphone capture. |
| `src/livoia_web/__init__.py` | `EXPORT_ADAPT` | `src/livoia_prod/__init__.py` or `src/livoia_prod/app/__init__.py` | Adjust exports for new package layout. |
| `src/livoia_web/py.typed` | `EXPORT_AS_IS` | `src/livoia_prod/py.typed` | Keep typing marker. |

### 3.2 `src/livoia_google`

| Source | Decision | Target | Rationale |
|---|---|---|---|
| `src/livoia_google/config.py` | `EXPORT_ADAPT` | `src/livoia_prod/providers/google_bidi_adapter.py` + `config/settings.py` | Keep config behavior but centralize runtime settings. |
| `src/livoia_google/agent.py` | `EXPORT_ADAPT` | `src/livoia_prod/providers/google_bidi_adapter.py` | Move provider setup behind adapter contract. |
| `src/livoia_google/__init__.py` | `EXPORT_ADAPT` | `src/livoia_prod/providers/__init__.py` | Re-export in new namespace. |
| `src/livoia_google/py.typed` | `EXPORT_AS_IS` | `src/livoia_prod/py.typed` | Typing marker retained at package level. |

## 4) Runtime code - legacy/PoC internals (`src/livoia`)

Stage 1 should export only what is needed for the web demo parity.

| Source area | Decision | Target | Rationale |
|---|---|---|---|
| `src/livoia/modules/speech_caller.py` | `EXPORT_ADAPT` | `src/livoia_prod/providers/bedrock_bidi_adapter.py` internals | Needed for Bedrock streaming path. |
| `src/livoia/clients/speech/bedrock_sonic.py` | `EXPORT_ADAPT` | `src/livoia_prod/providers/bedrock_bidi_adapter.py` internals | Needed for Bedrock provider IO. |
| `src/livoia/tools/base.py` | `EXPORT_ADAPT` | `src/livoia_prod/domain/tools/base.py` (future-facing) | Keep minimal tool contract for roadmap readiness. |
| `src/livoia/tools/processor.py` | `DO_NOT_EXPORT` | - | Full tool execution not in stage 1 scope. |
| `src/livoia/tools/implementations/**` | `DO_NOT_EXPORT` | - | Built-in tools not needed in stage 1. |
| `src/livoia/audio/**` | `DO_NOT_EXPORT` | - | Browser-based web stage does not require PyAudio pipeline. |
| `src/livoia/agent/**` | `DO_NOT_EXPORT` | - | Legacy orchestration superseded by new session service. |
| `src/livoia/api/**` | `DO_NOT_EXPORT` | - | Separate PoC API surface not required for web stage 1. |
| `src/livoia/clients/embedding/**` | `DO_NOT_EXPORT` | - | Not needed for stage 1 conversation parity. |
| `src/livoia/clients/llm/**` | `DO_NOT_EXPORT` | - | Not needed for stage 1 conversation parity. |
| `src/livoia/modules/encoder_caller.py` | `DO_NOT_EXPORT` | - | Not needed for stage 1. |
| `src/livoia/modules/llm_caller.py` | `DO_NOT_EXPORT` | - | Not needed for stage 1. |
| `src/livoia/modules/cache_store.py` | `DO_NOT_EXPORT` | - | Not needed for stage 1 baseline. |
| `src/livoia/utils/prompt_templates.py` | `EXPORT_ADAPT` | `src/livoia_prod/services/prompt_rendering_service.py` helpers | Keep only useful prompt utilities. |
| `src/livoia/utils/{env.py,logging.py,helper.py}` | `EXPORT_ADAPT` | `src/livoia_prod/{config,observability}/...` | Reuse selectively with clearer separation. |
| `src/livoia/main.py` | `DO_NOT_EXPORT` | - | Entrypoint replaced by new app package conventions. |

## 5) Resources and scripts

| Source | Decision | Target | Rationale |
|---|---|---|---|
| `resources/prompts/interview_agent.txt` | `EXPORT_ADAPT` | `resources/prompts/interview_agent.txt` | Keep canonical prompt with possible refinements. |
| `resources/prompts/interview_agent_b.txt` | `DO_NOT_EXPORT` | - | Variant prompt not required for stage 1 baseline. |
| `resources/prompts/test/**` | `DO_NOT_EXPORT` | - | Non-essential for initial production seed. |
| `resources/examples/**` | `DO_NOT_EXPORT` | - | Evaluate later as optional references. |
| `scripts/voice_interview_agent_demo.py` | `DO_NOT_EXPORT` | - | CLI PoC script outside productized web scope. |
| `scripts/voice_agent.py` | `DO_NOT_EXPORT` | - | CLI/general assistant PoC path. |
| `scripts/voice_agent_legacy.py` | `DO_NOT_EXPORT` | - | Legacy path not for production seed. |
| `scripts/voice_agent_manual.py` | `DO_NOT_EXPORT` | - | Manual testing script, non-product. |
| `scripts/voice_agent_reference.py` | `DO_NOT_EXPORT` | - | Reference code intentionally not part of production baseline. |

## 6) Tests migration

| Source | Decision | Target | Rationale |
|---|---|---|---|
| `tests/unit/**` | `EXPORT_ADAPT` | `tests/unit/**` | Keep structure; rewrite around new module boundaries. |
| `tests/integration/**` | `EXPORT_ADAPT` | `tests/integration/**` | Keep integration strategy for provider and websocket flows. |
| `tests/e2e/**` | `EXPORT_ADAPT` | `tests/e2e/**` | Keep key health/observability/system checks. |
| `tests/fixtures/**` | `EXPORT_ADAPT` | `tests/fixtures/**` | Reuse fixture style, adapt object factories. |
| `tests/conftest.py` | `EXPORT_ADAPT` | `tests/conftest.py` | Update app import paths and session setup. |

## 7) Priority order for migration execution

1. Project skeleton + quality/CI files.
2. `livoia_web` + `livoia_google` essential paths.
3. Minimal Bedrock support internals from `livoia`.
4. Prompt/resource migration.
5. Test scaffolding and critical test suites.
6. Documentation set (`guides`, `reference`, `tutorials`).

## 8) Validation checklist for migrated scope

- Conversation + Settings stage 1 UX works for Google and Bedrock.
- No camera/image code path present in UI or backend routes.
- Prompt settings are applied at session start.
- CI pipeline runs lint/type/test/build jobs successfully.
- Docker image runs with env-var injected provider credentials.
