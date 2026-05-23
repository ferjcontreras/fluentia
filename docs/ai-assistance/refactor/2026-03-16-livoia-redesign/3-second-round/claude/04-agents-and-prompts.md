# 4. Agents and Prompts

## The Agent Concept

An **agent** in Livoia is not a separate code path or a different application. It is a **configuration bundle** that determines how a voice session behaves. Each agent definition specifies:

1. **A prompt template**: Jinja2 template that defines the agent's personality, instructions, and behavior.
2. **Template variables**: The set of variables the prompt template accepts (with defaults), which can be customized at session start via the `prompt_config` WebSocket message.
3. **Enabled tools**: Which tools from the tool registry are available to this agent.
4. **Provider settings**: Optional per-agent overrides for provider behavior (e.g., voice ID, language).

This design means adding a new agent type (scheduler, assistant, Q&A bot) requires **zero code changes to providers, session management, or the tool framework**. It is purely:
1. Write a prompt template.
2. Define an `AgentDefinition` that references it.
3. Register it in the agent registry.

## AgentDefinition

```python
@dataclass(frozen=True)
class AgentDefinition:
    """Defines an agent's behavior through configuration, not code."""

    name: str                                   # Unique identifier (e.g., "interviewer")
    display_name: str                           # Human-readable name (e.g., "Interview Agent")
    description: str                            # What this agent does
    template_path: str                          # Relative path to Jinja2 template
    default_variables: dict[str, Any]           # Default template variables
    enabled_tools: list[str]                    # Tool names this agent can use
    provider_settings: dict[str, Any] | None    # Optional per-agent provider overrides

    def render_prompt(self, user_variables: dict[str, Any]) -> str:
        """Render the prompt template with merged variables.

        User-provided variables (from prompt_config message) override defaults.
        Unknown variables are ignored.
        """
        ...
```

## Agent Registry

```python
class AgentRegistry:
    """Registry of available agent definitions. Agents register at startup."""

    def register(self, agent: AgentDefinition) -> None:
        """Register an agent definition."""
        ...

    def get(self, name: str) -> AgentDefinition:
        """Look up an agent by name. Raises KeyError if not found."""
        ...

    def list_agents(self) -> list[AgentDefinition]:
        """Return all registered agents (for UI display)."""
        ...
```

The registry is populated at application startup in the FastAPI lifespan handler. New agents are registered by adding a module under `agents/` and registering it in the lifespan.

## Stage 1: Interviewer Agent

The interviewer is the first and currently only agent. It conducts structured interviews with customizable questions and guidelines.

### Template: `agents/templates/interviewer.j2`

```jinja2
You are {{ agent_name }}, a professional and friendly interviewer conducting a voice interview on behalf of {{ company_name }}. Your role is to ask interview questions, listen to the candidate's responses, and maintain a natural conversation flow.

INTERVIEW PROCESS:
1. Start by greeting the candidate warmly and introducing yourself.
2. Ask each question one at a time, in the order provided.
3. Listen actively to their answers and ask brief follow-up questions if the answer is unclear or incomplete.
4. Be conversational and supportive -- this is a dialogue, not an interrogation.
5. After all questions are answered, thank the candidate and conclude the interview.

QUESTIONS TO ASK (in order):
{{ questions }}

GUIDELINES:
{{ guidelines }}

Remember: This is a voice conversation, so speak naturally, use conversational language, and keep your responses concise. Do not use formatting, bullet points, or written-style language.
```

### Definition: `agents/interviewer.py`

```python
interviewer_agent = AgentDefinition(
    name="interviewer",
    display_name="Interview Agent",
    description="Conducts structured voice interviews with customizable questions.",
    template_path="agents/templates/interviewer.j2",
    default_variables={
        "agent_name": "Taylor",
        "company_name": "Avature",
        "questions": (
            'Question 1: "Tell us about the size of team you have previously '
            'supported."\n\n'
            'Question 2: "How would you rate your proficiency with Microsoft '
            'Excel on a scale from 1 to 10?"'
        ),
        "guidelines": (
            "- Ask naturally and conversationally, not robotically\n"
            "- Ask follow-up questions if the answer is unclear\n"
            "- Repeat questions if the candidate asks\n"
            "- Keep tone professional yet warm\n"
            "- Don't rush -- give the candidate time to think\n"
            "- Move to the next question only after the current one is "
            "adequately answered"
        ),
    },
    enabled_tools=["getDateAndTimeTool"],
    provider_settings=None,
)
```

