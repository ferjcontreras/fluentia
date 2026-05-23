# Iterative Redesign: Requirements and Architecture

## 1. Context and Goals

The goal of this redesign is to take the successful "Live Voice Agent" PoC and structure it into a robust, production-ready repository. The new repository will serve as the foundation for our live bidirectional conversational AI platform, initially supporting the same Web Demo functionality (audio streaming with LLMs like Google ADK and Amazon Bedrock), but heavily structured to support significant future extensibility.

### 1.1 Current Baseline (To be ported)
- Real-time bidirectional voice conversations.
- Web-based frontend showcasing the demo.
- FastAPI backend bridging WebSockets (frontend) with downstream providers (Google ADK, Bedrock Nova Sonic).
- Core abstractions (`Clients`, `Modules`, `Agent` layers) from the `src/livoia` structure.

### 1.2 Future Requirements (To be designed for)
- **Advanced Configuration Engine:** The user interface will feature a "Settings" tab allowing dynamic modification of variables injected into the system prompt.
- **Dynamic Tool Registry:** The UI will feature a "Tools" tab where users can toggle which tools the agent has access to (e.g., "Web Search", "File Search").
- **Orchestrator Integration (Multi-Agent Tooling):** The agent will need the ability to invoke external agents via the company's Orchestrator system as "tools" (e.g., invoking a "Job Description Writer" agent).
- **Asynchronous Tool Execution with Continuous Voice:** When a long-running tool is invoked (like the Orchestrator), the Livoia agent must remain responsive and continue the live bidirectional conversation with the user without blocking audio I/O.
- **Transparency UI:** A "Prompt" tab showing the live rendered prompt, and a "Tool Use" tab showing active/completed tool invocations.

## 2. Infrastructure and CI/CD

The new repository will inherit the mature Python tooling from the PoC, with explicit targets for Dockerization and Kubernetes deployment.

### 2.1 Python Environment & Quality
- **Package Manager:** `uv`
- **Linting & Formatting:** `ruff`
- **Type Checking:** `mypy` (strict mode)
- **Code Quality Analysis:** `pylint`
- **Pre-commit:** Git hooks managed via `pre-commit`
- **Test Runner:** `pytest` orchestrated by `tox`

### 2.2 Containerization (Docker & Kubernetes)
Since the production application will be deployed via Kubernetes:
- **Stateless Design:** The FastAPI server must be stateless. State (like active session audio buffers) should only live for the duration of the WebSocket connection.
- **Secret Management:** Hardcoded secrets or `.env` file dependencies will be completely removed. Credentials like Google and Orchestrator tokens will be injected dynamically via Kubernetes secrets as environment variables (`os.environ`). AWS credentials will be resolved automatically via the standard AWS credential pipeline (e.g., IAM Roles for Service Accounts in Kubernetes), meaning they don't need to be explicitly configured in the app unless overriding for local development.
- **Dockerfile:** A multi-stage Docker build optimized for production (using `uv` to install production-only dependencies).

### 2.3 CI/CD (`.github/workflows/ci.yml`)
The CI pipeline will retain the following vital stages:
- **Quality:** Linters (`ruff`), Typecheck (`mypy`).
- **Tests:** Unit and Integration tests with coverage reports (`pytest`, `cobertura` format).
- **Dependency Analysis:** Custom company dependency scanner.
- **Build:** Docker build and push to AWS ECR (using Jenkins IAM role).

## 3. Core Architecture Design

The core `src/` directory will be unified and cleaned up. Instead of splitting `livoia`, `livoia_google`, and `livoia_web` into sibling paths, the application will follow a domain-driven layout better suited for a deployed service.

```text
src/
├── app/                      # FastAPI Web Application (formerly livoia_web)
│   ├── main.py               # App entrypoint
│   ├── api/                  # API routers and WebSocket endpoints
│   ├── static/               # Frontend assets
│   └── dependencies.py       # Dependency injection (configs, services)
│
├── core/                     # Core Business Logic (formerly livoia/modules & agent)
│   ├── agent.py              # High-level orchestrator
│   ├── session.py            # Conversation session management
│   ├── prompt_engine.py      # Dynamic prompt rendering (Settings Tab support)
│   └── tools/                # Tool Registry
│       ├── base.py
│       ├── local_tools.py    # e.g., DateTime, Search
│       └── orchestrator.py   # Async adapter for external Orchestrator agents
│
└── providers/                # External Integrations (formerly livoia/clients & livoia_google)
    ├── bedrock/
    │   └── sonic_client.py
    └── google/
        └── adk_client.py
```

### 3.1 Addressing the Asynchronous Orchestrator Challenge
To support the requirement where Livoia must talk to the user *while* a tool (like the Orchestrator) is running:
1. Tool execution must be completely detached from the main WebSocket/Audio event loop.
2. Tools will yield intermediate states (e.g., `STARTED`, `PROGRESS`, `COMPLETED`).
3. The Agent will inject "system messages" into the live LLM context window natively, notifying the LLM that "The Orchestrator has started working on the job description," allowing the LLM to vocally tell the user "I've started that for you right now."
4. A separate Server-Sent Events (SSE) or WebSocket channel will bridge the tool's progress directly to the Frontend's "Tool Use" tab.
