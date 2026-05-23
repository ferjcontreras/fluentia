# Summary: Design Intuition and Key Decisions

## Core Insight

The agent framework already supports multiple agents, registries, and dynamic config fields. The gap is entirely in how the frontend discovers and presents this information. Phase 2 is primarily a UI project backed by a richer metadata API.

## Key Decisions

### 1. The frontend never hardcodes field names

Today, the settings form has four hardcoded `<input>` elements (`settingAgentName`, `settingCompanyName`, `settingQuestions`, `settingGuidelines`). These correspond to the Interviewer agent's `default_variables`.

In Phase 2, the frontend fetches agent metadata from `GET /api/agents` at page load, including the list of configurable fields with their types, labels, defaults, and display hints. The settings form is generated dynamically from this metadata. When the user selects a different agent, the form rebuilds itself.

This is the central design decision. It means adding a new agent with completely different fields (e.g., a "topic" field instead of "questions") requires no frontend changes.

### 2. Field metadata lives in the agent definition, not in a separate schema

Rather than creating a parallel configuration schema, each `AgentDefinition` carries field metadata alongside its `default_variables`. This keeps agent configuration self-contained: one file defines the agent's name, description, prompt template, tools, and field metadata.

The metadata is lightweight -- a label, an input type hint (text, textarea, select), and optionally a placeholder and description. This is not a full form schema language; it is the minimum needed to render a usable settings form.

### 3. Prompt Preview uses a server-side render endpoint

The frontend cannot render Jinja2 templates. Rather than shipping a JS template engine or duplicating prompt logic, the Prompt Preview panel calls `POST /api/agents/{name}/render-prompt` with the current field values and displays the result as read-only text.

This has a latency cost (a round-trip per preview update), but:
- The rendering is authoritative (same Jinja2 engine as the actual session).
- The template files stay server-side only.
- A debounce of 300-500ms makes the latency imperceptible during typing.

### 4. Agent selection happens before connection, not during

The user selects an agent and configures its fields before clicking "Start Conversation". Changing the agent while connected is not supported in Phase 2 -- it would require disconnecting and reconnecting (new prompt, potentially different tools). The selector and settings form are disabled during an active session.

This matches the existing behavior where provider selection triggers a reconnect. It avoids complexity around mid-session agent switching.

### 5. The prompt_config message becomes agent-agnostic

Today, `prompt_config` sends four hardcoded fields (`agent_name`, `company_name`, `questions`, `guidelines`). In Phase 2, it sends a generic `variables` dictionary:

```json
{
  "type": "prompt_config",
  "variables": {
    "agent_name": "Taylor",
    "company_name": "Avature",
    "questions": "..."
  }
}
```

The `SessionManager._receive_prompt_config()` method already merges user variables into the agent's defaults. The change is removing the hardcoded field name filter so it accepts any key present in the agent's `config_fields`.

This is a backward-compatible change: if the frontend sends the old format, the backend can detect and adapt. But since we control both sides, a clean switch is preferable.

### 6. The Q&A Assistant agent validates the framework

The second agent is deliberately simple: a general Q&A assistant that answers questions about a configurable topic. No tools. Two or three configurable fields (`agent_name`, `topic`, `guidelines`). This validates that the dynamic form works with a different field set and that the prompt_config flow handles arbitrary variables correctly.

## Trade-offs

| Decision | Benefit | Cost |
|----------|---------|------|
| Server-side prompt render | Authoritative, no template duplication | Network round-trip per preview |
| No mid-session agent switch | Simpler state management | User must reconnect to change agent |
| Field metadata in AgentDefinition | Self-contained agent files | Slightly larger dataclass |
| Dynamic form from API | Zero frontend changes for new agents | More complex initial form rendering |
| Generic prompt_config variables | Agent-agnostic protocol | Backend must validate against agent's known fields |

## Risks

1. **Form complexity**: If a future agent needs conditional fields, grouped sections, or validation rules, the lightweight metadata model may be insufficient. Mitigation: the metadata model is extensible (add optional keys) without breaking existing agents.

2. **Prompt preview latency**: On slow connections, the 300ms debounce plus round-trip may feel sluggish. Mitigation: show a loading indicator; the preview is informational, not blocking.

3. **Agent list growth**: If many agents are registered, a dropdown becomes unwieldy. Mitigation: not a concern for Phase 2 (2-3 agents). A card-based selector can replace the dropdown later.
