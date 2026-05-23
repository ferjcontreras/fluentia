# Agent Use-Case Model

## Objective

Define how the platform supports multiple conversational agent behaviors over time while shipping only one use case in stage 1.

## Terminology

- **Agent Use Case:** Business behavior package (purpose, prompt, settings schema, policy constraints).
- **Provider:** Runtime speech/model backend (Google or Bedrock in stage 1).
- **Session:** One websocket conversation instance combining one provider and one agent use case.

## Stage 1 supported use case

## Interviewer Agent

Purpose:
- Conduct structured but natural interview conversations.

Core behavior:
- Uses configurable prompt fields such as agent name, company, questions, and guidelines.
- Keeps conversational flow aligned to interview process.

Settings contract (stage 1):
- `agent_name`
- `company_name`
- `questions`
- `guidelines`

## Future use cases (not implemented in stage 1)

## Scheduler Agent

Expected behavior:
- Gather scheduling intent (participants, date/time constraints, timezone, duration).
- Propose candidate slots and finalize one.

Future settings examples:
- `default_timezone`
- `working_hours`
- `scheduling_policy`

## Avature Assistant Agent

Expected behavior:
- Support conversational tasks related to Avature workflows and records.
- Provide guided interactions and clarifications while respecting access/policy boundaries.

Future settings examples:
- `assistant_scope`
- `interaction_mode`
- `domain_context_profile`

## Design contract for extensibility

Agent behavior should be represented by a typed profile abstraction.

```text
AgentProfile
- id
- display_name
- stage (ga|beta|disabled)
- prompt_template_id
- prompt_settings_schema
- prompt_defaults
- provider_capabilities_policy
- feature_flags
```

Stage 1 policy:
- Register only one profile (`interviewer`) as enabled.
- Keep profile registry and schema validation infrastructure in place.
- UI can internally carry agent identity but should display only Interviewer options in stage 1.

## Backend responsibilities

1. Validate incoming `agent_id` and settings payload against profile schema.
2. Render prompt through profile-specific template and defaults policy.
3. Apply provider capability checks before session start.
4. Emit profile metadata in session logs (never secret values).

## Frontend responsibilities

1. Hold settings fields for active profile.
2. Send `prompt_config` + `agent_id` as first message.
3. Keep behavior unchanged for Interviewer in stage 1.
4. Preserve structure to add profile selector later with minimal UI rewrite.

## Provider compatibility policy

- Providers stay generic and agnostic of business use-case semantics.
- Agent-specific behavior should be resolved before adapter initialization.
- Provider adapters consume rendered instructions and normalized session policy only.

## Why this model is important

Without this contract, each new use case would likely duplicate websocket handlers, prompt logic, and validation paths. A typed profile model keeps growth controlled and avoids branching by ad hoc conditionals across the codebase.
