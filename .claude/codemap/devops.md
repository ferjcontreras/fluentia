# Configuration, CI/CD & DevOps

## Overview

Project tooling, dependency management, code quality enforcement, CI/CD pipeline, and containerization. Uses `uv` for packages, `ruff` + `mypy` + `pylint` for code quality, `tox` for test orchestration, GitHub Actions for automation, and Docker for deployment.

---

## Package Management (uv)

**When to look here**: Adding/removing dependencies, understanding the dependency tree, or the private PyPI index.

- **Config**: `pyproject.toml` (root, ~284 lines)
  - Core dependencies: 48 packages (AI/ML, web framework, observability, data)
  - Dev dependencies: 16 packages (testing, linting, type checking)
  - No private PyPI index (public packages only)
- **Lock file**: `uv.lock`
- **Commands**: `uv sync`, `uv sync --group dev`, `uv run <command>`

---

## Code Quality Tools

**When to look here**: Linter errors, formatter issues, type checking failures, or configuring quality thresholds.

### Quick Check Script
**File**: `check_code.sh` (root)
- Runs all 4 checks with colored pass/fail output
- Usage: `./check_code.sh`

### Ruff (Linter + Formatter)
- **Config**: `pyproject.toml` [tool.ruff] section
- Line length: 100, Target: Python 3.13
- Enabled rule sets: E, W, F, I, N, UP, D, S, B, T20, ARG, RUF
- Force single-line imports, Google-style docstrings
- Per-file ignores for tests, configs, and reference code
- Commands: `uv run ruff format .`, `uv run ruff check --fix .`

### MyPy (Type Checker)
- **Config**: `pyproject.toml` [tool.mypy] section
- Strict mode enabled, Python 3.13 target
- Pydantic mypy plugin for BaseModel support
- Module-specific overrides for cache_store and tests
- Command: `uv run mypy src/fluentia tests`

### Pylint (Code Quality)
- **Config**: `pyproject.toml` [tool.pylint] section
- Minimum score: 9.9/10 (fail-under)
- Max locals: 16 per function, max attributes: 10 per class
- Command: `uv run pylint src/fluentia`

---

## Pre-commit Hooks

**When to look here**: Hook failures on commit, adding new hooks, or understanding what runs before each commit.

**File**: `.pre-commit-config.yaml`

Stages: `commit-msg`, `pre-commit`

1. **File hygiene** (pre-commit-hooks): trailing whitespace, EOF, large files, merge conflicts, AST, JSON/TOML/YAML validation, debug statements, private keys
2. **Python checks** (pygrep-hooks): mock method validation, type annotation enforcement
3. **Ruff**: Linting + formatting with auto-fix
4. **Commitizen**: Conventional Commits validation (commit-msg stage)

---

## Tox (Test Orchestration)

**When to look here**: Running the full test suite, understanding test environments, or CI test configuration.

**File**: `tox.ini`

| Environment | What it runs |
|-------------|-------------|
| `py313` | Unit tests with coverage (excludes manual/integration/e2e) |
| `lint` | ruff check, ruff format, pylint |
| `typecheck` | mypy |

Coverage reports: terminal (missing lines), XML (CI), HTML (`coverage/html/`)

---

## GitHub Actions CI Pipeline

**When to look here**: CI failures, pipeline configuration, build process, or deployment setup.

**File**: `.github/workflows/ci.yml`

| Stage | Job | Trigger | What it does |
|-------|-----|---------|-------------|
| quality | `lint` | .py or config changes | `tox -e lint` |
| quality | `typecheck` | .py or config changes | `tox -e typecheck` |
| tests | `tests` | .py or config changes | `tox` (all checks + tests), produces coverage |
| build | docker build | Git tags only | Builds and pushes image |

**Note**: CI pipeline not yet configured (local development only)

---

## Docker

**When to look here**: Container build issues, deployment configuration, health checks, or the production runtime environment.

### Dockerfile (root)
- Multi-stage build: Builder (gcc, git, pip install) -> Production (slim, non-root user)
- Non-root user: `fluentia` (UID 1000)
- Default CMD: `uvicorn fluentia_web.app:create_app --factory --host 0.0.0.0 --port 8000`
- Health check: 240s interval, 3s timeout

### Docker Scripts (`docker/`)
- `entrypoint.sh`: Container initialization, executes passed command
- `healthcheck.sh`: Curls `/health` endpoint, configurable via env vars

### Environment Variables for Docker
- `FLUENTIA_API__HOST`, `FLUENTIA_API__PORT`, `HEALTH_ENDPOINT`
- `PYTHONUNBUFFERED=1`, `PYTHONDONTWRITEBYTECODE=1`

---

## Environment Configuration

**File**: `.env.example` (template), `.env` (active, with placeholders)

Key variables:
- `OPENAI_API_KEY`: OpenAI API access
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`: AWS credentials
- `GOOGLE_API_KEY`, `GOOGLE_CLOUD_PROJECT`: Google Cloud/Gemini access
- `FLUENTIA_*`: Application-specific configuration (see API section)
