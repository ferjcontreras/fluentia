# CI/CD and Quality Baseline

## Goals

- Preserve current quality standards.
- Keep GitLab CI integration compatible with organizational infrastructure.
- Make Docker build/publish straightforward for release pipelines.

## Quality toolchain (keep)

- Package/dependency manager: `uv`
- Formatter/linter: `ruff`
- Type checking: `mypy`
- Static analysis: `pylint`
- Test orchestration: `pytest` + `tox`
- Commit hooks: `pre-commit`

## Local development contract

- `uv sync --group dev`
- `uv run pre-commit install --install-hooks`
- `./check_code.sh` for rapid full quality feedback
- `uv run tox` before merge request

## CI stages (recommended)

1. `quality`
   - lint (`ruff`, `pylint`)
   - typecheck (`mypy`)
2. `tests`
   - unit tests mandatory
   - integration tests conditional by tag or env availability
3. `build`
   - Docker build on tags/releases
4. `dependency-analysis` (manual or scheduled)

## Adaptation from current `.gitlab-ci.yml`

Keep:
- `python:3.13-slim` base image convention
- `uv` bootstrap in `before_script`
- cached directories (`.cache/uv`, `.venv`, `.tox`, `.pytest_cache`)
- separate jobs for lint/typecheck/tests
- tagged `build-image` job pattern

Adapt:
- remove `portaudio19-dev` dependency from baseline build if camera/native audio hardware path is not required in production image
- align test coverage targets to `src/livoia_prod`
- adjust Docker image name/repository for new project
- ensure build job uses least-privilege credentials and short-lived tokens

## Docker build guidance

- Multi-stage Dockerfile preferred:
  - builder stage installs dependencies and builds wheel
  - runtime stage contains only runtime deps and app artifacts
- Run app as non-root user.
- Expose only required port.
- Add healthcheck endpoint integration.
- Keep provider credentials external (runtime env vars only).

## Release and deployment posture

- Tag-driven immutable image publishing.
- GitLab job artifacts include test and coverage reports.
- Optional security/scanning jobs can be added without changing architecture.

## Recommended initial quality gates

- Lint and format clean on merge requests.
- `mypy` clean for production package.
- `pylint` minimum threshold preserved (or stricter).
- Unit tests required; integration tests required in protected branches/pipeline variants.
