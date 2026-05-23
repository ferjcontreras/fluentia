# Architecture Specification

## Project Identity
- **Repository Name**: `livoia-core` (or similar)
- **Primary Goal**: A production-ready, highly extensible platform for bidirectional conversational voice agents.

## Core Architectural Philosophy: Pragmatic Domain-Driven Design
The system will be structured to clearly separate concerns without introducing prohibitive boilerplate. It avoids over-abstraction while strictly decoupling the network transport (WebSockets) from the external LLM integrations (Providers), using a central Orchestration layer to manage state and tool execution.

Crucially, **the architecture must treat multi-agent and complex tool orchestration as a first-class citizen from day one**. Initial scope may emphasize the "Interviewer" agent, but the engine must effortlessly support "Scheduler", "Avature Assistant", and other future agents without refactoring.

## High-Level Repository Layout

```text
src/livoia/
├── app/                  # Transport & Entrypoints
│   ├── main.py           # FastAPI application factory
│   ├── api.py            # HTTP and unified WebSocket endpoints
│   └── dependencies.py   # Dependency injection container
├── core/                 # Business Logic & Orchestration
│   ├── session.py        # Central WebSocket lifecycle & event normalizer
│   ├── agent_registry.py # Defines and registers agent personas (Interviewer, Scheduler, etc.)
│   ├── prompt.py         # Prompt template rendering engine
│   └── tools/            # Tool definitions and execution framework
│       ├── base.py
│       ├── local/        # e.g., DateTime, Simple Search
│       └── async_bridge/ # e.g., Orchestrator integrations
├── providers/            # External LLM / Speech SDK Integrations
│   ├── base.py           # Provider Adapter ABC
│   ├── google/           # Google ADK specific implementations
│   └── bedrock/          # AWS Bedrock specific implementations
└── config/               # Configuration and Environment validation
    └── settings.py       # Pydantic BaseSettings
```

## Foundational Components

### 1. The Transport Layer (`app/`)
- Purely responsible for parsing incoming HTTP/WebSocket connections.
- Exposes a unified WebSocket endpoint: `/ws/{provider}/{agent_type}/{user_id}/{session_id}`.
- *Why*: Injecting `agent_type` (e.g., `interviewer`, `scheduler`) directly into the route allows the Orchestrator to instantly load the correct system prompt and toolset profile before the connection is fully initialized.

### 2. The Orchestration Layer (`core/`)
- **`SessionOrchestrator`**: The heart of the system. It receives raw audio/text from the Transport layer and passes it to the Provider. It receives normalized events back from the Provider and dispatches them to the user.
- **`AgentRegistry`**: A new concept introduced to support multiple use cases. Instead of hardcoding prompts, the registry maps an `agent_type` to a specific system prompt template and a specific whitelist of enabled tools.
- **Asynchronous Tool Execution**: The Orchestrator manages the event loop for tools. When a Provider indicates the LLM wants to use a tool, the Orchestrator executes it. If the tool is a long-running external agent (via the company Orchestrator), it runs in the background. The Orchestrator injects system messages into the LLM context ("Tool started...", "Tool finished with result X") while keeping the live voice connection open so the LLM can speak to the user *during* execution.

### 3. The Provider Adapters (`providers/`)
- Completely decoupled from FastAPI and WebSockets.
- Implement a strict `BaseProvider` interface with methods like `send_audio`, `send_text`, and an asynchronous event generator `receive_events()`.
- Providers translate SDK-specific events (like Bedrock's `Chunk` or Google's `LiveRequest`) into the system's internal unified event vocabulary (`AudioOutput`, `TextOutput`, `ToolInvocationRequest`).

## CI/CD and Infrastructure

- **Multi-Stage Docker**: A highly optimized `uv`-based multi-stage Dockerfile that drops compiler toolchains in the final runtime image, resulting in a minimal, secure container.
- **Strict Environment Validation**: Uses `pydantic-settings`. No fallback to `.env` files in production. Secrets like Google API keys must be injected via Kubernetes Secrets. AWS permissions are derived ambiently from K8s Service Accounts.
- **Testing**: Layers of testing (`unit` for purely isolated logic, `integration` for Provider SDK validation using mocked network responses, and `e2e` for the full WebSocket flow).

## Key Advantages over the PoC

1. **Multi-Agent Readiness:** By abstracting the "Interviewer" logic out of the core app into an `AgentRegistry`, adding a new "Scheduler" agent is simply a matter of registering a new prompt and tool list.
2. **True Modularity:** You can test the Google Provider without spinning up a FastAPI server, and test the WebSocket logic using a Mock Provider.
3. **Enterprise Robustness:** Hardened containerization and strict CI/CD quality gates guarantee stability at scale.
