# Roadmap

## Phase 1: Production parity baseline

- Deliver stage 1 scope (Conversation + Settings tabs, Google/Bedrock voice/text parity).
- Hardening: typed config, structured logs, CI quality gates, Docker readiness.
- Publish onboarding docs in `guides`, `reference`, `tutorials`.

## Phase 2: Prompt transparency

- Add `Prompt` tab showing rendered prompt from current settings.
- Include safe preview controls and explain defaults/overrides.
- Add test coverage for prompt rendering consistency.

## Phase 3: Tool-use transparency

- Add `Tool use` tab with live timeline of tool events.
- Define normalized tool event schema and correlation IDs.
- Persist short-lived tool traces for support diagnostics.

## Phase 4: User-configurable tools

- Add configurable tool catalog (enable/disable + scoped params).
- Introduce policy controls for allowed tools per environment.
- Validate and sandbox tool requests.

## Phase 5: External orchestrator agent tools

- Integrate asynchronous tool bridge to orchestrator agents.
- Keep live voice conversation active while external agents run.
- Push completion/progress events back to the UI and conversation context.
- Add timeout/fallback and cancellation semantics.

## Cross-phase guardrails

- Keep provider-neutral event protocol stable.
- Maintain strict separation of orchestration and provider adapter logic.
- Avoid leaking credentials in logs/telemetry.
- Ensure each phase is independently releasable.
