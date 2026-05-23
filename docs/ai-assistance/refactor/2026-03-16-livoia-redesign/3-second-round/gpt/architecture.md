# Architecture (Recommended)

## Chosen architecture

Use a **modular monolith** for stage 1.

Rationale:

- Fastest and safest path to production parity.
- Strong internal boundaries without microservice overhead.
- Easier consistency across providers and future agent use cases.
- Clean extension path for future prompt transparency, tool execution, and additional agent profiles.

## High-level component model

1. **Web/API layer (`app/`)**
   - FastAPI app factory, HTTP routes, WebSocket routes.
   - Static UI serving and health endpoint.

2. **Session orchestration layer (`services/realtime_session_service.py`)**
   - Owns websocket lifecycle.
   - Coordinates upstream messages and downstream provider events.
   - Normalizes event contract for the UI.

3. **Agent profile layer (`domain/agent_profile.py`, `services/agent_profile_service.py`)**
   - Resolves active use case (`interviewer` in stage 1).
   - Validates profile-specific prompt settings.
   - Produces profile-level session policy used by prompt rendering and providers.

4. **Prompt/configuration layer (`domain/prompt_config.py`, `services/prompt_rendering_service.py`, `config/settings.py`)**
   - Typed settings payload from UI.
   - Prompt rendering from profile defaults + runtime overrides.
   - Startup env validation and fail-fast checks.

5. **Provider adapter layer (`providers/`)**
   - Provider interface boundary and capability contract.
   - Google adapter and Bedrock adapter implementations.
   - SDK-specific event/payload translation isolated here.

6. **Observability/security layer (`observability/`)**
   - Structured logging for session/provider/error lifecycle.
   - Basic metrics hooks (connections, reconnects, failures, latency).
   - Redaction policy for sensitive values.

## Transport and routing strategy

Stage 1 keeps explicit provider routes to minimize migration risk:

- `/ws/google/{user_id}/{session_id}`
- `/ws/bedrock/{user_id}/{session_id}`

HTTP endpoints:

- `/` (serve app)
- `/health`
- `/static/*`

## Bounded contexts and responsibilities

- `app/`: routing/transport only; no provider SDK logic.
- `services/`: runtime orchestration and policy coordination.
- `providers/`: provider-specific API contracts and protocol mapping.
- `domain/`: typed models/contracts, pure domain definitions.
- `config/`: runtime settings and startup validation.
- `web/protocol/`: frontend/client message and event schemas.

## Stage 1 capability mapping

| Capability | Owning module(s) |
|---|---|
| Provider selection | `services/provider_selection_service.py` |
| Agent profile selection (stage 1 fixed) | `services/agent_profile_service.py` |
| Settings-driven prompt injection | `domain/prompt_config.py`, `services/prompt_rendering_service.py` |
| Live audio/text conversation | `services/realtime_session_service.py`, `providers/*/adapter.py` |
| Turn/interruption semantics | `domain/events.py`, `services/realtime_session_service.py` |
| Health and static serving | `app/routes_http.py` |

## Event protocol decisions

- Keep UI-facing event schema provider-neutral.
- Adapter layer maps provider-specific payloads into normalized events.
- Version protocol from start (for example `v1`) for forward compatibility.

## Multi-agent extensibility decisions

- Agent behavior must be defined by `AgentProfile` contracts, not route duplication.
- Profile selection is session-scoped and validated before provider startup.
- Providers consume rendered instruction + policy, not raw use-case semantics.
- Adding a new agent should mostly involve:
  - new profile registration,
  - prompt template and schema,
  - optional policy/capability updates.

## Architectural decisions

- ADR-001: modular monolith for stage 1.
- ADR-002: explicit provider adapter boundary with normalized event contract.
- ADR-003: typed prompt config as first websocket message.
- ADR-004: profile-based agent/use-case model with Interviewer only in stage 1.
- ADR-005: no camera/image runtime path in stage 1.
