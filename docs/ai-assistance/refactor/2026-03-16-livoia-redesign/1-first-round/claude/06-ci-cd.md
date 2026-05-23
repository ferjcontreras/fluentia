# CI/CD and Code Quality Design

## Code Quality Tools

Same toolchain as the PoC, with the same configuration philosophy:

| Tool | Purpose | Config Location |
|------|---------|-----------------|
| **ruff** | Linting + formatting | `pyproject.toml` [tool.ruff] |
| **mypy** | Type checking | `pyproject.toml` [tool.mypy] |
| **pylint** | Code quality analysis | `pyproject.toml` [tool.pylint] |
| **pre-commit** | Git hook automation | `.pre-commit-config.yaml` |
| **commitizen** | Commit message validation | `pyproject.toml` [tool.commitizen] |
| **tox** | Test orchestration | `tox.ini` |
| **pytest** | Test framework | `pyproject.toml` [tool.pytest] |

## pyproject.toml

### Build System

```toml
[build-system]
requires = ["hatchling>=1.27.0"]
build-backend = "hatchling.build"

[project]
name = "livoia"
version = "0.1.0"
description = "Live Voice Agent - Production"
requires-python = ">=3.13"
dependencies = [
    "aws-sdk-bedrock-runtime>=0.1.0,<0.2.0",
    "fastapi>=0.123.10",
    "google-adk>=1.20.0",
    "pydantic-settings>=2.7.1",
    "pydantic>=2.10.6",
    "smithy-aws-core>=0.0.1",
    "uvicorn>=0.35.0",
]

[dependency-groups]
dev = [
    "commitizen>=4.1.0",
    "factory-boy>=3.3.0",
    "faker>=22.0.0",
    "mypy>=1.15.0",
    "pre-commit>=4.0.0",
    "pylint>=3.3.4",
    "pytest-asyncio>=1.1.0",
    "pytest-cov>=6.0.0",
    "pytest-mock>=3.14.0",
    "pytest>=8.3.4",
    "ruff>=0.9.5",
    "tox>=4.24.1",
    "tox-uv>=1.25.0",
]

[tool.hatch.build.targets.wheel]
packages = ["src/livoia"]
```

### Ruff Configuration

Same as PoC, adapted for new paths:

```toml
[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "D", "S", "B", "T20", "ARG", "RUF"]
extend-select = ["E501", "ASYNC", "RUF006", "I"]
fixable = ["ALL"]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "ARG", "FBT", "S311", "D", "S104", "S106"]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.isort]
split-on-trailing-comma = false
force-single-line = true

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = true
line-ending = "auto"
```

### Mypy Configuration

```toml
[tool.mypy]
allow_untyped_defs = true
allow_untyped_calls = true
disable_error_code = "annotation-unchecked"
ignore_missing_imports = true
plugins = ['pydantic.mypy']
python_version = "3.13"
show_error_codes = true
strict = true
warn_return_any = true
warn_unused_configs = true
warn_unused_ignores = true

[[tool.mypy.overrides]]
module = "tests.*"
disable_error_code = [
    "no-untyped-def", "no-untyped-call", "misc", "arg-type",
    "var-annotated", "union-attr", "index", "assignment",
    "return-value", "attr-defined"
]
check_untyped_defs = false
```

### Pylint Configuration

```toml
[tool.pylint.main]
fail-under = 9.9
jobs = 0
py-version = "3.13"

[tool.pylint.format]
max-line-length = 100

[tool.pylint.design]
max-locals = 16

[tool.pylint."messages control"]
disable = [
    "C0111", "W0703", "unsubscriptable-object", "W0511", "W1203",
    "raw-checker-failed", "bad-inline-option", "locally-disabled",
    "file-ignored", "suppressed-message", "useless-suppression",
    "deprecated-pragma", "use-symbolic-message-instead", "too-few-public-methods",
]
max-attributes = 10
```

### Pytest Configuration

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
markers = [
    "manual: marks tests that should only be run manually",
    "real_env: marks tests that should use real environment variables",
    "integration: marks tests as integration tests",
    "e2e: marks tests as end-to-end tests",
]
testpaths = ["tests"]
addopts = "-m 'not manual and not integration and not e2e'"
```

## tox.ini

```ini
[tox]
min_version = 4.24.1
basepython = python3.13
envlist = py313, lint, typecheck
isolated_build = true

[testenv]
package = editable
dependency_groups = dev
commands =
    pytest -m "not manual and not integration and not e2e" \
        --cov=livoia --cov-report=term-missing \
        --cov-report=xml --cov-report=html {posargs:tests}

[testenv:lint]
dependency_groups = dev
commands =
    ruff check .
    ruff format --check .
    pylint src/livoia

[testenv:typecheck]
dependency_groups = dev
commands =
    mypy src/livoia tests
```

## .pre-commit-config.yaml

Same as PoC:

```yaml
default_install_hook_types: [commit-msg, pre-commit]
default_language_version:
  python: python3.13
