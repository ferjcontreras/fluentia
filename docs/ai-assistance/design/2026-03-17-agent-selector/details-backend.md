# Backend Details

## Changes Summary

| Component | Change Type | Description |
|-----------|-------------|-------------|
| `agents/base.py` | Modify | Add `FieldMetadata` dataclass and `field_metadata` to `AgentDefinition` |
| `agents/interviewer.py` | Modify | Add field metadata to existing agent |
| `agents/qa_assistant.py` | New | Q&A Assistant agent definition and template |
| `agents/templates/qa_assistant.j2` | New | Jinja2 prompt template |
| `app.py` | Modify | Enhance `/api/agents`, add `/api/agents/{name}/render-prompt`, register new agent |
| `session/manager.py` | Modify | Update `_receive_prompt_config()` for generic variables |

No changes to providers, tools, events, observability, or configuration.

---

## agents/base.py

### New: FieldMetadata

```python
@dataclass(frozen=True)
class FieldMetadata:
    """Rendering hints for a configurable agent field."""

    label: str
    field_type: str = "text"
    placeholder: str = ""
    description: str = ""
    options: list[str] | None = None
    rows: int = 6
    order: int = 0
```

`FieldMetadata` is a frozen dataclass, consistent with `AgentDefinition`. It carries only presentation hints -- no validation rules. Validation is the template's responsibility (Jinja2 handles missing variables gracefully via `jinja2.Undefined`).

### Modified: AgentDefinition

Add one field:

```python
field_metadata: dict[str, FieldMetadata] = field(default_factory=dict)
```

Add one method for API serialization:

```python
def serialize_fields(self) -> list[dict[str, Any]]:
    """Serialize field metadata for the API response, sorted by order."""
    fields: list[dict[str, Any]] = []
    for key in self.default_variables:
        meta: FieldMetadata = self.field_metadata.get(
            key,
            FieldMetadata(label=key.replace("_", " ").title()),
        )
        fields.append({
            "key": key,
            "label": meta.label,
            "field_type": meta.field_type,
            "placeholder": meta.placeholder,
            "description": meta.description,
            "default": self.default_variables[key],
            "options": meta.options,
            "rows": meta.rows,
            "order": meta.order,
        })
    fields.sort(key=lambda f: f["order"])
    return fields
```

Fields without explicit metadata get a fallback: the variable name converted to title case (e.g., `"agent_name"` becomes `"Agent Name"`). This ensures every variable in `default_variables` appears in the API response even if the agent author omits metadata.

---

## agents/qa_assistant.py

New file. Defines the Q&A Assistant agent.

```python
"""Q&A assistant agent definition."""

from fluentia.agents.base import AgentDefinition
from fluentia.agents.base import FieldMetadata

qa_assistant_agent: AgentDefinition = AgentDefinition(
    name="qa_assistant",
    display_name="Q&A Assistant",
    description="Answers questions about a configurable topic via voice conversation.",
    template_path="templates/qa_assistant.j2",
    default_variables={
        "agent_name": "Alex",
        "topic": "general knowledge",
        "guidelines": "Be concise and factual. If you are unsure about something, say so.",
    },
    field_metadata={
        "agent_name": FieldMetadata(
            label="Agent Name",
            placeholder="e.g., Alex",
            description="Name the agent uses to introduce itself.",
            order=0,
        ),
        "topic": FieldMetadata(
            label="Topic",
            placeholder="e.g., Python programming, company policy, product features",
            description="The subject area the agent specializes in.",
            order=1,
        ),
        "guidelines": FieldMetadata(
            label="Guidelines",
            field_type="textarea",
            placeholder="Behavioral instructions for the agent...",
            rows=6,
            order=2,
        ),
    },
    enabled_tools=[],
)
```

### agents/templates/qa_assistant.j2

```
You are {{ agent_name }}, a knowledgeable and helpful voice assistant specializing in {{ topic }}.

Your role is to answer questions clearly and conversationally. This is a voice conversation, so speak naturally and keep your answers concise.

GUIDELINES:
{{ guidelines }}

Remember: If a question is outside your area of expertise, acknowledge this honestly rather than guessing. Ask clarifying questions when the user's intent is ambiguous.
```

---

## app.py

### Enhanced GET /api/agents

```python
@app.get("/api/agents")
async def list_agents() -> JSONResponse:
    """Return available agent definitions with field metadata."""
    registry: AgentRegistry = app.state.agent_registry
    agents: list[dict[str, Any]] = [
        {
            "name": agent.name,
            "display_name": agent.display_name,
            "description": agent.description,
            "fields": agent.serialize_fields(),
        }
        for agent in registry.list_agents()
    ]
    return JSONResponse(content=agents)
```

