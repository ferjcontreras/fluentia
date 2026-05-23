# CI/CD and Quality Baseline

## Goals

- Preserve current engineering quality standards.
- Keep GitLab CI compatibility with organizational infrastructure.
- Make Docker build/publish reliable for release pipelines.

## Quality toolchain

- Package/dependency manager: `uv`
- Formatter/linter: `ruff`
- Type checking: `mypy`
- Static analysis: `pylint`
- Test orchestration: `pytest` + `tox`
- Commit hooks: `pre-commit`

## Local development contract

- `uv sync --group dev`
- `uv run pre-commit install --install-hooks`
- `./check_code.sh` for rapid quality feedback
- `uv run tox` before merge request

## CI stages (recommended)

1. `quality`
   - lint (`ruff`, `pylint`)
   - typecheck (`mypy`)
2. `tests`
   - unit tests mandatory
   - integration tests conditional by env/tag strategy
3. `build`
   - Docker build on tags/releases
4. `dependency-analysis`
   - manual or scheduled

## Adaptation rules for pipeline file

Keep:

- `python:3.13-slim` base image convention
- `uv` bootstrap in `before_script`
- cache paths (`.cache/uv`, `.venv`, `.tox`, `.pytest_cache`)
- separate lint/typecheck/test jobs
- tag-driven build-image pattern

Adapt:

- remove dependencies not required by stage 1 runtime image
- align package paths to `src/livoia`
- ensure image naming and registry paths match the new project
- enforce least-privilege, short-lived credentials in build job

## Docker build guidance

- Multi-stage Dockerfile preferred:
  - builder stage installs deps and builds wheel/artifacts
  - runtime stage keeps only runtime dependencies and app artifacts
- Run as non-root user.
- Expose only required port.
- Integrate `/health` check.
- Keep provider credentials external.

## Recommended quality gates

- Lint/format clean on merge requests.
- `mypy` clean for production package.
- `pylint` threshold preserved (or stricter).
- Unit tests required for merge.
- Integration/e2e required in protected branch or dedicated pipeline variants.

## Test strategy posture

- `tests/unit`: primary fast feedback loop for domain/services/providers.
- `tests/integration`: provider contract and websocket flow confidence.
- `tests/e2e`: critical product-path verification and health checks.

## Multi-agent readiness in quality policy

- Add profile contract tests for each new `AgentProfile`.
- Add schema validation tests for profile-specific prompt settings.
- Prevent profile additions without corresponding tests and documentation updates.
