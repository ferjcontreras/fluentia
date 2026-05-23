# Frontend Details

## Settings Tab: Tools Section

The Settings tab gains a new "Tools" section after the dynamic configuration form (Phase 2) and before the Prompt Preview panel.

### Layout

```
Settings Tab
┌─────────────────────────────────────────────┐
│ Agent                                       │
│   [▼ Interview Agent               ]        │
│   "Conducts structured voice interviews."   │
│                                             │
│ Configuration                               │
│   Agent Name: [Taylor          ]            │
│   Company Name: [Avature       ]            │
│   ...                                       │
│                                             │
│ Tools                                       │
│   Available tools for this agent:           │
│                                             │
│   [✓] Date & Time                           │
│       Get the current date and time in UTC. │
│                                             │
│   [✓] City Time                             │
│       Get the current date and time in a    │
│       specific city.                        │
│                                             │
│   [ ] Google Search        ⓘ Google only    │
│       Search the web for information.       │
│                                             │
│ ┌─ Prompt Preview ──────────────────────┐   │
│ │ You are Taylor, a professional...     │   │
│ └───────────────────────────────────────┘   │
│                                             │
│ "Changes apply when starting a new          │
│  conversation."                             │
└─────────────────────────────────────────────┘
```

### Tool Toggle Component

Each tool is rendered as a toggle row:

```html
<div class="tool-toggle" data-tool-name="getDateAndTimeTool">
  <label class="tool-toggle-switch">
    <input type="checkbox" checked>
    <span class="toggle-slider"></span>
  </label>
  <div class="tool-toggle-info">
    <span class="tool-toggle-name">Date & Time</span>
    <span class="tool-toggle-desc">Get the current date and time in UTC.</span>
  </div>
</div>
```

For provider-restricted tools that are unavailable:

```html
<div class="tool-toggle disabled" data-tool-name="google_search">
  <label class="tool-toggle-switch">
    <input type="checkbox" disabled>
    <span class="toggle-slider"></span>
  </label>
  <div class="tool-toggle-info">
    <span class="tool-toggle-name">Google Search</span>
    <span class="tool-toggle-badge">Google only</span>
    <span class="tool-toggle-desc">Search the web for information.</span>
  </div>
</div>
```

### Dynamic Generation

Tools are built from the cached `/api/agents` response, same pattern as the dynamic settings form:

```javascript
function buildToolToggles(agent, currentProvider) {
  const container = document.getElementById("toolTogglesContainer");
  container.innerHTML = "";

  if (!agent.tools || agent.tools.length === 0) {
    container.innerHTML = '<p class="tools-empty">No tools available for this agent.</p>';
    return;
  }

  for (const tool of agent.tools) {
    const isRestricted = tool.provider_restriction
      && tool.provider_restriction !== currentProvider;

    const row = document.createElement("div");
    row.className = "tool-toggle" + (isRestricted ? " disabled" : "");
    row.dataset.toolName = tool.name;

    const label = document.createElement("label");
    label.className = "tool-toggle-switch";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = tool.enabled_by_default && !isRestricted;
    checkbox.disabled = isRestricted;
    checkbox.dataset.toolName = tool.name;

    const slider = document.createElement("span");
    slider.className = "toggle-slider";

    label.appendChild(checkbox);
    label.appendChild(slider);

    const info = document.createElement("div");
    info.className = "tool-toggle-info";

    const nameSpan = document.createElement("span");
    nameSpan.className = "tool-toggle-name";
    nameSpan.textContent = tool.display_name;

    info.appendChild(nameSpan);

    if (tool.provider_restriction) {
      const badge = document.createElement("span");
      badge.className = "tool-toggle-badge";
      badge.textContent = tool.provider_restriction.charAt(0).toUpperCase()
        + tool.provider_restriction.slice(1) + " only";
      info.appendChild(badge);
    }

    const desc = document.createElement("span");
    desc.className = "tool-toggle-desc";
    desc.textContent = tool.description;
    info.appendChild(desc);

    row.appendChild(label);
    row.appendChild(info);
    container.appendChild(row);
  }
}
```