The change: `config_fields` (a list of strings) is replaced by `fields` (a list of field metadata objects). This is a breaking change to the API response shape, but the endpoint is consumed only by the Fluentia frontend (no external clients).

### New: POST /api/agents/{name}/render-prompt

```python
@app.post("/api/agents/{name}/render-prompt")
async def render_prompt(name: str, body: dict[str, Any]) -> Response:
    """Render an agent's prompt template with the provided variables."""
    registry: AgentRegistry = app.state.agent_registry
    try:
        agent_def: AgentDefinition = registry.get(name)
    except KeyError:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Agent not found: {name}"},
        )

    variables: dict[str, Any] = body.get("variables", {})
    rendered: str = agent_def.render_prompt(variables)
    return Response(content=rendered, media_type="text/plain")
```

This endpoint is stateless. It does not require a WebSocket session.

### Register Q&A Assistant

In the lifespan handler:

```python
from fluentia.agents.qa_assistant import qa_assistant_agent

agent_registry.register(interviewer_agent)
agent_registry.register(qa_assistant_agent)
```

---

## session/manager.py

### Updated _receive_prompt_config

The current implementation extracts four hardcoded field names:

```python
for field_name in ("agent_name", "company_name", "questions", "guidelines"):
    value = data.get(field_name)
    ...
```

The updated implementation reads from a `variables` dictionary and accepts any string key:

```python
async def _receive_prompt_config(
    self, websocket: WebSocket, agent_def: AgentDefinition
) -> dict[str, Any]:
    """Read a prompt_config message from the WebSocket (5s timeout)."""
    try:
        raw: str = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
        data: dict[str, Any] = json.loads(raw)
        if data.get("type") != "prompt_config":
            return {}

        # Phase 2 format: generic variables dict
        variables: dict[str, Any] = data.get("variables", {})

        # Filter to keys the agent actually uses
        known_keys: set[str] = set(agent_def.config_fields)
        result: dict[str, str] = {}
        for key, value in variables.items():
            if key in known_keys and isinstance(value, str) and value.strip():
                result[key] = value

        logger.info("Received prompt_config with fields: %s", list(result.keys()))
        return result

    except (TimeoutError, json.JSONDecodeError, Exception):
        logger.debug("No prompt_config received, using defaults")
        return {}
```

Key changes:

1. The method now receives the `agent_def` parameter to know which fields are valid.
2. Variables are read from `data["variables"]` instead of top-level keys.
3. Only keys present in the agent's `config_fields` are accepted (unknown keys are silently dropped).

This requires reordering the logic in `handle_websocket()`: resolve the agent definition before calling `_receive_prompt_config()`, since the method now needs the agent's config_fields to filter variables.

Updated call order in `handle_websocket()`:

```python
# 1. Resolve provider
# 2. Resolve agent definition (moved up)
# 3. Wait for prompt_config (now receives agent_def)
# 4. Merge prompt_config variables into agent definition
# 5. Create session context and start
```

---

## Testing

### Unit Tests

| Test | Description |
|------|-------------|
| `test_field_metadata_defaults` | `FieldMetadata` uses correct defaults for all optional fields |
| `test_serialize_fields_with_metadata` | `serialize_fields()` returns correctly ordered field list |
| `test_serialize_fields_without_metadata` | Fields missing from `field_metadata` get auto-generated labels |
| `test_qa_assistant_render` | Q&A assistant template renders with default and custom variables |
| `test_list_agents_response` | `GET /api/agents` returns field metadata for all agents |
| `test_render_prompt_endpoint` | `POST /api/agents/{name}/render-prompt` returns rendered text |
| `test_render_prompt_unknown_agent` | Returns 404 for unknown agent name |
| `test_prompt_config_generic_variables` | `_receive_prompt_config` extracts from `variables` dict |
| `test_prompt_config_filters_unknown_keys` | Unknown variable keys are silently dropped |

### Integration Tests

| Test | Description |
|------|-------------|
| `test_websocket_with_qa_assistant` | Full session with Q&A assistant agent (mocked provider) |
| `test_agent_switch_between_sessions` | Two sequential sessions with different agents |

---

## Migration Notes

### API Breaking Change

The `GET /api/agents` response changes from:

```json
{ "config_fields": ["agent_name", "company_name", ...] }
```

to:

```json
{ "fields": [{ "key": "agent_name", "label": "Agent Name", ... }] }
```

Since the frontend is the only consumer and both are deployed together, this is a coordinated change with no migration period needed.

### prompt_config Protocol Change

The WebSocket `prompt_config` message changes from top-level fields to a nested `variables` object. Both frontend and backend are updated in the same deployment. No backward compatibility shim is needed.
