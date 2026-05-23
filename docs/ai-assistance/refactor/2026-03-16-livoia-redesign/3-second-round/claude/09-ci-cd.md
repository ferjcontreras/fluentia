# 9. CI/CD and Docker

## Quality Tooling

### Code Quality Stack

| Tool | Purpose | Configuration |
|------|---------|--------------|
| **Ruff** | Linting + formatting | 100-char line length, Python 3.13 target, one import per line |
| **MyPy** | Type checking | Strict mode, Pydantic plugin, Python 3.13 |
| **Pylint** | Code quality analysis | Minimum score 9.9/10 |
| **pytest** | Test runner | Async support via `pytest-asyncio`, coverage via `pytest-cov` |
| **tox** | Test orchestration | Environments: `py313`, `lint`, `typecheck` |
| **pre-commit** | Git hook runner | Enforced on every commit |
| **commitizen** | Commit message validation | Conventional Commits format |

### Local Quality Check Script

A `check_code.sh` script runs all quality checks with colored pass/fail output:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== Ruff Format ==="
uv run ruff format --check . && echo "PASS" || echo "FAIL"

echo "=== Ruff Check ==="
uv run ruff check . && echo "PASS" || echo "FAIL"

echo "=== MyPy ==="
uv run mypy src/livoia tests && echo "PASS" || echo "FAIL"

echo "=== Pylint ==="
uv run pylint src/livoia && echo "PASS" || echo "FAIL"
```

### Pre-Commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-ast
      - id: check-merge-conflict
      - id: check-json
      - id: check-yaml
      - id: check-toml

  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/commitizen-tools/commitizen
    hooks:
      - id: commitizen
```

### Commit Message Format

Conventional Commits, enforced by commitizen:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `chore`, `build`, `ci`

**Scopes**: `providers`, `session`, `agents`, `tools`, `config`, `api`, `frontend`, `observability`

Jira ticket numbers in scope are optional (not enforced).

---

## CI Pipeline (GitLab CI)

### Stages

```yaml
stages:
  - quality
  - tests
  - dependency-analysis
  - build
```

### Stage: Quality

Runs on every push that changes `.py`, `pyproject.toml`, or `tox.ini` files.

```yaml
lint:
  stage: quality
  image: python:3.13-slim
  script:
    - pip install uv
    - uv sync --group dev
    - uv run ruff check .
    - uv run ruff format --check .
    - uv run pylint src/livoia
  rules:
    - changes: ["**/*.py", "pyproject.toml", "tox.ini"]

typecheck:
  stage: quality
  image: python:3.13-slim
  script:
    - pip install uv
    - uv sync --group dev
    - uv run mypy src/livoia tests
  rules:
    - changes: ["**/*.py", "pyproject.toml", "tox.ini"]
```

### Stage: Tests

Runs full tox suite. Produces Cobertura coverage report for GitLab's native coverage visualization.

```yaml
tests:
  stage: tests
  image: python:3.13-slim
  script:
    - pip install uv
    - uv sync --group dev
    - uv run tox
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
  rules:
    - changes: ["**/*.py", "pyproject.toml", "tox.ini"]
```

### Stage: Dependency Analysis

Manual trigger. Uses the internal dependency analysis tool.

```yaml
dependency-analysis:
  stage: dependency-analysis
  image: registry.xcade.net/python-dependency-analysis:latest
  script:
    - analyze
  when: manual
```

### Stage: Build

Triggered only on Git tags (e.g., `v1.0.0`). Builds Docker image and pushes to AWS ECR.

```yaml
build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - apk add --no-cache aws-cli
    - aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REGISTRY
    - docker build -t $ECR_REGISTRY/livoia:$CI_COMMIT_TAG .
    - docker push $ECR_REGISTRY/livoia:$CI_COMMIT_TAG
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/
  variables:
    ECR_REGISTRY: 381491985459.dkr.ecr.us-east-1.amazonaws.com
```

### Security Practices

- **Least-privilege CI credentials**: ECR push permissions only, no admin access.
- **Short-lived tokens**: AWS credentials via STS assume-role, not long-lived keys.
- **Immutable tags**: Docker images tagged with the Git tag. No `:latest` tag in production.
- **No secrets in CI config**: Secrets stored in GitLab CI variables (masked).

---

## Docker

### Dockerfile

Multi-stage build for minimal image size:

```dockerfile
# --- Builder stage ---
FROM python:3.13-slim AS builder

WORKDIR /build

# Install build dependencies
RUN pip install --no-cache-dir uv

# Copy dependency files first (layer caching)
COPY pyproject.toml uv.lock ./

# Install production dependencies only
RUN uv sync --no-dev --frozen

# Copy source code
COPY src/ src/

# Build wheel
RUN uv build --wheel


# --- Production stage ---
FROM python:3.13-slim AS production

# Create non-root user
RUN groupadd -r livoia && useradd -r -g livoia -d /app livoia

WORKDIR /app

# Install wheel from builder
COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

# Copy static files (if not included in wheel via package_data)
# COPY --from=builder /build/src/livoia/static/ /app/static/

# Switch to non-root user
USER livoia

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Expose port
EXPOSE 8000

# Run with single uvicorn worker (WebSocket sessions are stateful)
CMD ["uvicorn", "livoia.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

### Design Decisions

**Single uvicorn worker**: WebSocket connections are long-lived and stateful. Multiple workers within a single container require sticky session routing at the process level, adding complexity without benefit. Horizontal scaling is handled by Kubernetes replicas.

**No `portaudio19-dev`**: The PoC required PortAudio for CLI-based microphone access (PyAudio). The production system uses browser-based audio via Web Audio API. No system audio libraries needed.

**Non-root user**: The container runs as `livoia` (non-root) for security. No elevated privileges needed.

**No `.env` file copied**: Secrets are injected by Kubernetes as environment variables. The Docker image contains zero credentials.

**No `gunicorn`**: For a WebSocket-heavy application with a single worker, gunicorn's process management adds overhead without value. Uvicorn's async event loop handles concurrent WebSocket connections directly.

### Local Development with Docker Compose

```yaml
# docker-compose.yml
services:
  livoia:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LIVOIA_LOG_LEVEL=DEBUG
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - BEDROCK_REGION=us-east-1
      - BEDROCK_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - BEDROCK_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    volumes:
      - ./src:/app/src  # Hot reload (development only)
```

---

## Tox Configuration

```ini
[tox]
envlist = py313, lint, typecheck
isolated_build = true

[testenv]
deps = .[dev]
commands = pytest --cov=livoia --cov-report=term --cov-report=xml:coverage.xml {posargs}

[testenv:lint]
commands =
    ruff check .
    ruff format --check .
    pylint src/livoia

[testenv:typecheck]
commands = mypy src/livoia tests
```

The `tox.ini` is the single source of truth for quality checks. CI runs the same commands as local development.

---

## pyproject.toml

### Key Sections

```toml
[project]
name = "livoia"
version = "1.0.0"
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "pydantic>=2.10",
    "pydantic-settings>=2.7",
    "google-adk>=1.3",
    "jinja2>=3.1",
    "structlog>=24.4",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.25",
    "pytest-cov>=6.1",
    "tox>=4.23",
    "ruff>=0.11",
    "mypy>=1.15",
    "pylint>=3.3",
    "pre-commit>=4.1",
    "commitizen>=4.4",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/livoia"]
```

Note: The Bedrock SDK dependency (`aws-sdk-bedrock-runtime` or equivalent) will be specified based on the exact package available at implementation time. The PoC uses internal Avature packages for Bedrock streaming.
