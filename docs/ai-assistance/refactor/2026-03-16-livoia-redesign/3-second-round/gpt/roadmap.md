# Roadmap

## Phase 1: Production parity baseline (Interviewer)

- Deliver stage 1 scope (Conversation + Settings, Google/Bedrock voice-text parity).
- Implement profile contract with only `interviewer` enabled.
- Hardening: typed config, structured logs, CI quality gates, Docker readiness.
- Publish onboarding docs and protocol references.

## Phase 2: Profile expansion foundation

- Add profile selector in UI and backend policy controls.
- Keep Interviewer as default profile.
- Add profile contract tests and profile-specific schema validation tests.

## Phase 3: Scheduler Agent

- Introduce `scheduler` profile with dedicated prompt schema and policy.
- Add schedule-intent settings and response constraints.
- Ensure provider-neutral behavior and no provider-specific business leakage.

## Phase 4: Avature Assistant Agent

- Introduce `avature-assistant` profile.
- Add domain-specific interaction policies and safety constraints.
- Expand observability for profile-specific diagnostics.

## Phase 5: Prompt transparency

- Add `Prompt` tab showing rendered prompt for active profile.
- Include safe preview controls and defaults/overrides explanation.
- Add test coverage for rendering consistency per profile.

## Phase 6: Tool-use transparency and runtime tools

- Add `Tool use` tab with live lifecycle events.
- Define normalized tool event schema with correlation IDs.
- Add configurable tool catalog and policy constraints.

## Phase 7: External orchestrator agent integration

- Integrate asynchronous bridge for external agent/tool execution.
- Keep live conversation active while long-running tasks execute.
- Add timeout, cancellation, and fallback semantics.

## Cross-phase guardrails

- Keep provider-neutral event protocol stable and versioned.
- Keep strict separation between orchestration, profiles, and provider adapters.
- Never leak credentials in logs or telemetry.
- Keep each phase independently releasable.
