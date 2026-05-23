# Configuration and Secrets Strategy

## Objectives

- Be fully container-friendly for Docker/Kubernetes deployment.
- Keep secrets out of code and repository config files.
- Enforce typed validation at startup.
- Keep provider and agent-profile configuration explicit and isolated.

## Configuration layers

1. **Environment variables** as production source of truth.
2. **Typed settings models** (`pydantic-settings`) for defaults and validation.
3. **Runtime request config** for prompt fields and selected `agent_id`.

## Suggested environment variable groups

## Core app

- `APP_ENV` (`development|staging|production`)
- `APP_LOG_LEVEL`
- `APP_PORT`
- `APP_ALLOWED_ORIGINS`
- `WS_MAX_CONCURRENT_SESSIONS`
- `WS_IDLE_TIMEOUT_SECONDS`
- `WS_MAX_MESSAGE_BYTES`

## Agent profile controls

- `AGENT_DEFAULT_ID` (stage 1: `interviewer`)
- `AGENT_ENABLED_IDS` (stage 1: `interviewer`)
- `AGENT_PROFILE_STRICT_MODE` (reject unknown/disabled profiles)

## Google provider

- `GOOGLE_API_KEY`
- `GOOGLE_MODEL`
- `GOOGLE_USE_VERTEX_AI`
- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_CLOUD_LOCATION`
- `GOOGLE_ENABLE_NATIVE_AUDIO_DEFAULT`

## Bedrock provider

- `AWS_ACCESS_KEY_ID` (optional in cloud if IAM role used)
- `AWS_SECRET_ACCESS_KEY` (optional in cloud if IAM role used)
- `AWS_SESSION_TOKEN` (optional in cloud if IAM role used)
- `AWS_REGION`
- `BEDROCK_MODEL_ID`
- `BEDROCK_VOICE_ID`
- `BEDROCK_INPUT_SAMPLE_RATE`
- `BEDROCK_OUTPUT_SAMPLE_RATE`

## Future tool/orchestrator controls (reserved)

- `TOOLS_ENABLE_RUNTIME`
- `ORCHESTRATOR_API_URL`
- `ORCHESTRATOR_AUTH_TOKEN`

## Secret handling policy

- Never log raw secrets.
- Redact sensitive env vars in startup diagnostics.
- Keep config-dump endpoints separated from secret values.
- Inject secrets via runtime platform only.

## Prompt and profile payload policy

- `prompt_config` fields are user content, not secrets.
- Validate against profile schema with max-length and shape constraints.
- Log only metadata (field names, lengths, agent_id), not raw prompt text by default.

## Startup validation policy

- Required provider settings are validated at process startup.
- If one provider is intentionally disabled, startup still succeeds if policy allows and routing reflects that state.
- `AGENT_ENABLED_IDS` must include at least one valid profile.
- Stage 1 default startup should expose only Interviewer profile.

## Deployment notes

- Docker image contains no baked credentials.
- Service starts only when required config is valid.
- Optional provider/profile enablement can be controlled via env-driven feature flags.

## Future compatibility

- New profiles should be additive: new prompt schema + defaults + policy.
- New tools/orchestrator env groups should not break existing config contracts.
- Provider adapters receive typed settings objects, never raw `os.environ`.