### Collecting Enabled Tools

```javascript
function collectEnabledTools() {
  const enabled = [];
  document.querySelectorAll('.tool-toggle-switch input[type="checkbox"]').forEach(cb => {
    if (cb.checked && !cb.disabled) {
      enabled.push(cb.dataset.toolName);
    }
  });
  return enabled;
}
```

### Updated sendPromptConfig

```javascript
function sendPromptConfig() {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    websocket.send(JSON.stringify({
      type: "prompt_config",
      variables: collectFieldValues(),
      enabled_tools: collectEnabledTools(),
    }));
  }
}
```

### Provider Switch Behavior

When the user changes the provider dropdown:

1. Rebuild tool toggles with the new provider context.
2. Provider-restricted tools for the old provider become disabled.
3. Provider-restricted tools for the new provider become enabled (if they were enabled by default).
4. Non-restricted tools retain their current toggle state.

```javascript
providerSelect.addEventListener("change", () => {
  const agent = agentMetadata.find(a => a.name === selectedAgentName);
  if (agent) {
    // Preserve current toggle states for non-restricted tools
    const currentStates = {};
    document.querySelectorAll('.tool-toggle-switch input').forEach(cb => {
      if (!cb.disabled) {
        currentStates[cb.dataset.toolName] = cb.checked;
      }
    });

    buildToolToggles(agent, providerSelect.value);

    // Restore preserved states
    for (const [name, checked] of Object.entries(currentStates)) {
      const cb = document.querySelector(`input[data-tool-name="${name}"]`);
      if (cb && !cb.disabled) {
        cb.checked = checked;
      }
    }
  }
  // ... existing provider switch logic
});
```

### Disabled State During Session

When a session is active, all tool toggles are disabled (same as agent selector and settings fields). A visual indicator confirms the lock.

---

## CSS

### Tool Toggle Styles

```css
.tools-section {
  margin-top: 1.5rem;
}

.tools-section h2 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.tools-section-desc {
  color: var(--text-secondary);
  font-size: 0.85rem;
  margin-bottom: 1rem;
}

.tool-toggle {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 0.5rem;
  margin-bottom: 0.5rem;
  transition: opacity 0.2s;
}

.tool-toggle.disabled {
  opacity: 0.5;
}

.tool-toggle-info {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  flex: 1;
}

.tool-toggle-name {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--text-primary);
}

.tool-toggle-desc {
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

.tool-toggle-badge {
  display: inline-block;
  font-size: 0.7rem;
  padding: 0.125rem 0.5rem;
  border-radius: 1rem;
  background: rgba(0, 84, 185, 0.1);
  color: var(--avature-blue);
  font-weight: 500;
  width: fit-content;
}

.tools-empty {
  color: var(--text-secondary);
  font-size: 0.85rem;
  font-style: italic;
  padding: 0.5rem 0;
}
```

### Toggle Switch (iOS-style)

```css
.tool-toggle-switch {
  position: relative;
  display: inline-block;
  width: 2.5rem;
  height: 1.375rem;
  flex-shrink: 0;
  margin-top: 0.125rem;
}

.tool-toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--border-color);
  border-radius: 1rem;
  transition: background-color 0.2s;
}

.toggle-slider::before {
  content: "";
  position: absolute;
  height: 1rem;
  width: 1rem;
  left: 0.1875rem;
  bottom: 0.1875rem;
  background-color: white;
  border-radius: 50%;
  transition: transform 0.2s;
}

.tool-toggle-switch input:checked + .toggle-slider {
  background-color: var(--avature-blue);
}

.tool-toggle-switch input:checked + .toggle-slider::before {
  transform: translateX(1.125rem);
}

.tool-toggle-switch input:disabled + .toggle-slider {
  cursor: not-allowed;
  opacity: 0.5;
}
```

---

## Agent Switch Behavior

When the user selects a different agent, the tool toggles rebuild from scratch using the new agent's `tools` array. Toggle states from the previous agent are discarded (they may not apply -- different agents have different tool sets).
