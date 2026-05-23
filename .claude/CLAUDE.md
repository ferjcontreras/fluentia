# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Navigating the Codebase

**Before exploring code for any task, start by reading `.claude/CODEMAP.md`**. It provides a hierarchical navigation map that helps you find the right area of the codebase efficiently:

1. Read `CODEMAP.md` (Level 0) to identify which area is relevant to your task.
2. Read the linked Level 1 file in `.claude/codemap/` for component-level detail with file:line references.
3. Read the actual source code at the referenced locations.

This avoids broad codebase searches and gets you to the right file quickly.

**Maintenance**: When you make structural changes (new files, renamed classes, moved modules), update the relevant codemap files as part of your work. See the "Keeping This Map Current" section at the bottom of `CODEMAP.md`.

## Essential Commands

### Development Setup
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies (creates .venv automatically)
uv sync --group dev

# Install pre-commit hooks
uv run pre-commit install
```

**Note**: This project uses `uv` for dependency management. All commands should be prefixed with `uv run` to ensure they run in the correct environment:
```bash
uv run pytest
uv run ruff format .
```

### Code Quality

**IMPORTANT**: After making any code changes, always run:
```bash
./check_code.sh
```

This script runs all four required quality checks (ruff format, ruff check, mypy, pylint) and will show clear pass/fail indicators for each.

Individual tools (if needed):
```bash
uv run ruff format .              # Auto-format code
uv run ruff check --fix .         # Lint and auto-fix
uv run mypy src/fluentia tests      # Type checking
uv run pylint src/fluentia          # Code quality analysis (must score ≥9.9/10)
```

### Testing
```bash
# Run all tests via tox
uv run tox

# Run specific test environments
uv run tox -e py313       # Unit tests only
uv run tox -e lint        # Linters only
uv run tox -e typecheck   # Type checking only

# Run tests directly with pytest (faster for iterative development)
uv run pytest                                              # Unit tests only (default)
uv run pytest -m integration                               # Integration tests
uv run pytest -m e2e                                       # End-to-end tests
uv run pytest tests/unit/providers/bedrock/                # Specific directory
uv run pytest tests/unit/providers/bedrock/test_client.py  # Single file
uv run pytest tests/unit/test_app.py::TestHealthEndpoint   # Single test class
```

### Before Committing

**REQUIRED**: Before creating any git commit, you must run:
```bash
uv run tox
```

This runs all linters, type checkers, and tests to ensure code quality. All checks must pass before committing.

**Pre-commit hooks**: This project uses pre-commit hooks for automatic validation. Install them with:
```bash
uv run pre-commit install
```

### Development Workflow Summary

1. Make code changes
2. Run `./check_code.sh` to verify quality (ruff, mypy, pylint)
3. Run tests with `uv run pytest`
4. Before committing: Run `uv run tox` (all checks + all tests)
5. Create commit following Conventional Commits format

### Running the API
```bash
# Development mode
uv run python -m fluentia.main

