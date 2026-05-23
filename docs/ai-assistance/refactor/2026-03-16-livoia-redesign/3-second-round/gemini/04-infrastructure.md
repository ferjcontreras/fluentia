# Infrastructure & CI/CD Specification

The production repository must operate as a secure, stateless, and horizontally scalable backend service designed specifically for Kubernetes deployment.

## Containerization (Docker)

The application will be packaged using a highly optimized, two-stage Dockerfile leveraging `uv` for dependency management. Real-time audio processing (even if handled remotely by the LLM SDKs, local buffering may require specific libraries) necessitates careful base image selection.

### Multi-Stage Build Strategy

**Stage 1: Builder (`python:3.13-slim`)**
1. Install OS-level build dependencies if required (e.g., `build-essential`, `portaudio19-dev` for testing tools, though pure production shouldn't require local audio devices).
2. Install `uv`.
3. Copy `pyproject.toml` and `uv.lock`.
4. Run `uv sync --no-dev` to resolve and install the exact production dependency tree into a virtual environment (`/.venv`).

**Stage 2: Runtime (`python:3.13-slim`)**
1. Install only the essential runtime OS libraries (omitting compilers).
2. Copy the synthesized `/.venv` from the Builder stage.
3. Copy application source code.
4. Establish a non-root system user (`appuser`).
5. **Entrypoint**: `uvicorn src.livoia.app.main:app --host 0.0.0.0 --port 8000 --workers 4`
   *(Worker count configures horizontal scaling per-pod depending on target K8s resources).*

## Environment & Configuration Management

Configuration will be strictly typed and validated at application startup using `pydantic-settings`. There will be no fallback to parsing `.env` files in the production deployment; all variables must be explicitly provided to the container environment by the orchestrator.

### Core Configuration Schema

```python
class AppSettings(BaseSettings):
    environment: Literal["dev", "staging", "prod"] = "dev"
    log_level: str = "INFO"

    # External Provider Keys
    google_api_key: SecretStr | None = None

    # AWS configuration relies entirely on boto3/AWS SDK ambient credential discovery
    # via Kubernetes IAM Roles for Service Accounts (IRSA).
    aws_region: str = "us-east-1"

    # Tool Integrations
    orchestrator_api_url: HttpUrl | None = None
    orchestrator_auth_token: SecretStr | None = None
```

If an environment variable required by the configuration schema is missing or malformed, the application will crash immediately upon initialization, adhering to the "fail-fast" principle.

## CI/CD Pipeline Architecture (`.github/workflows/ci.yml`)

The pipeline enforces rigorous progression gates before any code merges or deploys to staging/production.

### 1. Quality & Static Analysis Stage
Executes instantly on runner provision. Failure halts the entire pipeline.
- **Linting**: `uv run ruff check .`
- **Formatting**: `uv run ruff format --check .`
- **Type Checking**: `uv run mypy src tests` (running in strict mode)

### 2. Testing Stage
- **Unit Tests**: Isolated testing of Orchestrator logic, Prompts, and Tools using heavily mocked generic inputs.
- **Integration Tests**: Tests asserting the `ProviderAdapters` behave correctly. Some tests may require sandbox credentials to hit real Bedrock/Google endpoints to ensure API compatibility hasn't shifted.
- **Coverage Output**: Generates a standard Cobertura XML report for GitLab UI visualization. Requires minimum coverage thresholds.

### 3. Security & Dependency Analysis Stage
- Executes company-standard docker-based dependency scanners. Needs manual triggering for non-critical branches or scheduled daily runs against `main`.

### 4. Build & Registry Stage
- Triggered exclusively on tags (e.g., `v*.*.*`) or explicit merges to `main`.
- Authenticates securely with AWS ECR via STS assume-role using the GitLab Runner's identity.
- Builds the multi-stage Dockerfile and pushes the hardened image to the deployment registry.
