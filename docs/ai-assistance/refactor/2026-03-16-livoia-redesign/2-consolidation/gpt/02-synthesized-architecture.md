# Synthesized Architecture (Recommended)

## 1) Final recommendation

Adopt a **stage-1-first modular monolith** with strict scope control:

- Preserve current web-demo user behavior (Conversation + Settings, Google + Bedrock, audio/text, prompt_config first message, event console).
- Exclude camera/image path in stage 1 in both backend and frontend.
- Keep one deployable service and one frontend bundle.
- Define explicit boundaries between transport, orchestration, provider adapters, prompt/config, and observability.

This architecture combines GPT's scope discipline with Claude's migration concreteness.

## 2) Architecture shape

## Layers and ownership

1. `app/` (transport)
   - FastAPI app factory.
   - HTTP routes (`/`, `/health`, static serving).
   - WebSocket routes and connection bootstrap.

2. `services/` (runtime orchestration)
   - Session lifecycle control.
   - Upstream/downstream task coordination.
   - Provider selection and provider-neutral event forwarding.

3. `providers/` (SDK and protocol adapters)
   - `google` adapter wrapping ADK live runner flow.
   - `bedrock` adapter wrapping Bedrock streaming flow.
   - Provider-specific payload translation isolated here.

4. `domain/` (typed contracts)
   - Prompt config schema.
   - Normalized UI event schema.
   - Session state types.

5. `config/` (typed settings)
   - `pydantic-settings` models.
   - startup validation and defaults.

6. `observability/`
   - Structured logging setup.
   - metrics hooks and redaction policies.

## 3) Runtime contracts

## WebSocket session bootstrap

1. Client opens provider route.
2. First text message must be `prompt_config`.
3. Server validates + renders prompt.
4. Server starts provider adapter session.
5. Server runs upstream/downstream tasks until disconnect.

## Normalized UI event contract

Maintain provider-neutral events exposed to frontend:

- `content` (audio/text payload envelope)
- `inputTranscription`
- `outputTranscription`
- `turnComplete`
- `interrupted`
- structured error event for session-scoped failures

Provider SDK event formats stay internal to adapters.

## 4) Route strategy

Keep two explicit stage-1 routes for minimal churn and parity:

- `/ws/google/{user_id}/{session_id}`
- `/ws/bedrock/{user_id}/{session_id}`

Why this choice:

- Current frontend and backend already align to this contract.
- Reduces migration risk and regression surface.
- A unified `/ws/{provider}/...` route can be introduced later with low effort if desired.

## 5) Scope decisions (hard boundaries)

## Included in stage 1

- Conversation + Settings tabs.
- Prompt-config injection at connection start.
- Google/Bedrock live bidirectional voice + text behavior parity.
- Event console and health endpoint.
- CI/tooling parity and Docker readiness.

## Excluded in stage 1

- Camera/image capture and image message flow.
- Prompt tab and Tool Use tab.
- User-configurable runtime tool registry.
- External orchestrator-agent tool execution.

## 6) Quality and operations baseline

- Preserve `uv`, `ruff`, `mypy`, `pylint`, `pytest`, `tox`, `pre-commit`.
- Keep GitLab CI stage structure (`quality`, `tests`, `dependency-analysis`, `build`).
- Docker image runs non-root, with `/health` probe and env-var-first configuration.
- Startup fails fast on invalid required provider configuration.
- Sensitive values must be redacted from logs.

## 7) Why this synthesis is preferred

- Lower delivery risk than Gemini-style broader re-platforming.
- Better scope control than Claude-only draft where image details still appear.
- More actionable than GPT-only draft by borrowing concrete migration execution detail.
- Provides a clean step-2 path for prompt/tool transparency and async orchestration without polluting stage 1.
