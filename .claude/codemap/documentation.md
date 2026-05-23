# Documentation & Guides

## Overview

The repository contains comprehensive developer documentation covering coding conventions, testing practices, commit standards, domain knowledge, and tutorials. These are the authoritative references for how code should be written, tested, and documented.

---

## Development Standards

### Code Style Guide
**File**: `docs/guides/code-style-guide.md` (~481 lines)

**When to read**: Before writing or modifying any Python code. Covers all enforced conventions.

Key topics:
- Python 3.13 syntax: PEP 604 unions (`str | None`), built-in generics (`list[str]`)
- Type hints on ALL variables (including locals)
- Import organization: one per line, three groups (stdlib, third-party, local), alphabetical
- Pydantic over dataclasses for all configuration
- ABC patterns with `@abc.abstractmethod`
- Composition over inheritance
- Google-style docstrings on all classes and public methods
- 100 character line length
- Error handling: specific exceptions, graceful degradation

### Commit Message Guide
**File**: `docs/guides/commit-message-guide.md`

**When to read**: Before creating any git commit.

Key topics:
- Format: `<type>[scope]: <description>`
- Types: feat, fix, refactor, perf, style, test, build, ci, chore, docs
- Scopes: api, clients, modules, utils, tests, ci, docker
- Description rules: imperative mood, lowercase, no period, max 50 chars
- Body: explain what and why, wrap at 72 chars
- Footers: BREAKING CHANGE, issue references

### Test Development Guide
**File**: `docs/guides/test-development-guide.md` (~1044 lines)

**When to read**: Before writing or modifying any test code. The most detailed guide in the repo.

Key topics:
- Test organization: unit (fast, mocked), integration (real services), e2e (workflows)
- Four-layer unit test approach: configuration, methods, helpers, behavior
- Mock patterns: AsyncMock, MagicMock, aiobotocore session mocking
- Async testing with `@pytest.mark.asyncio`
- Fluent mock builders (LLMClientMockBuilder, etc.)
- Test markers and execution modes
- Arrange-Act-Assert pattern
- Anti-patterns to avoid: testing implementation details, over-mocking, test interdependence

### Technical Writing Style Guide
**File**: `docs/guides/technical-writing-style-guide.md`

**When to read**: Before writing documentation, issue descriptions, or code comments.

Key topics:
- Precision over persuasion, no superlatives
- Words to avoid: state-of-the-art, cutting-edge, revolutionary, sophisticated, powerful
- Engineering tone: factual, objective, professional
- Document-specific guidance: commits, issues, README, code comments

---

---

## Tutorials

### Voice Interview Agent CLI Demo
**File**: `docs/tutorials/voice-interview-agent-cli-demo.md`

**When to read**: Running the command-line voice agent demo.

Covers: AWS credential setup, running `scripts/voice_interview_agent_demo.py`, command-line options, troubleshooting.

### Voice Interview Agent Web Demo
**File**: `docs/tutorials/voice-interview-agent-web-demo.md`

**When to read**: Running the browser-based voice agent demo.

Covers: Provider configuration (Google/Bedrock), server startup, using the web interface, audio/text modes.

---

## AI Assistance Documentation

**Directory**: `docs/ai-assistance/`

Documentation for AI-assisted development workflows (primarily Windsurf):
- `HELP.md`: Overview and main guide
- `analysis/`: Investigation and exploration documents
  - `google-adk-integration-analysis.md`: Google ADK integration analysis
- `code-review/HELP.md`: Code review patterns
- `debug/HELP.md`: Debugging processes
- `design/HELP.md`: Architecture decisions
- `feature/HELP.md`: Feature development tracking
- `refactor/`: Refactoring plans
  - `2026-02-google-alternative/`: Google alternative implementation (README, plan, progress)

---

## Project README

**File**: `README.md` (root)

High-level project overview: architecture, components, prerequisites, installation, quick start, project structure.
