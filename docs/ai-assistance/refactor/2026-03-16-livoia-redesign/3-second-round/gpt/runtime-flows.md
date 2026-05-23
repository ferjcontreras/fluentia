# Runtime Flows

## Flow 1: Session bootstrap

1. Browser initializes UI state.
2. Client creates `session_id` and opens provider websocket route.
3. Client sends first message as `prompt_config` including `agent_id`.
4. Server resolves `AgentProfile` and validates settings payload.
5. Server renders prompt from profile defaults + overrides.
6. Server initializes provider adapter with rendered instruction and policy.
7. Server starts upstream/downstream tasks and marks session active.

## Flow 2: Live conversation loop

## Upstream (user to model)

- Audio chunks stream from microphone pipeline to websocket binary frames.
- Text messages are sent as structured JSON messages.
- Session service translates inputs into provider adapter calls.

## Downstream (model to user)

- Provider adapter emits normalized events:
  - `content.text`
  - `content.audio`
  - `input_transcription`
  - `output_transcription`
  - `turn_complete`
  - `interrupted`
- Session service forwards events to the client.
- UI updates conversation view and event console.

## Flow 3: Provider switch

1. User changes provider in UI.
2. Existing websocket is intentionally closed.
3. New websocket opens for selected provider.
4. Client resends `prompt_config` and `agent_id`.
5. New provider adapter session starts.

## Flow 4: Settings update

1. User edits settings in `Settings` tab.
2. Values remain client-side until next conversation start/reconnect.
3. On next connection, settings are sent in first `prompt_config` message.
4. Server applies schema validation and bounded field limits.
5. Prompt is rendered and used for the new session.

## Flow 5: Turn and interruption lifecycle

- On interruption signal:
  - server emits `interrupted`,
  - UI flushes/halts active playback,
  - partial output is finalized as interrupted.
- On turn completion signal:
  - server emits `turn_complete`,
  - UI finalizes interim transcription indicators.

## Flow 6: Disconnect and reconnect

- Unexpected disconnect:
  - mark disconnected state,
  - apply bounded retry strategy with backoff and max attempts,
  - keep diagnostic event trail in logs/console.
- Intentional disconnect (provider/settings change):
  - treat as normal lifecycle event,
  - trigger fast reconnect path.

## Flow 7: Agent profile resolution (stage 1 + future)

1. Client sends `agent_id` in bootstrap message.
2. Server checks if profile exists and is enabled.
3. Stage 1 policy:
   - accept `interviewer` only,
   - reject other values with structured session error and close.
4. Future policy:
   - enable `scheduler` and `avature-assistant` profiles by config/feature flag.

## Error handling model

- Fail fast on invalid startup config.
- For session runtime failures:
  - isolate to affected session,
  - emit structured error event,
  - close adapter gracefully,
  - avoid process-wide crash.
- Classify provider errors retryable vs non-retryable and apply policy.

## Protocol guidance

- Keep first-message contract explicit (`prompt_config` + `agent_id`).
- Keep event schema provider-neutral and versioned.
- Keep profile-specific and provider-specific translation logic out of UI code.
