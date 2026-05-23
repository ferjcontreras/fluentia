# Tools & Multi-Agent Orchestration

This system is designed from the ground up to support multiple agents (personas/use cases) and continuous conversational loops during long-running tool executions.

## Agent Profiles

An "Agent" in this architecture is not a separate application, but a configured profile containing:
1. A **System Prompt Template**.
2. A **Tool Whitelist**.

### The `AgentRegistry`

The registry defines what behavior the system exhibits based on the `{agent_profile}` path parameter in the WebSocket connection.

```python
# Pseudo-code representation
AGENT_PROFILES = {
    "interviewer": {
        "prompt_template": "templates/interviewer.j2",
        "allowed_tools": ["get_current_time"]
    },
    "scheduler": {
        "prompt_template": "templates/scheduler.j2",
        "allowed_tools": ["get_current_time", "check_calendar_availability", "create_meeting"]
    },
    "avature_assistant": {
        "prompt_template": "templates/avature_assistant.j2",
        "allowed_tools": [
             "search_candidates",
             "invoke_orchestrator_job_writer" # Long-running tool
        ]
    }
}
```
When a session starts, the `SessionOrchestrator` uses this registry to compile the final payload sent to the Provider (LLM).

## The Tool Framework

Tools inherit from a strict `BaseTool` class that enforces structured I/O and self-description.

```python
class BaseTool(abc.ABC):
    name: str
    description: str
    input_schema: dict # JSON Schema format

    @abc.abstractmethod
    async def execute(self, **kwargs) -> dict:
        pass
```

### Addressing the Async Execution Challenge

The most critical requirement for production tooling is handling **long-running external tools** (e.g., invoking the Avature Orchestrator) without blocking the live voice conversation.

If the LLM decides to format a job description via the Orchestrator, that task might take 30 seconds. The user must be able to ask, "Is it done yet?" and the LLM must be able to reply, "I'm still working on it."

#### The Execution Flow

1. **Invocation**: The Provider yields a `ToolInvocationRequest` to the `SessionOrchestrator`.
2. **Background Dispatch**: The Orchestrator does *not* `await` the tool execution in the main event loop. Instead, it fires an `asyncio.create_task(self.execute_tool(tool, args))`.
3. **Context Injection (Start)**: The Orchestrator immediately utilizes the Provider's context injection capability (e.g., sending a system message) to tell the LLM: *"System Note: Tool 'X' has started executing in the background."*
4. **UI Notification**: The Orchestrator sends a `tool_event` JSON frame to the WebSocket so the frontend can display a loading spinner in a "Tools" transparency tab.
5. **Continuous Conversation**: Because the tool is running in a background task, the loops handling audio I/O continue without interruption.
6. **Completion**: When the background task finishes, the Orchestrator sends the result back to the Provider via `send_tool_result()`. The LLM is now aware of the outcome and can naturally inform the user ("I've finished writing that job description for you!").
7. **UI Resolution**: The Orchestrator sends a `tool_event: completed` frame to the frontend to clear the spinner.

### Security and Boundaries

- **No Client Execution**: The frontend never executes tools. It only receives transparency events *about* tool execution.
- **Provider Agnosticism**: Because tool schemas are normalized via `BaseTool.input_schema`, the `ProviderAdapter` is responsible for translating that standard JSON Schema into whatever proprietary format the LLM SDK requires (e.g., Bedrock's exact `toolSpec` format).
