# Detailed Design: Component Specifications

## Data Model

### Field Metadata

Each configurable field in an agent definition carries rendering metadata.

```python
@dataclass(frozen=True)
class FieldMetadata:
    """Rendering hints for a single configurable field."""

    label: str                          # Human-readable label (e.g., "Company Name")
    field_type: str = "text"            # Input type: "text", "textarea", "select"
    placeholder: str = ""               # Placeholder text for the input
    description: str = ""               # Help text shown below the field
    options: list[str] | None = None    # Choices for "select" type fields
    rows: int = 6                       # Number of rows for "textarea" fields
    order: int = 0                      # Display order (lower = earlier)
```

### Extended AgentDefinition

The existing `AgentDefinition` gains one new field:

```python
@dataclass(frozen=True)
class AgentDefinition:
    name: str
    display_name: str
    description: str
    template_path: str
    default_variables: dict[str, Any] = field(default_factory=dict)
    enabled_tools: list[str] = field(default_factory=list)
    provider_settings: dict[str, Any] | None = field(default=None)
    field_metadata: dict[str, FieldMetadata] = field(default_factory=dict)  # NEW
```

`field_metadata` maps variable names (keys in `default_variables`) to their `FieldMetadata`. Fields not present in `field_metadata` are rendered as plain text inputs using the variable name as the label.

### Example: Interviewer Agent

```python
interviewer_agent = AgentDefinition(
    name="interviewer",
    display_name="Interview Agent",
    description="Conducts structured voice interviews with customizable questions.",
    template_path="templates/interviewer.j2",
    default_variables={
        "agent_name": "Taylor",
        "company_name": "Avature",
        "questions": "...",
        "guidelines": "...",
    },
    field_metadata={
        "agent_name": FieldMetadata(
            label="Agent Name",
            placeholder="e.g., Taylor",
            description="Name the agent uses to introduce itself.",
            order=0,
        ),
        "company_name": FieldMetadata(
            label="Company Name",
            placeholder="e.g., Avature",
            description="Company mentioned during the interview.",
            order=1,
        ),
        "questions": FieldMetadata(
            label="Interview Questions",
            field_type="textarea",
            placeholder="Questions to ask the candidate...",
            rows=8,
            order=2,
        ),
        "guidelines": FieldMetadata(
            label="Guidelines",
            field_type="textarea",
            placeholder="Behavioral instructions for the agent...",
            rows=8,
            order=3,
        ),
    },
    enabled_tools=["getDateAndTimeTool"],
)
```

### Example: Q&A Assistant Agent

```python
qa_assistant_agent = AgentDefinition(
    name="qa_assistant",
    display_name="Q&A Assistant",
    description="Answers questions about a configurable topic.",
    template_path="templates/qa_assistant.j2",
    default_variables={
        "agent_name": "Alex",
        "topic": "general knowledge",
        "guidelines": "Be concise and factual. If unsure, say so.",
    },
    field_metadata={
        "agent_name": FieldMetadata(
            label="Agent Name",
            placeholder="e.g., Alex",
            order=0,
        ),
        "topic": FieldMetadata(
            label="Topic",
            placeholder="e.g., Python programming, company policy",
            description="The subject area the agent specializes in.",
            order=1,
        ),
        "guidelines": FieldMetadata(
            label="Guidelines",
            field_type="textarea",
            placeholder="Behavioral instructions...",
            rows=6,
            order=2,
        ),
    },
    enabled_tools=[],
)
```

---

## API Contracts

### GET /api/agents (enhanced)

Returns the list of registered agents with full field metadata.

**Response:**

