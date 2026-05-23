# Remaining Phases: Orchestrator Integration and Advanced Voice

This document captures the high-level intent for the final two phases of the Fluentia roadmap. Each section includes context, open questions, and a ready-to-use prompt for creating the full design specification when the time comes.

## Prerequisites

Both phases depend on earlier work:

- **Phase 5** requires Phase 2 (multi-agent, since it introduces two new agents) and Phase 4 (configurable tools + Google tool support, since it introduces the first long-running async tool).
- **Phase 6** is independent of Phases 2-5 and can be pursued in parallel.

---

## Phase 5: External Orchestrator Integration

### Intent

Connect Fluentia to the Avature Orchestrator API so that voice agents can perform real actions in the Avature platform: check calendar availability, schedule interviews, search candidate records, update workflow steps. This is where Fluentia transitions from a demo tool to a product with operational value.

### What the Orchestrator Is

The Avature Orchestrator is an internal API that exposes platform operations as composable steps. A client sends a request describing the desired action (e.g., "find available time slots for interviewer X next week"), and the Orchestrator executes the necessary Avature platform calls, returning results or progress updates as the operation proceeds. Operations can be fast (record lookup) or slow (multi-step scheduling with conflict resolution).

### Key Deliverables

- **`OrchestratorTool`**: A new `BaseTool` implementation that calls the Orchestrator API via HTTP. Unlike existing tools (which return instantly), this tool may take seconds to complete and should emit `TOOL_PROGRESS` events as the Orchestrator reports intermediate steps.
- **`OrchestratorConfig`**: Pydantic configuration for the Orchestrator API endpoint, authentication, and timeout settings. Added to `AppConfig` with `ORCHESTRATOR_` env prefix.
- **Scheduler agent**: A new `AgentDefinition` whose prompt instructs the model to help users find available times and book meetings. Enabled tools: `getDateAndTimeTool`, `getCityTimeTool`, `orchestratorTool` (with an availability-checking action).
- **Avature Assistant agent**: A new `AgentDefinition` whose prompt instructs the model to search Avature records, answer questions about candidates or jobs, and perform basic workflow actions. Enabled tools: `orchestratorTool` (with record search and update actions).
- **Vocal narration of progress**: When a long-running tool is executing, the agent should narrate what is happening ("I'm checking the calendar now...", "I found three available slots..."). This requires injecting system-level context into the provider so the model knows a tool is in progress.
- **Timeout and error handling**: Orchestrator calls can fail or hang. The tool must have configurable timeouts and produce `TOOL_FAILED` events with actionable error messages.

### Open Questions

1. **Orchestrator API contract**: What is the exact API shape? REST? gRPC? What authentication mechanism? This needs to be defined with the Orchestrator team before spec creation.
2. **Action taxonomy**: What specific actions does the Orchestrator expose? We need a concrete list (e.g., `search_records`, `get_availability`, `create_event`, `update_workflow_step`) to design the tool's input schema.
3. **Progress protocol**: How does the Orchestrator report progress? Streaming responses? Polling? Webhooks? This affects whether `OrchestratorTool` uses SSE, long-polling, or WebSocket to the Orchestrator.
4. **Single tool vs. multiple tools**: Should there be one `OrchestratorTool` with an `action` parameter, or separate tools per action (`SearchRecordsTool`, `GetAvailabilityTool`, etc.)? A single tool is simpler to register but harder for the model to use correctly. Multiple tools give the model clearer affordances.
5. **Vocal narration mechanism**: How does the provider inject "the tool is running, please narrate" context into the model? Google ADK may handle this differently than Bedrock.
6. **Authorization**: Should the Orchestrator tool operate with a service account, or should it use the session user's identity? This affects security and audit logging.

### New Dependency

`httpx` (async HTTP client) for Orchestrator API calls. This would be Fluentia's first runtime dependency beyond the voice provider SDKs.

### Prompt for Spec Creation

```
Could you please design a specification for Phase 5 (External Orchestrator
Integration), and store it in
@docs/ai-assistance/design/YYYY-MM-DD-orchestrator-integration ?

Please analyze the problem as if you were a professional functional analyst,
working with very talented designers and user experience researchers. Please
read the @docs/ai-assistance/design/HELP.md document.

Before starting, please read:
- The Phase 5 description in the roadmap:
  @docs/ai-assistance/refactor/2026-03-16-livoia-redesign/3-second-round/claude/11-roadmap.md
- The discussion document with open questions:
  @docs/discussions/remaining-phases-5-and-6.md
- The Avature platform context: @docs/guides/about-avature.md
- The existing tool framework: @docs/reference/agent-and-tools.md
- The Phase 4 spec (configurable tools, Google ADK bridge):
  @docs/ai-assistance/design/2026-03-17-configurable-tools/

The design should cover:
1. The OrchestratorTool implementation (async HTTP calls, progress events,
   timeout handling)
2. OrchestratorConfig (Pydantic settings, env vars, authentication)
3. The Scheduler and Avature Assistant agent definitions
4. The vocal narration mechanism (how the agent narrates tool progress)
5. The prompt_config and UI changes needed for the new agents
6. Error handling and resilience patterns for external API calls

Please also address the open questions listed in the discussion document,
proposing concrete answers with trade-off analysis where the answer is not
obvious.
```

