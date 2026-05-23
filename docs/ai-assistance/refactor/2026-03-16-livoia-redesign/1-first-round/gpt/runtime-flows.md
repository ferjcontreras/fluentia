# Runtime Flows

## Flow 1: Session bootstrap

1. Browser opens app and initializes UI state.
2. Client creates `session_id` and opens WebSocket to selected provider route.
3. Client sends `prompt_config` as first message.
4. Server validates settings and renders prompt.
5. Server initializes provider adapter with rendered instruction.
6. Server starts upstream/downstream tasks.
7. UI reflects connected state and enables controls.

## Flow 2: Live conversation loop

### Upstream (user to model)

- Audio chunks are streamed from microphone pipeline to websocket.
- Text messages are sent as structured JSON.
- Orchestrator layer converts messages into provider adapter calls.

### Downstream (model to user)

- Provider adapter yields normalized events:
  - `content.text`
  - `content.audio`
  - `input_transcription`
  - `output_transcription`
  - `turn_complete`
  - `interrupted`
- Session service forwards normalized events to UI.
- UI updates conversation pane and event console.

## Flow 3: Provider switch

1. User changes provider in UI.
2. Current websocket is intentionally closed.
3. New session websocket is opened with selected provider.
4. New `prompt_config` is sent and new provider adapter is created.
5. Conversation resumes under new provider contract.

## Flow 4: Prompt customization

1. User edits settings values in `Settings` tab.
2. Values are held client-side until next conversation start.
3. On new connection, settings are sent in `prompt_config`.
4. Server renders prompt with defaults + overrides.
5. Session logs prompt field usage metadata (not raw secrets).

## Flow 5: Interruption and turn lifecycle

- On provider interruption signal:
  - Server emits `interrupted` event.
  - UI stops/flushes active audio playback state.
  - Partial output bubble is finalized as interrupted.
- On turn completion signal:
  - Server emits `turn_complete`.
  - UI finalizes partial typing/transcription indicators.

## Flow 6: Disconnect and reconnect

- Unexpected disconnect:
  - Mark connection state as disconnected.
  - Trigger bounded retry policy with backoff and max attempts.
  - Keep diagnostic event trail in console/logs.
- Intentional disconnect (settings/provider change):
  - No error semantics in UI.
  - Fast reconnect path.

## Error handling model

- Fail fast on invalid startup config.
- For session runtime failures:
  - isolate to affected session,
  - emit structured error event,
  - close adapter gracefully,
  - avoid process-wide crash.
- For provider temporary errors:
  - classify retryable vs non-retryable,
  - apply per-provider retry policy where safe.

## Event protocol guidance

- Keep UI-facing event schema provider-neutral.
- Map provider-specific payloads only inside adapters.
- Version the protocol (for example `v1`) to support forward compatibility.
