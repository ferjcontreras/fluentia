# Frontend Details

## UI Layout Changes

### Settings Tab: Before and After

**Phase 1 (current):**

```
Settings Tab
┌─────────────────────────────────────────────┐
│ Customization Layer                         │
│   Agent Name: [Taylor          ]            │
│   Guidelines: [textarea........]            │
│                                             │
│ Use Case                                    │
│   Company Name: [Avature       ]            │
│   Interview Questions: [textarea]           │
│                                             │
│ "Changes apply when starting a new          │
│  conversation."                             │
└─────────────────────────────────────────────┘
```

**Phase 2 (proposed):**

```
Settings Tab
┌─────────────────────────────────────────────┐
│ Agent                                       │
│   [▼ Interview Agent               ]  ←── agent selector dropdown
│   "Conducts structured voice interviews     │
│    with customizable questions."            │
│                                             │
│ Configuration                               │
│   Agent Name: [Taylor          ]    ←── dynamically generated
│   Company Name: [Avature       ]        from agent.fields
│   Interview Questions: [textarea]           │
│   Guidelines: [textarea........]            │
│                                             │
│ ┌─ Prompt Preview ────────────────────────┐ │
│ │ You are Taylor, a professional and      │ │
│ │ friendly interviewer conducting a voice  │ │
│ │ interview on behalf of Avature...       │ │
│ │                                         │ │
│ │ (read-only, updates live as fields      │ │
│ │  are edited)                            │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ "Changes apply when starting a new          │
│  conversation."                             │
└─────────────────────────────────────────────┘
```

### Agent Selector Component

The selector is a `<select>` dropdown at the top of the Settings tab. It replaces the hardcoded "Customization Layer" section header.

| Element | Details |
|---------|---------|
| Label | "Agent" |
| Type | `<select>` dropdown |
| Options | Populated from `GET /api/agents` response |
| Display text | `agent.display_name` (e.g., "Interview Agent") |
| Value | `agent.name` (e.g., "interviewer") |
| Default | First agent in the list, or the agent matching `AppConfig.default_agent` |
| Disabled when | A voice session is active |

Below the dropdown, the agent's `description` is displayed as muted help text.

### Dynamic Settings Form

When the user selects an agent, the "Configuration" section is rebuilt:

1. Clear all existing field elements from the form container.
2. Retrieve the selected agent's `fields` array from the cached `/api/agents` response.
3. For each field (sorted by `order`):
   - Create a `<div class="settings-field">` container.
   - Create a `<label>` with the field's `label` text.
   - Create the input element based on `field_type`:
     - `"text"` -> `<input type="text">` with `placeholder` and `value` set to `default`.
     - `"textarea"` -> `<textarea>` with `placeholder`, `rows`, and content set to `default`.
     - `"select"` -> `<select>` with `<option>` elements from `options`, selected value set to `default`.
   - If `description` is non-empty, create a `<span class="field-description">` below the input.
   - Set `data-field-key` attribute on the input for retrieval.
4. Attach `input` event listeners to all generated fields for prompt preview updates.

The form generation function is pure: given an agent's field metadata, it produces DOM elements. No field names are hardcoded.

### Prompt Preview Panel

The Prompt Preview is a collapsible section at the bottom of the Settings tab. It shows the fully rendered system prompt as read-only preformatted text.

| Element | Details |
|---------|---------|
| Container | `<div class="prompt-preview">` with a disclosure toggle |
| Content | `<pre>` element with the rendered prompt text |
| Default state | Collapsed (user opens it by clicking the header) |
| Update trigger | Any field edit, debounced at 400ms |
| Loading state | Faded text with "Rendering..." indicator while the API call is in flight |
| Error state | "Could not render prompt" message if the API call fails |

**Update flow:**

```
Field input event
  → Reset debounce timer (400ms)
  → On timer fire:
      → Collect all field values from the dynamic form
      → POST /api/agents/{selectedAgent}/render-prompt
      → On success: replace <pre> content with response text
      → On error: show error message in <pre>
```

The preview does not block any user action. It is informational only.

### Disabled State During Session

When a voice session is active (`conversationActive === true`):

- The agent selector dropdown is disabled.
- All settings fields are disabled (prevents confusion about when changes take effect).
- The Prompt Preview remains visible but stops updating (no API calls).
- A banner reads: "Settings are locked during an active session."

When the session ends, all controls are re-enabled.

---