---

## Phase 6: Advanced Voice Features

### Intent

Improve the voice experience with features that make conversations feel more natural and configurable: language selection, voice selection, conversation summaries, and proactive agent behavior. These are largely provider-specific configurations and UI enhancements -- no new architectural patterns.

### Key Deliverables

- **Multi-language support**: The agent adapts its language based on a user preference (selected in Settings) or automatic detection. This primarily affects the system prompt ("Respond in Spanish") and potentially provider-specific settings (language hints for speech recognition).
- **Voice selection**: Users choose from available voices for each provider. Google and Bedrock each offer a set of named voices with different characteristics (gender, accent, tone). The UI presents a dropdown populated from provider metadata.
- **Conversation summary**: At the end of a session, the system generates a text summary of the conversation (key topics, decisions, action items). This could be a post-session API call to a text model or a provider feature.
- **Audio quality settings**: Expose provider-side audio settings (noise reduction, echo cancellation) as session configuration. These are provider-specific and may not be configurable on all providers.
- **Proactive agent behavior**: Google's native audio models support proactive responses (the agent speaks without being prompted). This is already partially implemented (the `proactivity` query parameter exists). Phase 6 would refine the UX: when should the agent be proactive, how does the UI indicate it, and how does the user control it.

### Open Questions

1. **Language support scope**: Which languages do Google Gemini and Bedrock Nova Sonic support for voice input/output? Do they support mixed-language conversations? Does the system prompt language need to match the speech language?
2. **Voice catalog**: How do we discover available voices per provider? Is there an API, or do we hardcode the known voice list? Bedrock has a `voice_id` config field already.
3. **Conversation summary timing**: Is the summary generated during the session (incremental) or after disconnect? Who generates it -- the voice model itself, a separate text model call, or the provider?
4. **Proactivity UX**: The current checkbox is binary (on/off). Should there be finer control (e.g., proactivity level, topics the agent can initiate)?
5. **Provider feature matrix**: Not all features are available on all providers. How does the UI communicate which features are provider-specific? (The Phase 4 pattern of "provider restriction" badges could extend here.)

### Prompt for Spec Creation

```
Could you please design a specification for Phase 6 (Advanced Voice
Features), and store it in
@docs/ai-assistance/design/YYYY-MM-DD-advanced-voice ?

Please analyze the problem as if you were a professional functional analyst,
working with very talented designers and user experience researchers. Please
read the @docs/ai-assistance/design/HELP.md document.

Before starting, please read:
- The Phase 6 description in the roadmap:
  @docs/ai-assistance/refactor/2026-03-16-livoia-redesign/3-second-round/claude/11-roadmap.md
- The discussion document with open questions:
  @docs/discussions/remaining-phases-5-and-6.md
- The current provider implementations:
  @src/fluentia/providers/google.py and @src/fluentia/providers/bedrock/provider.py
- The Bedrock config (already has voice_id, language fields):
  @src/fluentia/config.py
- The WebSocket protocol: @docs/reference/websocket-protocol.md

The design should cover:
1. Multi-language support (prompt adaptation, provider speech settings,
   UI language selector)
2. Voice selection (voice catalog per provider, UI dropdown, provider
   config changes)
3. Conversation summary (generation strategy, delivery mechanism, UI
   display)
4. Proactive agent behavior refinement (UX beyond the current checkbox,
   Google-specific settings)
5. Provider feature matrix (how the UI communicates per-provider
   availability)

For each feature, please assess which providers support it, what the
implementation complexity is, and whether it requires backend changes,
frontend changes, or both. Phase 6 features are independently deployable,
so the spec should make it clear which can be shipped first.
```

---

## Sequencing Notes

Phase 5 is the higher-value deliverable (it enables real Avature workflows), but it depends on Phases 2 and 4 and on the Orchestrator API being available. Phase 6 features are lower-risk and can fill time while waiting for Orchestrator API access or between Phase 5 milestones.

A practical order might be:

1. Ship a few Phase 6 features early (voice selection, language preference) as quick wins.
2. Begin Phase 5 once the Orchestrator API contract is defined.
3. Interleave remaining Phase 6 features as needed.
