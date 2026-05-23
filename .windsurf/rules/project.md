---
trigger: always
---

# Live Voice Agent PoC — Project Rules

This file provides guidance to Windsurf (Cascade) when working with code in this repository.

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
uv run pytest                                    # Unit tests only (default)
uv run pytest -m integration                     # Integration tests
uv run pytest -m e2e                             # End-to-end tests
uv run pytest tests/unit/clients/llm/            # Specific directory
uv run pytest tests/unit/clients/llm/test_openai.py  # Single file
uv run pytest tests/unit/clients/llm/test_openai.py::test_function_name  # Single test
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
uv run uvicorn fluentia.api.app:create_app --factory --reload
```

## Documentation Guides

The `docs/guides/` directory contains critical reference documentation:

### `docs/guides/code-style-guide.md`
Comprehensive coding conventions enforced in this repository. **Consult this when writing or modifying code.** Covers:
- Python 3.13 syntax requirements (PEP 604 unions, built-in generics)
- Type hint requirements (all variables must be typed)
- Import organization (one per line, sorted alphabetically)
- Pydantic usage for configuration and data models
- ABC patterns for interfaces
- Naming conventions and docstring style
- Line length (100 characters) and formatting rules

### `docs/guides/commit-message-guide.md`
Conventional Commits specification for this repository. **Consult this when creating commits.** Covers:
- Commit message format: `<type>[scope]: <description>`
- Valid commit types (`feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `chore`, `build`, `ci`)
- Scopes for different parts of the codebase (`api`, `clients`, `modules`, `utils`, etc.)
- Breaking change notation
- Issue references

### `docs/guides/test-development-guide.md`
Comprehensive testing practices and patterns for this repository. **Consult this when writing or modifying tests.** Covers:
- Test organization (unit, integration, e2e)
- Four-layer unit test approach (configuration, methods, helpers, behavior)
- Mock patterns for async operations and external services
- Integration test patterns with real APIs
- Fixtures and configuration best practices
- Test markers (`@pytest.mark.integration`, `@pytest.mark.manual`, `@pytest.mark.real_env`)
- Arrange-Act-Assert pattern and assertion strategies
- Common anti-patterns to avoid
- The guide includes extensive code examples showing exactly how to structure tests

### `docs/guides/about-english-teacher.md`
Context about the english-teacher SaaS platform and business domain. **Consult this when working on features related to english-teacher integration.** Covers:
- english-teacher's core data model (records: person, company, object)
- Workflows and automation
- Portals and portal applications
- Search capabilities (Advanced Search, WebSources)
- Communication methods (email, SMS, WhatsApp)
- Additional solutions (DNA, Learning, Calendar, Video)
- This provides essential domain knowledge for understanding how this ML infrastructure will be used

## Architecture Overview

### Three-Layer Pattern

The codebase follows a strict three-layer architecture:

1. **Clients** (`src/fluentia/clients/`): Direct integrations with external services (OpenAI, AWS Bedrock, Skynet)
2. **Modules** (`src/fluentia/modules/`): Business logic layer that wraps clients with caching, templating, and unified interfaces
3. **API** (`src/fluentia/api/`): FastAPI application exposing HTTP endpoints

Additionally, the project includes two supplementary packages:
- **fluentia_google** (`src/fluentia_google/`): Google ADK voice agent integration
- **fluentia_web** (`src/fluentia_web/`): FastAPI web application with WebSocket endpoints for browser-based voice demos (Google ADK + Bedrock)

**Key principle**: Always use Modules in application code, never Clients directly. Modules provide caching, consistent error handling, and abstraction over provider differences.

### Key Components

- **VoiceAgent** (`src/fluentia/agent/voice_agent.py`): High-level API for voice conversations. Orchestrates AudioStreamer, SpeechCaller, and tools. Handles barge-in detection.
- **SpeechCaller** (`src/fluentia/modules/speech_caller.py`): Module for bidirectional speech streaming with tool support via ToolProcessor.
- **BedrockSonicClient** (`src/fluentia/clients/speech/`): Low-level client for Amazon Nova Sonic bidirectional streaming.
- **AudioStreamer** (`src/fluentia/audio/streamer.py`): PyAudio-based microphone input and speaker output handling.
- **ToolProcessor** (`src/fluentia/tools/processor.py`): Registration and execution of tools available to the voice model.
- **BaseTool** (`src/fluentia/tools/base.py`): Abstract base class for implementing tools (name, description, input_schema, execute).

### Provider Abstraction Pattern

Both LLM and Embedding services use a discriminated union pattern for multi-provider support:

```python
# Configuration uses Pydantic discriminated unions
ProviderConfig = Annotated[
    BedrockLLMProviderConfig | OpenAILLMProviderConfig | SkynetLLMProviderConfig,
    Field(discriminator="provider")
]

# Modules automatically instantiate the correct client
llm_caller = LLMCaller(config)  # config.provider determines which client
```

**Supported providers**:
- **OpenAI**: Standard OpenAI API
- **Bedrock**: AWS Bedrock (Meta Llama, Anthropic Claude, Nova Sonic)
- **Skynet**: Internal english-teacher service (uses OpenAI-compatible API)
- **Google**: Google ADK / Gemini (via fluentia_google package)

### Caching Architecture

Modules implement two-tier caching via the `Module` base class:

- **File-based** (`cache_type="file"`): JSON files in `.cache/`, good for development
- **Redis** (`cache_type="redis"`): Production caching with TTL support

