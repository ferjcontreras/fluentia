# Iterative Redesign: CI/CD & Containerization

## 1. Containerization Strategy

The production system needs to be fully stateless and horizontally scalable inside Kubernetes. This requires a hardened Docker image that strips away all development tools while preserving the necessary system dependencies for real-time audio.

### 1.1 Dockerfile Design (Multi-Stage)

Currently, the PoC runs directly on the host using `uv run`. The production image will use a two-stage approach leveraging `uv`'s performance.

**Stage 1: Builder:**
- Base Image: `python:3.13-slim`
- Install system dependencies: `build-essential`, `portaudio19-dev` (needed for PyAudio/Bidirectional audio).
- Install `uv` via bash script.
- Copy application code and `pyproject.toml` / `uv.lock`.
- Run `uv sync --no-dev` to install only production dependencies into a `.venv`.

**Stage 2: Runtime:**
- Base Image: `python:3.13-slim`
- Install ONLY runtime system dependencies (e.g., `libportaudio2`), dropping the heavier `-dev` packages and compilers.
- Copy the `.venv` and application code from the Builder stage.
- Run as a non-root user for security.
- **Entrypoint:** Run the FastAPI server via `uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --workers 4` (or using gunicorn depending on concurrency tests).

### 1.2 Environment Management (Kubernetes Readiness)

The current PoC relies on `.env` files or direct exports. The new app must use `pydantic-settings` to strictly define and validate environment variables at startup.

**Required Secrets/Variables (Injected by K8s):**
- `AWS_REGION` (For Bedrock Nova Sonic. AWS credentials like `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are optional and omitted in production, as the K8s pod inherits its AWS IAM role automatically).
- `GOOGLE_API_KEY` (For Google ADK).
- `ORCHESTRATOR_API_URL`, `ORCHESTRATOR_AUTH_TOKEN` (For future tool routing).
- `LOG_LEVEL` (Default `INFO`, settable to `DEBUG`).

## 2. CI/CD Pipeline (`.github/workflows/ci.yml`)

The existing GitHub Actions configuration is strong and already uses `uv` and AWS ECR integrations. The new `.github/workflows/ci.yml` will be an evolution of the current file.

### 2.1 Pipeline Stages
The pipeline will execute the following stages in order:

1. **`quality`**:
   - `lint`: Runs `uv run ruff check .` and `uv run ruff format --check .`
   - `typecheck`: Runs `uv run mypy src tests`
   - *Failure in this stage blocks all subsequent stages.*

2. **`tests`**:
   - `unit_tests`: Runs isolated logic tests.
   - `integration_tests`: Runs tests requiring mocked external providers or local Redis (if caching is used).
   - Generates coverage reports (`coverage/coverage.xml`) used by GitLab's native coverage visualization.

3. **`dependency-analysis`**:
   - Uses the custom `registry. image.
   - Requires `manual` trigger (as in the PoC).

4. **`build`**:
   - Triggered only on tags (e.g., `v1.0.0`).
   - Assumes Jenkins ECR role via AWS STS.
   - Builds the optimized multi-stage Dockerfile.
   - Pushes to `381491985459.dkr.ecr.us-east-1.amazonaws.com/english-teacher-assistant:v...`

### 2.2 Local Development Parity

To ensure developers match the CI environment exactly:
- `tox.ini` will remain the source of truth for local task execution.
- Running `tox -e lint`, `tox -e typecheck`, and `tox -e py313` locally will execute the exact same commands running in the GitLab `quality` and `tests` stages.
