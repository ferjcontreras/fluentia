# Documentation Design

## Directory Structure

```
docs/
├── ai-assistance/                    # AI-generated development docs
│   ├── HELP.md                       # How to use this directory
│   ├── analysis/
│   │   └── HELP.md
│   ├── code-review/
│   │   └── HELP.md
│   ├── debug/
│   │   └── HELP.md
│   ├── design/
│   │   ├── HELP.md
│   │   └── 2026-03-16-prod-redesign/ # This design (copied from PoC)
│   ├── feature/
│   │   └── HELP.md
│   └── refactor/
│       └── HELP.md
├── guides/                           # Developer guides
│   ├── about-avature.md              # Domain context
│   ├── code-style-guide.md           # Coding conventions
│   ├── commit-message-guide.md       # Commit message format
│   ├── getting-started.md            # Onboarding guide (new)
│   ├── technical-writing-style-guide.md  # Documentation standards
│   └── test-development-guide.md     # Testing practices
├── references/                       # Technical reference docs
│   ├── environment-variables.md      # All env vars documented
│   └── websocket-protocol.md         # WebSocket message format spec
└── tutorials/                        # Step-by-step tutorials
    ├── running-locally.md            # Local development setup
    └── deploying-with-docker.md      # Docker deployment
```

## Documents to Copy As-Is

These documents are relevant to the new project without changes:

| Source | Destination | Reason |
|--------|------------|--------|
| `docs/guides/about-avature.md` | Same | Domain context is project-agnostic |
| `docs/guides/technical-writing-style-guide.md` | Same | Writing standards don't change |
| `docs/ai-assistance/HELP.md` | Same | AI assistance directory structure |
| `docs/ai-assistance/*/HELP.md` | Same | Subdirectory help files |
| `docs/ai-assistance/design/2026-03-16-prod-redesign/` | Same | This design documentation |

## Documents to Adapt

These documents need revision for the new project:

### `docs/guides/code-style-guide.md`

**Adaptations needed:**
- Remove references to `clients/`, `modules/`, `api/` directories
- Update import examples to use new package structure (`livoia.providers`, `livoia.tools`)
- Remove references to LangChain messages, OpenAI/Skynet clients, embedding clients
- Keep all general Python style rules (type hints, modern syntax, Pydantic usage, ABC patterns)
- Update example code snippets to reflect new architecture

**Improvements to consider:**
- Add section on async/await patterns (the project is heavily async)
- Add section on WebSocket handler patterns
- Add section on provider implementation guidelines

### `docs/guides/commit-message-guide.md`

**Adaptations needed:**
- Update valid scopes to match new architecture:
  - `app` (application factory, endpoints)
  - `providers` (provider implementations)
  - `providers/google` (Google-specific)
  - `providers/bedrock` (Bedrock-specific)
  - `tools` (tool framework)
  - `prompts` (prompt management)
  - `frontend` (static HTML/CSS/JS)
  - `docker` (Docker and deployment)
  - `ci` (CI/CD pipeline)
  - `docs` (documentation)
- Remove scopes that no longer exist: `api`, `clients`, `modules`, `utils`

### `docs/guides/test-development-guide.md`

**Adaptations needed:**
- Update file path examples to new structure
- Remove sections about LLM client mocks, embedding client mocks
- Focus on WebSocket testing patterns, provider mocking, tool testing
- Update mock builder examples for new classes

**Improvements to consider:**
- Add section on testing WebSocket endpoints with `TestClient`
- Add section on testing async generators (event streams)
- Add patterns for mocking Google ADK components
- Add patterns for mocking AWS Bedrock streaming

## New Documents

### `docs/guides/getting-started.md` (new)

Onboarding guide for new developers. Contents:

1. **What is Livoia**: Brief description of the project
2. **Prerequisites**: Python 3.13+, uv, browser with microphone
3. **Setup**: Clone, install, configure environment
4. **Running locally**: Start the server, open browser
5. **Project structure**: Overview of the package layout
6. **Key concepts**: Providers, tools, prompts, WebSocket protocol
7. **Making changes**: Development workflow (code -> check -> test -> commit)
8. **Where to learn more**: Links to other guides

### `docs/references/environment-variables.md` (new)

Complete reference for all environment variables:

1. **Application settings**: `LIVOIA_LOG_LEVEL`, etc.
2. **Google Gemini**: `GOOGLE_API_KEY`, `GOOGLE_MODEL`, etc.
3. **AWS Bedrock**: `BEDROCK_REGION`, `BEDROCK_MODEL_ID`, etc.
4. **AWS credentials**: `AWS_ACCESS_KEY_ID`, etc.
5. **Examples**: Common configurations for development and production

### `docs/references/websocket-protocol.md` (new)

Technical reference for the WebSocket protocol:

1. **Connection**: URL format, query parameters
2. **Prompt configuration**: First message format
3. **Audio streaming**: Binary frame format, sample rates
4. **Text messages**: JSON format for text and images
5. **Server events**: All event types with examples
6. **Provider differences**: What each provider supports

### `docs/tutorials/running-locally.md` (new)

Step-by-step tutorial:

1. Install prerequisites (Python, uv)
2. Clone and install
3. Obtain API keys (Google, AWS)
4. Configure environment
5. Start the server
6. Open the web UI
7. Have a conversation
8. Customize settings

### `docs/tutorials/deploying-with-docker.md` (new)

Step-by-step tutorial:

1. Build the Docker image
2. Run locally with Docker
3. Configure environment variables
4. Health check verification
5. Production considerations (Kubernetes, secrets)

## README.md

The new README should be concise and focused:

```markdown
# Livoia - Live Voice Agent

A production web application for real-time voice conversations with AI,
supporting Google Gemini and AWS Bedrock Nova Sonic.

## Quick Start

    # Install
    uv sync --group dev

    # Configure
    export GOOGLE_API_KEY="..."
    export AWS_ACCESS_KEY_ID="..."

    # Run
    uv run uvicorn livoia.app:create_app --factory --reload --port 8000

    # Open http://localhost:8000

## Documentation

- [Getting Started](docs/guides/getting-started.md)
- [Running Locally](docs/tutorials/running-locally.md)
- [Deploying with Docker](docs/tutorials/deploying-with-docker.md)
- [Environment Variables](docs/references/environment-variables.md)
- [WebSocket Protocol](docs/references/websocket-protocol.md)
- [Code Style Guide](docs/guides/code-style-guide.md)
- [Test Development Guide](docs/guides/test-development-guide.md)

## Development

    ./check_code.sh          # Run code quality checks
    uv run pytest            # Run unit tests
    uv run tox               # Run all checks + tests

## Architecture

See [Production Redesign](docs/ai-assistance/design/2026-03-16-prod-redesign/00-main.md)
for the design documentation.
```

## .claude/CLAUDE.md

A new CLAUDE.md tailored to the production project. Key differences from PoC:

- Updated project structure references
- Simplified architecture description (no 3-layer pattern)
- Updated command examples for new paths
- Provider pattern documentation
- No references to unused components (LLM clients, embedding, caching, etc.)