# Or with uvicorn directly
uv run uvicorn fluentia.app:create_app --factory --reload --host 0.0.0.0 --port 8000
```

## Documentation

### Guides (`docs/guides/`)

- **`code-style-guide.md`**: Python 3.13+ coding conventions. **Consult when writing or modifying code.** Covers type hints, imports, Pydantic usage, ABC patterns, naming conventions.
- **`commit-message-guide.md`**: Conventional Commits specification. **Consult when creating commits.** Format: `<type>[scope]: <description>`. Scopes: `api`, `providers`, `session`, `agents`, `tools`, `observability`, `config`.
- **`test-development-guide.md`**: Testing practices and patterns. **Consult when writing or modifying tests.** Four-layer unit test approach, mock patterns, fixtures, markers.
- **`technical-writing-style-guide.md`**: Documentation standards. Precision over persuasion, direct language, no superlatives.

### Reference (`docs/reference/`)

- **`websocket-protocol.md`**: WebSocket connection, session lifecycle, all 13 event types with JSON examples, audio format.
- **`provider-architecture.md`**: Provider abstraction (`BaseProvider`, `SessionContext`), Google and Bedrock implementation details, how to add a new provider.
- **`agent-and-tools.md`**: Agent definitions, prompt rendering, tool framework (`BaseTool`, `ToolProcessor`), how to create new agents and tools.

### Tutorials (`docs/tutorials/`)

- **`voice-interview-agent-web-demo.md`**: Running the web UI with Google Gemini or AWS Bedrock.
- **`docker-local-deployment.md`**: Building and running with Docker Compose.
- **`voice-interview-agent-cli-demo.md`**: Legacy CLI script (PoC-era, uses scripts/).

## Architecture Overview

### Domain-Based Package Structure

```
src/fluentia/
├── app.py              # FastAPI factory, WebSocket endpoint, static files
├── config.py           # Pydantic BaseSettings (AppConfig, GoogleProviderConfig, BedrockProviderConfig)
├── main.py             # CLI entry point
├── agents/             # Agent definitions with Jinja2 prompt templates
├── session/            # WebSocket session management and event protocol
├── providers/          # Voice provider implementations (Google ADK, Bedrock Nova Sonic)
├── tools/              # Tool framework (BaseTool ABC, ToolProcessor, implementations)
├── observability/      # Structured logging, health checks, metrics
└── static/             # Frontend SPA (HTML/CSS/JS)
```

### Key Patterns

**Provider Abstraction**: All voice providers implement `BaseProvider.handle_session()`. The `SessionManager` resolves the provider by name and delegates the WebSocket connection. Providers emit normalized `SessionEvent` objects via a callback.

**Agents as Configuration**: `AgentDefinition` is a frozen dataclass combining a Jinja2 prompt template with metadata (name, enabled tools, default variables). The same agent definition works with any provider.

**Normalized Event Protocol**: All server-to-client messages use versioned JSON with `SessionEventType` (13 types: audio, text, transcriptions, session control, tool lifecycle, errors). See `docs/reference/websocket-protocol.md`.

**Tool Framework**: `BaseTool` ABC with `name`, `description`, `input_schema`, and `execute()`. `ToolProcessor` handles registration and dispatch. Tools return `ToolResult` with `COMPLETED` or `FAILED` state.

**Pydantic Configuration**: `AppConfig` uses `BaseSettings` with environment variable support. Nested configs: `GoogleProviderConfig` (prefix `GOOGLE_`), `BedrockProviderConfig` (prefix `BEDROCK_`).

**Structured Logging**: `structlog` with JSON output, context variables for correlation (session_id, user_id, provider, agent), sensitive value masking.

### Supported Providers

- **Google Gemini**: Uses Google ADK for bidirectional audio streaming. Supports native audio models with optional proactivity and affective dialog.
- **AWS Bedrock Nova Sonic**: Uses HTTP/2 bidirectional streaming via AWS SDK. Supports tool execution during voice conversations.

## Code Style Requirements

This project enforces strict Python 3.13+ style conventions:

### Type Hints
**All variables must have type hints**, including local variables:
```python
# Correct
def process_data(items: list[str]) -> dict[str, int]:
    result: dict[str, int] = {}
    count: int = 0
    for item in items:
        processed: str = item.strip()
        result[processed] = count
        count += 1
    return result
```

### Modern Syntax
- Use PEP 604 unions: `str | None` (not `Optional[str]`)
- Use built-in generics: `list[str]`, `dict[str, Any]` (not `List[str]`, `Dict[str, Any]`)
- Exception: Import `Any` and `ClassVar` from `typing`
- One import per line (configured in pyproject.toml)

### Configuration
- **Always use Pydantic models** for configuration (never dataclasses)
- Use `Field()` with validation and descriptions
- Use `BaseSettings` for environment variable support

### Abstract Base Classes
Provider and tool interfaces use `abc.ABC` with `@abc.abstractmethod`:
```python
@abc.abstractmethod
async def handle_session(self, websocket: WebSocket, session_context: SessionContext) -> None:
    """Run a complete voice session."""
    raise NotImplementedError("Subclasses must implement `handle_session()`")
```

## Testing Patterns

**IMPORTANT**: See `docs/guides/test-development-guide.md` for full guidance.

### Quick Reference

**Test Organization**:
- `tests/unit/`: Fast tests with mocked dependencies (agents, config, observability, providers, session, tools)
- `tests/integration/`: Tests with real external services (marked `@pytest.mark.integration`)
- `tests/e2e/`: End-to-end workflow tests (marked `@pytest.mark.e2e`)

**Fixtures** (in `tests/conftest.py`):
- `mock_env`: Auto-use fixture that clears provider credentials
- `google_config`: Default `GoogleProviderConfig`
- `bedrock_config`: Default `BedrockProviderConfig`
- `app_config`: Default `AppConfig`

**Environment Mocking**:
- `@pytest.fixture(autouse=True)` in `conftest.py` clears sensitive env vars
- Mark tests with `@pytest.mark.real_env` to use real environment variables

## Commit Convention

Follow Conventional Commits strictly (see `docs/guides/commit-message-guide.md`):

```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

**Common types**: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `chore`, `build`, `ci`

**Scopes**: `api`, `providers`, `session`, `agents`, `tools`, `observability`, `config`, `docker`

Examples:
- `feat(agents): add customer support agent definition`
- `fix(providers): handle WebSocket disconnect in Bedrock provider`
- `test(session): add unit tests for prompt config parsing`

## Project Context

**Fluentia** is a real-time bidirectional voice agent platform used as the backend for the English Teacher assistant app. It provides a unified interface for voice conversations across multiple AI providers (Google Gemini, AWS Bedrock Nova Sonic).

Key domain knowledge:
- The primary use case is voice-based English practice with real-time corrections, guided topics, and CEFR level adaptation
- The only registered agent is `english_teacher` (see `src/fluentia/agents/english_teacher.py`)
