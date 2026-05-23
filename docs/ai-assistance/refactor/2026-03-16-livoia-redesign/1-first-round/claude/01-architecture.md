# Architecture Design

## Project Name

**livoia** (same name, new repository)

## Repository Layout

```
livoia/
├── .claude/
│   ├── CLAUDE.md                     # AI assistant instructions
│   ├── CODEMAP.md                    # Navigation map (L0)
│   └── codemap/                      # L1 navigation files
├── docs/
│   ├── ai-assistance/                # AI-generated design/analysis docs
│   │   ├── analysis/
│   │   ├── code-review/
│   │   ├── debug/
│   │   ├── design/
│   │   ├── feature/
│   │   └── refactor/
│   ├── guides/                       # Developer guides
│   │   ├── about-avature.md          # Domain context (copied)
│   │   ├── code-style-guide.md       # Adapted for new project
│   │   ├── commit-message-guide.md   # Adapted for new project
│   │   ├── test-development-guide.md # Adapted for new project
│   │   ├── technical-writing-style-guide.md  # Copied
│   │   └── getting-started.md        # New: onboarding guide
│   ├── references/                   # API and protocol reference docs
│   │   ├── websocket-protocol.md     # WebSocket message format spec
│   │   └── environment-variables.md  # All env vars documented
│   └── tutorials/                    # Step-by-step tutorials
│       ├── running-locally.md        # Local development setup
│       └── deploying-with-docker.md  # Docker deployment
├── docker/
│   ├── entrypoint.sh                # Container entrypoint
│   └── healthcheck.sh               # Health check script
├── src/
│   └── livoia/                       # Single top-level package
│       ├── __init__.py
│       ├── app.py                    # FastAPI application factory
│       ├── config.py                 # Application configuration (Pydantic BaseSettings)
│       ├── providers/                # Voice conversation providers
│       │   ├── __init__.py
│       │   ├── base.py              # Provider ABC
│       │   ├── google.py            # Google Gemini provider
│       │   └── bedrock/             # AWS Bedrock provider (multi-file, complex)
│       │       ├── __init__.py
│       │       ├── provider.py      # BedrockProvider (WebSocket adapter)
│       │       ├── client.py        # Nova Sonic streaming client
│       │       └── config.py        # Bedrock-specific configuration
│       ├── prompts/                  # Prompt management
│       │   ├── __init__.py
│       │   └── interview.py         # Interview prompt renderer
│       ├── tools/                    # Tool framework
│       │   ├── __init__.py
│       │   ├── base.py              # BaseTool ABC
│       │   ├── processor.py         # ToolProcessor
│       │   └── builtin/             # Built-in tool implementations
│       │       ├── __init__.py
│       │       └── date_time.py     # Date/time tool
│       └── static/                   # Frontend assets
│           ├── index.html
│           ├── css/
│           │   └── style.css
│           └── js/
│               ├── app.js
│               ├── audio-player.js
│               ├── audio-recorder.js
│               ├── pcm-player-processor.js
│               └── pcm-recorder-processor.js
├── tests/
│   ├── conftest.py
│   ├── unit/                         # Unit tests (mocked dependencies)
│   │   ├── providers/
│   │   │   ├── test_google.py
│   │   │   └── bedrock/
│   │   │       ├── test_provider.py
│   │   │       └── test_client.py
│   │   ├── prompts/
│   │   │   └── test_interview.py
│   │   ├── tools/
│   │   │   ├── test_processor.py
│   │   │   └── builtin/
│   │   │       └── test_date_time.py
│   │   ├── test_app.py
│   │   └── test_config.py
│   ├── integration/                  # Integration tests (real services)
│   │   └── providers/
│   │       ├── test_google.py
│   │       └── test_bedrock.py
│   └── e2e/                          # End-to-end tests
│       └── test_websocket.py
├── .env.example
├── .gitignore
├── .gitlab-ci.yml
├── .pre-commit-config.yaml
├── check_code.sh
├── Dockerfile
├── .dockerignore
├── pyproject.toml
├── tox.ini
└── README.md
```

## Key Architectural Decisions

### 1. Single Package (`src/livoia/`)

The PoC has three packages (`livoia`, `livoia_google`, `livoia_web`). The new project consolidates into a single `livoia` package because:

- All three are always deployed together
- The separation was an artifact of incremental PoC development
- A single package simplifies imports, testing, and packaging
- Google-specific code goes into `livoia.providers.google`
- Web app code is at the package root (`livoia.app`)