fail_fast: true

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-ast
      - id: check-case-conflict
      - id: check-json
      - id: check-merge-conflict
      - id: check-shebang-scripts-are-executable
      - id: check-toml
      - id: check-yaml
      - id: debug-statements
      - id: detect-private-key

  - repo: https://github.com/pre-commit/pygrep-hooks
    rev: v1.10.0
    hooks:
      - id: python-check-mock-methods
      - id: python-use-type-annotations

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.4
    hooks:
      - id: ruff-check
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/commitizen-tools/commitizen
    rev: v4.9.1
    hooks:
      - id: commitizen
        stages: [commit-msg]
```

## check_code.sh

Same as PoC, with updated paths:

```bash
#!/bin/bash
# Runs: ruff format, ruff check --fix, mypy, pylint
# Updated paths: src/livoia (single package)

# mypy: src/livoia tests
# pylint: src/livoia
```

## .gitlab-ci.yml

```yaml
image: python:3.13-slim

variables:
  UV_CACHE_DIR: "$CI_PROJECT_DIR/.cache/uv"
  UV_LINK_MODE: "copy"

before_script:
  - apt-get update && apt-get install -y --no-install-recommends git build-essential curl
  - curl -LsSf https://astral.sh/uv/install.sh | sh
  - export PATH="$HOME/.local/bin:$PATH"
  - python --version
  - uv --version
  - uv sync --group dev

cache:
  paths:
    - .cache/uv
    - .venv
    - .tox
    - .pytest_cache

stages:
  - quality
  - tests
  - dependency-analysis
  - build

lint:
  stage: quality
  script:
    - uv run tox -e lint
  rules:
    - changes:
      - "**/*.py"
      - "pyproject.toml"
      - "tox.ini"

typecheck:
  stage: quality
  script:
    - uv run tox -e typecheck
  rules:
    - changes:
      - "**/*.py"
      - "pyproject.toml"
      - "tox.ini"

tests:
  stage: tests
  script:
    - uv run tox
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage/coverage.xml
  rules:
    - changes:
      - "**/*.py"
      - "pyproject.toml"
      - "tox.ini"

dependency-analysis-job:
  stage: dependency-analysis
  when: manual
  variables:
    DEFAULT_EXPANDED: false
    DEPENDENCIES: build-essential
  image: registry.xcade.net/python-dependency-analysis:latest
  before_script: []
  script:
    - run
  artifacts:
    paths:
      - audit.json
      - outdated.json

build-image:
  stage: build
  tags:
    - dev-releaseengineering
  before_script: []
  script:
    - echo "Assuming ECR role"
    - STS=($(aws sts assume-role
        --role-arn arn:aws:iam::381491985459:role/AvatureJenkinsECR
        --role-session-name gitlab-ci-docker-pipeline
        --duration-seconds 900
        --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]'
        --output text))
    - export AWS_ACCESS_KEY_ID="${STS[0]}"
    - export AWS_SECRET_ACCESS_KEY="${STS[1]}"
    - export AWS_SESSION_TOKEN="${STS[2]}"
    - echo "Building image with tag ${CI_COMMIT_TAG}"
    - docker build -t 381491985459.dkr.ecr.us-east-1.amazonaws.com/livoia:$CI_COMMIT_TAG .
    - echo "Pushing image to ECR"
    - docker push 381491985459.dkr.ecr.us-east-1.amazonaws.com/livoia:$CI_COMMIT_TAG
  rules:
    - if: '$CI_COMMIT_TAG'
      when: always
    - when: never
```

Key changes from PoC:
- Removed `portaudio19-dev` from `before_script` (no PyAudio dependency)
- Updated image name from `english-teacher-assistant` to `livoia`
- Removed `DEPENDENCIES` that aren't needed (`libldap2-dev`, `libsasl2-dev`, `tzdata`, `pkg-config`)

## Testing Strategy

### Test Categories

| Type | Directory | Marker | Runs in CI | Description |
|------|-----------|--------|------------|-------------|
| Unit | `tests/unit/` | (default) | Yes | Fast, mocked, no external services |
| Integration | `tests/integration/` | `@pytest.mark.integration` | No (manual) | Real API calls |
| E2E | `tests/e2e/` | `@pytest.mark.e2e` | No (manual) | Full WebSocket sessions |

### Unit Test Coverage Targets

| Module | Target Coverage | Key Test Areas |
|--------|----------------|----------------|
| `config.py` | 100% | Default values, env var loading |
| `app.py` | 90% | App creation, endpoint routing, prompt_config parsing |
| `providers/google.py` | 80% | Session handling, config, modality selection |
| `providers/bedrock/provider.py` | 80% | Event conversion, connection lifecycle |
| `providers/bedrock/client.py` | 70% | Event sending, response handling |
| `prompts/interview.py` | 100% | Rendering with all parameter combinations |
| `tools/processor.py` | 100% | Registration, lookup, execution |
| `tools/builtin/date_time.py` | 100% | Execution and output format |

### Test Fixtures

Carry forward the fluent mock builder pattern:

```python
class NovaSonicClientMockBuilder:
    """Fluent builder for NovaSonicClient mocks."""

    def with_events(self, events: list[SpeechEvents.Base]) -> Self: ...
    def with_active(self, active: bool) -> Self: ...
    def build(self) -> MagicMock: ...
```