### Prompt Configuration at Session Start

When a client connects, it can send a `prompt_config` message to customize the interviewer:

```json
{
    "type": "prompt_config",
    "agent_name": "Jordan",
    "company_name": "Acme Corp",
    "questions": "Question 1: Describe a challenging project...\nQuestion 2: ...",
    "guidelines": "- Focus on technical skills\n- Keep it under 20 minutes"
}
```

The session manager passes this to `AgentDefinition.render_prompt()`, which merges user-provided values with defaults. Fields not provided in the message use the default values.

## Future Agents

The agent framework is designed to support diverse use cases. Examples of future agents:

### Scheduler Agent

Helps users schedule events (interviews, meetings) by conversing naturally and using tools to check availability and create calendar entries.

```python
scheduler_agent = AgentDefinition(
    name="scheduler",
    display_name="Scheduling Assistant",
    description="Helps schedule interviews and meetings via voice conversation.",
    template_path="agents/templates/scheduler.j2",
    default_variables={
        "company_name": "Avature",
        "agent_name": "Alex",
        "timezone": "America/New_York",
    },
    enabled_tools=["getDateAndTimeTool", "checkAvailability", "createEvent"],
    provider_settings=None,
)
```

### Avature Platform Assistant

Answers questions about the Avature platform, helps navigate features, and can perform actions via the Avature API.

```python
assistant_agent = AgentDefinition(
    name="avature_assistant",
    display_name="Avature Assistant",
    description="Voice assistant for navigating and interacting with Avature.",
    template_path="agents/templates/avature_assistant.j2",
    default_variables={
        "agent_name": "Sam",
        "platform_version": "current",
    },
    enabled_tools=["searchRecords", "getRecordDetails", "webSearch"],
    provider_settings=None,
)
```

### What Doesn't Change

When adding a new agent:
- **Providers**: No changes. They receive an `AgentDefinition` via `SessionContext` and use its rendered prompt. The provider doesn't know or care whether it's conducting an interview or scheduling a meeting.
- **Session manager**: No changes. It resolves the agent from the registry and passes it to the provider.
- **Tool framework**: No changes (assuming the tools already exist). If a new tool is needed, it's added to `tools/implementations/` and registered independently.
- **Frontend**: Minimal changes. The agent selector in the UI adds an option. The prompt config form may need different fields per agent type (handled via agent metadata or a future settings schema).

### What Does Change

1. **New template file** in `agents/templates/`.
2. **New definition module** in `agents/` (a Python file with an `AgentDefinition` instance).
3. **Registration** in the application lifespan handler.
4. **New tools** if the agent needs capabilities not yet implemented.

## Prompt Rendering

### Template Engine

Jinja2 is used for prompt rendering. Templates are loaded from `agents/templates/` relative to the package root.

### Rendering Flow

```
Client sends prompt_config message
    |
    v
Session manager extracts user variables
    |
    v
AgentDefinition.render_prompt(user_variables)
    |
    v
Merge: default_variables | user_variables  (user overrides defaults)
    |
    v
Load Jinja2 template from template_path
    |
    v
Render template with merged variables
    |
    v
Return rendered prompt string
```

### Variable Validation

- Unknown variables in `prompt_config` are silently ignored (forward compatibility).
- Missing required variables fall back to `default_variables`.
- Empty strings are treated as valid values (the user may intentionally clear a default).
- The template itself should be written defensively -- use `{{ variable | default('fallback') }}` for optional variables.

## Agent Metadata for the Frontend

The agent registry exposes metadata that the frontend can use to build the UI:

```python
# GET /api/agents
[
    {
        "name": "interviewer",
        "display_name": "Interview Agent",
        "description": "Conducts structured voice interviews.",
        "config_fields": ["agent_name", "company_name", "questions", "guidelines"]
    }
]
```

The `config_fields` list tells the frontend which fields to show in the prompt configuration form. This enables the UI to dynamically render the right settings panel for each agent type without hardcoding field names.