```json
[
  {
    "name": "interviewer",
    "display_name": "Interview Agent",
    "description": "Conducts structured voice interviews with customizable questions.",
    "fields": [
      {
        "key": "agent_name",
        "label": "Agent Name",
        "field_type": "text",
        "placeholder": "e.g., Taylor",
        "description": "Name the agent uses to introduce itself.",
        "default": "Taylor",
        "options": null,
        "rows": 6,
        "order": 0
      },
      {
        "key": "company_name",
        "label": "Company Name",
        "field_type": "text",
        "placeholder": "e.g., Avature",
        "description": "Company mentioned during the interview.",
        "default": "Avature",
        "options": null,
        "rows": 6,
        "order": 1
      },
      {
        "key": "questions",
        "label": "Interview Questions",
        "field_type": "textarea",
        "placeholder": "Questions to ask the candidate...",
        "description": "",
        "default": "Question 1: ...",
        "options": null,
        "rows": 8,
        "order": 2
      },
      {
        "key": "guidelines",
        "label": "Guidelines",
        "field_type": "textarea",
        "placeholder": "Behavioral instructions for the agent...",
        "description": "",
        "default": "- Ask naturally and conversationally...",
        "options": null,
        "rows": 8,
        "order": 3
      }
    ]
  },
  {
    "name": "qa_assistant",
    "display_name": "Q&A Assistant",
    "description": "Answers questions about a configurable topic.",
    "fields": [
      {
        "key": "agent_name",
        "label": "Agent Name",
        "field_type": "text",
        "placeholder": "e.g., Alex",
        "description": "",
        "default": "Alex",
        "options": null,
        "rows": 6,
        "order": 0
      },
      {
        "key": "topic",
        "label": "Topic",
        "field_type": "text",
        "placeholder": "e.g., Python programming, company policy",
        "description": "The subject area the agent specializes in.",
        "default": "general knowledge",
        "options": null,
        "rows": 6,
        "order": 1
      },
      {
        "key": "guidelines",
        "label": "Guidelines",
        "field_type": "textarea",
        "placeholder": "Behavioral instructions...",
        "description": "",
        "default": "Be concise and factual. If unsure, say so.",
        "options": null,
        "rows": 6,
        "order": 2
      }
    ]
  }
]
```

Fields are returned sorted by `order`.

### POST /api/agents/{name}/render-prompt

Renders the agent's Jinja2 template with the provided variables and returns the full system prompt as plain text.

**Request:**

```json
{
  "variables": {
    "agent_name": "Taylor",
    "company_name": "Acme Corp",
    "questions": "Tell me about yourself.",
    "guidelines": "Be concise."
  }
}
```

**Response (200):**

```
Content-Type: text/plain

You are Taylor, a professional and friendly interviewer conducting a voice
interview on behalf of Acme Corp. Your role is to ask interview questions,
listen to the candidate's responses, and maintain a natural conversation flow.

INTERVIEW PROCESS:
...
```

**Error responses:**

| Status | Condition |
|--------|-----------|
| 404 | Agent name not found in registry |
| 422 | Invalid request body |

### WebSocket prompt_config (updated)

The `prompt_config` message changes from hardcoded fields to a generic `variables` dictionary:

**Before (Phase 1):**

```json
{
  "type": "prompt_config",
  "agent_name": "Taylor",
  "company_name": "Avature",
  "questions": "...",
  "guidelines": "..."
}
```

**After (Phase 2):**

```json
{
  "type": "prompt_config",
  "variables": {
    "agent_name": "Taylor",
    "company_name": "Avature",
    "questions": "...",
    "guidelines": "..."
  }
}
```

The `SessionManager._receive_prompt_config()` method is updated to extract from `variables` and filter to keys present in the agent's `config_fields`. Unknown keys are silently dropped.

---

## Component Interaction

### Page Load Sequence

```
Browser                           Server
  |                                 |
  |  GET /api/agents                |
  |-------------------------------->|
  |                                 |
  |  [{name, display_name,         |
  |    description, fields}, ...]   |
  |<--------------------------------|
  |                                 |
  |  Build agent selector           |
  |  Build settings form for        |
  |    default agent                |
  |  (no WebSocket yet)             |
```

### Agent Selection

```
User selects "Q&A Assistant"
  |
  |  Frontend finds agent metadata in cached /api/agents response
  |  Frontend rebuilds settings form from agent.fields
  |  Frontend populates field defaults
  |  Frontend clears Prompt Preview (if visible)
```

### Prompt Preview Update

```
User edits a settings field
  |
  |  Debounce 400ms
  |
  |  POST /api/agents/qa_assistant/render-prompt
  |    { "variables": { "agent_name": "Alex", "topic": "Python", ... } }
  |
  |  Server renders Jinja2 template
  |
  |  Response: rendered prompt text
  |
  |  Frontend displays in Prompt Preview panel
```

### Session Start

```
User clicks "Start Conversation"
  |
  |  WebSocket connect: /ws/google/user-123/session-abc?agent=qa_assistant
  |
  |  Send prompt_config:
  |    { "type": "prompt_config", "variables": { "agent_name": "Alex", ... } }
  |
  |  Disable agent selector and settings form
  |
  |  (session proceeds as before)
```

### Session End

```
Session ends (user disconnects or server closes)
  |
  |  Re-enable agent selector and settings form
```
