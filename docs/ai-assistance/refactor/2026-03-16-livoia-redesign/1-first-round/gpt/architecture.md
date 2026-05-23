# Architecture (Recommended)

## Chosen architecture

Use a **modular monolith** for stage 1.

Rationale:
- Fastest path to production while preserving current behavior.
- Strong internal boundaries without the deployment overhead of microservices.
- Easier cross-provider consistency in event protocol and session lifecycle.
- Clean extension path for future prompt/tool transparency and tool execution.

## High-level component model

1. **Web/API layer**
   - FastAPI app factory, HTTP routes, WebSocket routes.
   - Static UI serving and health endpoints.

2. **Session orchestration layer**
   - Owns websocket connection lifecycle.
   - Owns session state transitions and event normalization.
   - Coordinates upstream client messages and downstream provider events.

3. **Prompt/configuration layer**
   - Typed settings payload from UI.
   - Prompt rendering service used at session bootstrap.
   - Validation and defaults policy.

4. **Provider adapter layer**
   - Provider-agnostic interface (`connect`, `send_audio`, `send_text`, `receive_events`, `close`).
   - Google adapter implementation.
   - Bedrock adapter implementation.

5. **Observability/security layer**
   - Structured logs for session, provider, and error events.
   - Basic metrics hooks (connections, reconnects, provider failures, latency buckets).
   - Sensitive-value redaction policy.

## Bounded contexts and responsibilities

- `app/`: transport routing only, no provider business logic.
- `services/`: runtime orchestration and policy decisions.
- `providers/`: SDK-specific and protocol translation logic.
- `domain/`: typed models and contracts; no network side effects.
- `config/`: startup/runtime settings and env validation.
- `web/protocol/`: schema for client/server payloads.

## Stage 1 capability mapping

| Capability | Owning module(s) |
|---|---|
| Provider selection | `services/provider_selection_service.py` |
| Settings-driven prompt injection | `domain/prompt_config.py`, `services/prompt_rendering_service.py` |
| Live bidirectional audio/text | `services/realtime_session_service.py`, `providers/*_bidi_adapter.py` |
| Turn/interruption semantics | `domain/events.py`, `services/realtime_session_service.py` |
| Connection status and reconnection policy | `app/routes_ws.py`, `services/realtime_session_service.py` |
| Health check | `app/routes_http.py` |

## Extension points for future features

1. **Prompt tab**
   - Add a read endpoint/service to expose the rendered prompt for current settings.
   - Reuse existing prompt rendering service to avoid divergence.

2. **Tool use tab**
   - Emit normalized tool lifecycle events (`tool_started`, `tool_progress`, `tool_completed`, `tool_failed`).
   - Feed these events to UI stream and log pipeline.

3. **Configurable tools**
   - Introduce `ToolCatalog` and `ToolPolicy` abstractions in `domain/` + `services/`.
   - Provider adapters consume a unified tool contract, not raw UI payloads.

4. **External orchestrator agents**
   - Add asynchronous tool bridge interface with correlation IDs and callback events.
   - Keep session conversation uninterrupted while long-running tool tasks execute.

## Architectural decisions

- ADR-001: modular monolith for stage 1.
- ADR-002: explicit provider adapter interface and event normalization boundary.
- ADR-003: typed prompt settings contract as first message at session bootstrap.
- ADR-004: no camera/image path in stage 1; keep protocol reserved for future.