## State Management

### Agent Metadata Cache

On page load, the frontend fetches `GET /api/agents` once and stores the response in a module-level variable:

```javascript
let agentMetadata = [];  // Populated on page load

async function loadAgentMetadata() {
  const response = await fetch("/api/agents");
  agentMetadata = await response.json();
  buildAgentSelector(agentMetadata);
  selectAgent(agentMetadata[0].name);  // or default from config
}
```

The metadata is not refetched during the session. Agents are static (defined at server startup).

### Selected Agent State

```javascript
let selectedAgentName = null;  // Currently selected agent name

function selectAgent(agentName) {
  selectedAgentName = agentName;
  const agent = agentMetadata.find(a => a.name === agentName);
  buildSettingsForm(agent.fields);
  clearPromptPreview();
}
```

### Collecting Field Values

When sending `prompt_config` or requesting a prompt render, field values are collected generically:

```javascript
function collectFieldValues() {
  const values = {};
  document.querySelectorAll("[data-field-key]").forEach(input => {
    const key = input.dataset.fieldKey;
    const value = input.tagName === "TEXTAREA" ? input.value : input.value;
    if (value.trim()) {
      values[key] = value;
    }
  });
  return values;
}
```

This replaces the current `getPromptConfig()` which references fields by hardcoded IDs.

### Updated sendPromptConfig

```javascript
function sendPromptConfig() {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    websocket.send(JSON.stringify({
      type: "prompt_config",
      variables: collectFieldValues(),
    }));
  }
}
```

### Updated WebSocket URL

The `agent` query parameter uses the selected agent name:

```javascript
function buildWebSocketUrl() {
  const provider = providerSelect.value;
  const wsProtocol = location.protocol === "https:" ? "wss:" : "ws:";
  let url = `${wsProtocol}//${location.host}/ws/${provider}/${userId}/${sessionId}`;
  url += `?agent=${encodeURIComponent(selectedAgentName)}`;
  // ... append provider-specific query params ...
  return url;
}
```

---

## CSS Additions

### Agent Selector

```css
.agent-selector {
  margin-bottom: 1.5rem;
}

.agent-selector select {
  /* Same styling as provider selector */
  width: 100%;
}

.agent-description {
  color: var(--text-secondary);
  font-size: 0.85rem;
  margin-top: 0.5rem;
  line-height: 1.4;
}
```

### Field Description (help text)

```css
.field-description {
  display: block;
  color: var(--text-secondary);
  font-size: 0.8rem;
  margin-top: 0.25rem;
}
```

### Prompt Preview

```css
.prompt-preview {
  margin-top: 1.5rem;
  border: 1px solid var(--border-color);
  border-radius: 0.5rem;
  overflow: hidden;
}

.prompt-preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: var(--input-bg);
  cursor: pointer;
  user-select: none;
}

.prompt-preview-header h3 {
  font-size: 0.9rem;
  font-weight: 600;
  margin: 0;
}

.prompt-preview-content {
  padding: 1rem;
  max-height: 300px;
  overflow-y: auto;
}

.prompt-preview-content pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: "SF Mono", "Fira Code", monospace;
  font-size: 0.8rem;
  line-height: 1.5;
  color: var(--text-primary);
  margin: 0;
}

.prompt-preview.collapsed .prompt-preview-content {
  display: none;
}

.prompt-preview.loading pre {
  opacity: 0.5;
}
```

---

## Interaction Details

### Agent Change While Disconnected

1. User selects a different agent from the dropdown.
2. Settings form rebuilds with new fields and defaults.
3. Prompt Preview clears and re-renders after debounce.
4. No WebSocket activity. The change takes effect on next "Start Conversation".

### Agent Change While Connected

The agent selector dropdown is disabled. The user cannot change agents mid-session. This is communicated via the disabled state and the "Settings are locked" banner.

### Page Load with No Agents

If `GET /api/agents` returns an empty list or fails:
- The agent selector shows "No agents available".
- The settings form is empty.
- The "Start Conversation" button is disabled.
- An error message is shown: "Could not load agent configuration."

This is an edge case (the server always registers at least one agent) but the frontend handles it gracefully.

### Prompt Preview Toggle

The Prompt Preview section header acts as a disclosure toggle (chevron icon). Clicking it expands or collapses the content. The collapsed/expanded state persists across agent switches within the same page session (not across page reloads).

The first expansion triggers the initial render request.