### 2. Provider Abstraction

Instead of the PoC's ad-hoc approach (Google handled inline in `app.py`, Bedrock via adapter), we introduce a **Provider ABC**:

```python
class BaseProvider(abc.ABC):
    """Base class for voice conversation providers."""

    @abc.abstractmethod
    async def handle_session(
        self, websocket: WebSocket, user_id: str, session_id: str, system_prompt: str
    ) -> None:
        """Handle a complete WebSocket session."""
        raise NotImplementedError
```

Each provider encapsulates its own:
- WebSocket message handling (upstream and downstream)
- Connection lifecycle
- Provider-specific features (proactivity, affective dialog, etc.)

This makes adding new providers straightforward and keeps `app.py` clean.

### 3. Flat Module Structure (No Deep Nesting)

The PoC has a 3-layer architecture (clients -> modules -> API) designed for a general-purpose ML library. The web demo only uses the speech path, so the new project flattens this:

- **No separate "clients" and "modules" layers**: The Bedrock provider directly contains its client logic
- **No "agent" layer**: The VoiceAgent orchestrator was for CLI demos; WebSocket handlers serve that role now
- **No "audio" package**: PyAudio was for local I/O; the browser handles audio

### 4. Prompts as a First-Class Module

Prompts are currently string templates in `prompts.py`. The new design makes `livoia.prompts` a dedicated module to support:

- Multiple prompt types (interview, general assistant, etc.)
- Template rendering with user-provided variables
- Future: Jinja2 templates for complex prompts
- Future: Prompt preview tab in the UI

### 5. Tools as an Extensible Framework

The tool framework is carried forward almost unchanged because it's well-designed:

- `BaseTool` ABC with `name`, `description`, `input_schema`, `execute`
- `ToolProcessor` for registration and dispatch
- `builtin/` directory for shipped tools
- Future: User-configurable tool activation via UI

### 6. Static Files Inside Package

Static frontend files live inside `src/livoia/static/` (not a separate directory). This ensures they're included in the wheel and accessible at runtime without path gymnastics.

## Dependency Flow

```
                    ┌─────────────┐
                    │   app.py    │   FastAPI application factory
                    │  (config)   │   WebSocket endpoints, static files
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
     ┌────────────┐ ┌───────────┐ ┌──────────┐
     │  providers/ │ │  prompts/ │ │  tools/  │
     │  google.py  │ │           │ │          │
     │  bedrock/   │ │           │ │          │
     └────────────┘ └───────────┘ └──────────┘
              │
              │ (Bedrock only)
              ▼
     ┌────────────────┐
     │ bedrock/client  │   Nova Sonic streaming
     └────────────────┘
```

- `app.py` depends on `providers`, `prompts`, and `config`
- `providers.bedrock` depends on `tools` (for tool execution during conversation)
- `providers.google` depends on `google-adk` (external)
- `prompts` is independent
- `tools` is independent

## Package Dependencies

### Runtime (production)
```
# Core
fastapi
uvicorn
pydantic
pydantic-settings

# Google Gemini
google-adk

# AWS Bedrock
aws-sdk-bedrock-runtime
smithy-aws-core

# Utilities (minimal)
# (No redis, no langchain, no openai, no numpy, no prometheus, etc.)
```

### Development
```
# Testing
pytest
pytest-asyncio
pytest-cov
pytest-mock
tox
tox-uv

# Code quality
ruff
mypy
pylint
pre-commit
commitizen

# Test utilities
factory-boy
faker
```

This is a significant reduction from the PoC's dependency list. We drop: `langchain-core`, `openai`, `numpy`, `redis`, `prometheus-client`, `prometheus-fastapi-instrumentator`, `slowapi`, `pyaudio`, `httpx`, `logstash-formatter`, `hyplex`, `PyYAML`, `aiobotocore`, `jinja2`, `python-dotenv`, `pytz`.

## Design Principles

1. **No unused code**: Every module must be reachable from `app.py`
2. **Provider isolation**: Provider-specific code lives entirely within its provider module
3. **Configuration via environment variables**: All secrets and settings via env vars (Kubernetes-friendly)
4. **Extensibility over generality**: Design for known future needs (tools, new tabs), not hypothetical ones
5. **Test coverage from day one**: Every module has corresponding unit tests
