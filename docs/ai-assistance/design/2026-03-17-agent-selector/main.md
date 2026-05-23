# Phase 2: Multi-Agent Support and Prompt Transparency

## Problem Statement

Fluentia currently supports a single agent type (Interviewer). The settings form is hardcoded to four fields specific to that agent. There is no way for users to select between different agent types, see what prompt will be sent to the model, or extend the system with new agents without modifying the frontend.

This limits the platform to a single use case. Avature's ML team needs to experiment with multiple agent types (interviewer, Q&A assistant, scheduler) using the same voice infrastructure.

## Objectives

1. **Agent selection**: Users can choose an agent type before starting a conversation.
2. **Dynamic configuration**: The settings form adapts to display the selected agent's configurable fields, with no hardcoded field names in the frontend.
3. **Prompt transparency**: Users can preview the fully rendered system prompt before and during a session, making the agent's behavior inspectable.
4. **Extensibility**: Adding a new agent requires only backend changes (a new `AgentDefinition` and Jinja2 template). The frontend adapts automatically via the `/api/agents` endpoint.

## Scope

### In scope

- Agent selector UI component
- Dynamic settings form driven by agent metadata
- Prompt Preview panel
- `/api/agents` endpoint enhancement (field metadata: types, labels, defaults)
- At least one additional agent definition (Q&A assistant)
- Prompt rendering endpoint (`/api/agents/{name}/render-prompt`)

### Out of scope

- Tool configuration or tool activity UI (Phase 3-4)
- New tools or provider changes
- Agent creation or editing at runtime (agents are code-defined)
- Multi-session or conversation history

## Success Criteria

1. A user can select "Interview Agent" or "Q&A Assistant" from the UI and conduct a voice conversation with each.
2. Switching agents causes the settings form to display the correct fields with appropriate labels, defaults, and input types.
3. The Prompt Preview panel shows the fully rendered system prompt using the current field values, updating live as the user edits fields.
4. Adding a third agent type requires zero frontend code changes.

## Design Documents

| Document | Contents |
|----------|----------|
| [summary.md](summary.md) | Design intuition, key decisions, trade-offs |
| [detailed-design.md](detailed-design.md) | Component specifications, data models, API contracts |
| [details-frontend.md](details-frontend.md) | UI layout, interaction design, state management |
| [details-backend.md](details-backend.md) | Backend changes, agent metadata model, new endpoint |