Cache keys are SHA-256 hashes of inputs. The base Module class handles all caching logic; subclasses only implement `_get_cache_file_name()`.

### Message Format Normalization

LLMCaller normalizes LangChain message types to provider-specific formats:

- **OpenAI/Skynet**: `{"role": "user|assistant|developer", "content": "string"}`
- **Bedrock**: `{"role": "user|assistant", "content": [{"text": "string"}]}`

This abstraction allows application code to use LangChain messages regardless of provider.

### Demo Scripts

| Script | Description |
|--------|-------------|
| `scripts/voice_agent.py` | General-purpose voice assistant with tool support |
| `scripts/voice_interview_agent_demo.py` | Interview conductor that asks questions from a file |
| `scripts/voice_agent_manual.py` | Manual lower-level voice agent demo |
| `scripts/voice_agent_legacy.py` | Legacy voice agent implementation |
| `scripts/voice_agent_reference.py` | AWS reference implementation (unmodified) |

## Code Style Requirements

This project enforces strict Python 3.13+ style conventions:

### Type Hints
**All variables must have type hints**, including local variables:
```python
# ✅ Correct
def process_data(items: list[str]) -> dict[str, int]:
    result: dict[str, int] = {}
    count: int = 0
    for item in items:
        processed: str = item.strip()
        result[processed] = count
        count += 1
    return result

# ❌ Wrong - missing variable type hints
def process_data(items):
    result = {}
    count = 0
    ...
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
All client interfaces use `abc.ABC` with `@abc.abstractmethod`. When implementing, raise `NotImplementedError` with a descriptive message:
```python
@abc.abstractmethod
async def fetch(self, url: str) -> dict[str, Any]:
    """Fetch data from URL."""
    raise NotImplementedError("Subclasses must implement `fetch()`")
```

### Logging
Use structured logging with appropriate levels:
```python
import logging

logger: logging.Logger = logging.getLogger(__name__)
```

### Line Length and Formatting
- Maximum line length: 100 characters
- Use `ruff format` for consistent formatting
- Google-style docstrings (Args, Returns, Raises sections)

## Testing Patterns

**IMPORTANT**: See `docs/guides/test-development-guide.md` for comprehensive testing guidance, including:
- Four-layer unit test approach (configuration, methods, helpers, behavior)
- Mock patterns for async operations
- Integration test patterns with parametrization
- E2E test patterns for FastAPI applications
- Extensive code examples and anti-patterns to avoid

### Quick Reference

**Test Organization**:
- `tests/unit/`: Fast tests with mocked dependencies
- `tests/integration/`: Tests with real external services (marked `@pytest.mark.integration`, `@pytest.mark.manual`, `@pytest.mark.real_env`)
- `tests/e2e/`: End-to-end workflow tests (marked `@pytest.mark.e2e`, `@pytest.mark.manual`)

**Fixtures**:
- Global fixtures in `tests/conftest.py`
- Mock builders in `tests/fixtures/builders.py` provide fluent interfaces:
  ```python
  mock_client = LLMClientMockBuilder().with_response("test").build()
  ```

**Environment Mocking**:
- `@pytest.fixture(autouse=True)` in `conftest.py` automatically mocks `load_env()`
- Mark tests with `@pytest.mark.real_env` to use real environment variables

## Commit Convention

Follow Conventional Commits strictly (see `docs/guides/commit-message-guide.md` for full specification):

```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

**Common types**: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `chore`, `build`, `ci`

Examples:
- `feat(api): add resume parsing endpoint`
- `fix(clients): handle timeout in LLM requests`
- `refactor(modules): extract cache logic to base class`

## Project Context

**Live Voice Agent PoC** is a Machine Learning infrastructure project for english-teacher's development. It provides:
- Real-time voice agents using Amazon Nova Sonic and Google Gemini
- Unified interfaces for LLM and embedding services across multiple providers (OpenAI, AWS Bedrock, Skynet)
- Bidirectional audio streaming with tool execution support
- Web-based demo UI via FastAPI + WebSockets

Key domain knowledge:
- **english-teacher** is an enterprise SaaS platform for English language learning (see `docs/guides/about-english-teacher.md`)
- **Skynet** is english-teacher's internal ML service platform that provides OpenAI-compatible APIs

## Module-Specific Notes

### LLMCaller
Three primary operations:
- `generate_text()`: Standard chat completion
- `generate_structured_output()`: Structured parsing with Pydantic models
- `make_decision()`: Choose from explicit options

System prompts use Jinja2 templates loaded from `resources/`.

### EncoderCaller
Three encoding methods with semantic differences:
- `encode_texts()`: General-purpose text encoding
- `encode_queries()`: Optimized for search queries
- `encode_documents()`: Optimized for document corpus

Some providers (e.g., Cohere via Bedrock) use different embeddings for queries vs documents.

### SpeechCaller
Bidirectional speech streaming module:
- `connect()`: Initialize stream with system prompt and tool specs
- `send_audio()`: Stream audio bytes to model
- `receive_events()`: Async iterator yielding AudioOutput, TextOutput, ContentEnd events
- Automatic tool execution via ToolProcessor when model requests tool use

### BedrockLLMClient
**Important**: Not all Bedrock models support tool use (required for `parse()` and `decide()`). Models in `MODELS_NOT_SUPPORTING_TOOL_USE` will raise errors for these operations.

Use Meta Llama 3.3 70B or Anthropic Claude for structured outputs on Bedrock.
