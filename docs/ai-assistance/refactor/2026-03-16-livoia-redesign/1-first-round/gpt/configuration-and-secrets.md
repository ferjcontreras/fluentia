# Configuration and Secrets Strategy

## Objectives

- Be fully container-friendly for Docker/Kubernetes deployment.
- Keep secrets out of code and out of repository config files.
- Enforce typed validation at startup.
- Keep provider configs explicit and isolated.

## Configuration layers

1. **Environment variables** (source of truth in production).
2. **Typed settings models** (`pydantic-settings`) for validation and defaults.
3. **Runtime request config** (user prompt fields, non-secret).

## Suggested environment variable groups

### Core app

- `APP_ENV` (`development|staging|production`)
- `APP_LOG_LEVEL`
- `APP_PORT`
- `APP_ALLOWED_ORIGINS`

### Google provider

- `GOOGLE_API_KEY`
- `GOOGLE_MODEL`
- `GOOGLE_ENABLE_NATIVE_AUDIO_DEFAULT`

### Bedrock provider

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_SESSION_TOKEN`
- `AWS_REGION`
- `BEDROCK_MODEL_ID`
- `BEDROCK_VOICE_ID`

### Runtime controls

- `WS_MAX_CONCURRENT_SESSIONS`
- `WS_IDLE_TIMEOUT_SECONDS`
- `WS_MAX_MESSAGE_BYTES`

## Secret-handling policy

- Never log raw key/token values.
- Redact sensitive env vars at startup reporting.
- Separate config dump endpoint from secrets entirely.
- Keep secrets injected by runtime platform (Kubernetes + enterprise secret system).

## Prompt configuration policy

- `prompt_config` fields are treated as user content, not secrets.
- Apply schema validation and max-length limits.
- Store only short metadata in logs (field names, lengths), not full prompt text by default.

## Deployment notes

- Docker image should run with zero baked credentials.
- Service starts only when required provider config is valid.
- Optional provider support can be enabled by feature flag if credentials are absent.

## Future compatibility

- Add `TOOLS_*` and `ORCHESTRATOR_*` env groups later without changing base config contracts.
- Keep provider adapter constructors dependent on typed settings objects, not raw `os.environ`.
