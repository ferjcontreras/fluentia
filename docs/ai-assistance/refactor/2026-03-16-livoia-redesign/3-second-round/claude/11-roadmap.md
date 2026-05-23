# 11. Roadmap

## Post-Launch Evolution

Each phase is independently deployable and delivers user-facing value.

---

## Phase 1: Production Parity

**Goal**: The new system does everything the PoC web demo does, in a production-grade deployment.

**Deliverables**:
- Voice conversations with Google Gemini and AWS Bedrock Nova Sonic
- Interviewer agent with customizable prompts
- Date/time tool (Bedrock only)
- Browser UI with settings panel and conversation log
- Health checks, structured logging, Docker deployment
- Full CI/CD pipeline

**Success criteria**: A user can conduct a voice interview in the browser with the same quality as the current PoC, backed by production infrastructure.

---

## Phase 2: Multi-Agent Support and Prompt Transparency

**Goal**: Users can choose between agent types and see what the agent is "thinking."

**Deliverables**:
- Agent selector in the UI (dropdown or tab)
- Dynamic settings form that adapts to the selected agent's `config_fields`
- Prompt Preview tab: read-only view of the rendered system prompt for the current session
- At least one additional agent definition beyond the interviewer (e.g., a simple Q&A assistant)
- `/api/agents` endpoint returning agent metadata for the frontend

**Architecture impact**: None. The agent framework from Phase 1 already supports this. This phase is primarily UI work and authoring new agent definitions.

**New agent example**: A general Q&A assistant that answers questions about a configurable topic. No tools needed -- just a different prompt template.

---

## Phase 3: Tool Transparency

**Goal**: Users can see tool invocations and results in real time.

**Deliverables**:
- Tool Activity tab in the UI showing live tool events
- `TOOL_STARTED`, `TOOL_PROGRESS`, `TOOL_COMPLETED`, `TOOL_FAILED` events displayed in the tab
- Tool events rendered with timestamps, tool name, inputs (sanitized), and outputs
- Tool execution duration displayed

**Architecture impact**: Minimal. The tool lifecycle events are already defined in the event protocol. This phase wires them to the frontend.

---

## Phase 4: Configurable Tools and New Capabilities

**Goal**: Users can enable/disable tools per session. New tools expand agent capabilities.

**Deliverables**:
- Tool configuration in the Settings tab: toggle individual tools on/off
- Tool catalog displayed in the UI with name, description, and status
- New built-in tools:
  - **Web search**: Search the internet for information (uses a search API)
  - **File/document search**: Search a document corpus (if applicable to the agent)
- Google ADK tool support: wire `ToolProcessor` into the Google provider
- Tool spec formatting for Google ADK's native format

**Architecture impact**: Moderate.
- The frontend needs a tool configuration UI.
- The Google provider needs tool execution support (wiring `ToolProcessor`).
- The `prompt_config` message may need to include `enabled_tools` to override agent defaults.

---

## Phase 5: External Orchestrator Integration

**Goal**: Agents can perform complex, multi-step workflows via the Avature Orchestrator.

**Deliverables**:
- `OrchestratorTool`: Async tool that calls the Avature Orchestrator API
- Progress tracking: tool emits `PROGRESS` events as the Orchestrator processes steps
- Vocal narration: provider injects system messages so the agent narrates progress ("I'm scheduling that for you now...")
- Timeout and error handling for long-running operations
- Scheduler agent: uses Orchestrator to check availability and create calendar events
- Avature Assistant agent: uses Orchestrator to search records and perform platform actions

**Architecture impact**: Moderate.
- New `OrchestratorConfig` in configuration
- New `OrchestratorTool` in `tools/implementations/`
- Async tool execution pattern (progress callbacks) exercised for the first time
- New agent definitions in `agents/`

**New dependencies**: HTTP client library for Orchestrator API calls (e.g., `httpx`).

---

## Phase 6: Advanced Voice Features

**Goal**: Enhanced voice experience with richer interaction patterns.

**Potential deliverables** (scope TBD based on provider capabilities):
- Multi-language support: agent adapts language based on user preference or detection
- Voice selection: user can choose from available voices per provider
- Conversation history: session summary generated at end of conversation
- Audio quality enhancements: noise reduction, echo cancellation (provider-side)
- Proactive agent behavior: agent initiates conversation based on context (Google native audio)

**Architecture impact**: Low to moderate. Most features are provider-specific configuration or UI enhancements.

---

## Phase Summary

| Phase | Focus | New Agents | New Tools | UI Changes |
|-------|-------|------------|-----------|------------|
| 1 | Production parity | Interviewer | Date/time | Settings + Conversation |
| 2 | Multi-agent + prompt preview | Q&A Assistant | None | Agent selector, Prompt tab |
| 3 | Tool transparency | None | None | Tool Activity tab |
| 4 | Configurable tools + Google tools | None | Web search, Document search | Tool config in Settings |
| 5 | Orchestrator integration | Scheduler, Avature Assistant | Orchestrator, availability, records | Progress indicators |
| 6 | Advanced voice | None | None | Language/voice selectors |

---

## Dependency Graph

```
Phase 1 (Production Parity)
    |
    +---> Phase 2 (Multi-Agent + Prompt Transparency)
    |         |
    |         +---> Phase 5 (Orchestrator -- needs multiple agents)
    |
    +---> Phase 3 (Tool Transparency)
    |         |
    |         +---> Phase 4 (Configurable Tools -- needs tool UI)
    |                   |
    |                   +---> Phase 5 (Orchestrator -- needs tool infra)
    |
    +---> Phase 6 (Advanced Voice -- independent of tools/agents)
```

Phase 5 (Orchestrator) depends on both Phase 2 (multi-agent) and Phase 4 (configurable tools). Phase 6 can be pursued in parallel with Phases 3-5.
