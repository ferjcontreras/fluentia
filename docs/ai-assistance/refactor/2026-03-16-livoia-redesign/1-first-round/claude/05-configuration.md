# Configuration and Deployment Design

## Application Configuration

All configuration uses **Pydantic BaseSettings** with environment variables. No `.env` file loading in production (environment variables injected by Kubernetes). `.env` files are only for local development.

### Configuration Hierarchy

```python
class AppConfig(BaseSettings):
    """Top-level application configuration."""

    # Application
    log_level: str = Field(default="WARNING", description="Logging level")
    host: str = Field(default="0.0.0.0", description="Server bind host")
    port: int = Field(default=8000, description="Server bind port")

    # Provider configs
    google: GoogleProviderConfig = Field(default_factory=GoogleProviderConfig)
    bedrock: BedrockProviderConfig = Field(default_factory=BedrockProviderConfig)

    model_config = {"env_prefix": "LIVOIA_", "env_nested_delimiter": "__"}


class GoogleProviderConfig(BaseSettings):
    """Google Gemini provider configuration."""
    model: str = "gemini-2.5-flash-native-audio-preview-09-2025"
    use_vertex_ai: bool = False
    api_key: str | None = None
    cloud_project: str | None = None
    cloud_location: str = "us-central1"

    model_config = {"env_prefix": "GOOGLE_"}


class BedrockProviderConfig(BaseSettings):
    """AWS Bedrock provider configuration."""
    region: str = "us-east-1"
    model_id: str = "amazon.nova-2-sonic-v1:0"
    voice_id: str = "matthew"
    input_sample_rate: int = 16000
    output_sample_rate: int = 24000
    language: str | None = None

    model_config = {"env_prefix": "BEDROCK_"}
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LIVOIA_LOG_LEVEL` | `WARNING` | Application log level |
| `LIVOIA_HOST` | `0.0.0.0` | Server bind address |
| `LIVOIA_PORT` | `8000` | Server port |
| `GOOGLE_API_KEY` | (none) | Google API key for Gemini |
| `GOOGLE_MODEL` | `gemini-2.5-flash-native-audio-preview-09-2025` | Gemini model ID |
| `GOOGLE_USE_VERTEX_AI` | `false` | Use Vertex AI instead of Gemini API |
| `GOOGLE_CLOUD_PROJECT` | (none) | GCP project (Vertex AI only) |
| `GOOGLE_CLOUD_LOCATION` | `us-central1` | GCP location (Vertex AI only) |
| `BEDROCK_REGION` | `us-east-1` | AWS region |
| `BEDROCK_MODEL_ID` | `amazon.nova-2-sonic-v1:0` | Nova Sonic model ID |
| `BEDROCK_VOICE_ID` | `matthew` | Voice for speech synthesis |
| `BEDROCK_INPUT_SAMPLE_RATE` | `16000` | Input audio sample rate |
| `BEDROCK_OUTPUT_SAMPLE_RATE` | `24000` | Output audio sample rate |
| `BEDROCK_LANGUAGE` | (none, auto-detect) | Language code (e.g., `en-US`) |
| `AWS_ACCESS_KEY_ID` | (none) | AWS credentials (from Kubernetes) |
| `AWS_SECRET_ACCESS_KEY` | (none) | AWS credentials (from Kubernetes) |
| `AWS_SESSION_TOKEN` | (none) | AWS session token (from Kubernetes) |

### `.env.example`

```bash
# Application
LIVOIA_LOG_LEVEL=INFO

# Google Gemini
GOOGLE_API_KEY=your-google-api-key-here
# GOOGLE_MODEL=gemini-2.5-flash-native-audio-preview-09-2025

# AWS Bedrock (obtain from https://aws-global.example.com/)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_SESSION_TOKEN=your-session-token

# Bedrock options (defaults are usually fine)
# BEDROCK_REGION=us-east-1
# BEDROCK_VOICE_ID=matthew
```

## Docker

### Dockerfile

Multi-stage build, same approach as PoC but simplified:

```dockerfile
# Build stage
FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Production stage
FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd -r livoia && useradd -r -u 1000 -g livoia -m -d /home/livoia livoia

WORKDIR /app

# Copy installed packages
COPY --from=builder /usr/local/lib/python3.13/site-packages \
     /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy Docker scripts
COPY --chown=livoia:livoia docker/ ./docker/
RUN chmod +x ./docker/entrypoint.sh ./docker/healthcheck.sh

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HOME=/home/livoia

EXPOSE 8000
USER livoia

HEALTHCHECK --interval=240s --timeout=3s --start-period=10s --retries=3 \
    CMD /app/docker/healthcheck.sh || exit 1

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["uvicorn", "livoia.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

Key differences from PoC:
- **No `resources/` copy**: Prompts are now in Python code, not text files
- **Entry point**: `livoia.app:create_app` (single package, not `livoia_web.app`)
- **Static files**: Inside the package, automatically included in site-packages

### `docker/entrypoint.sh`

```bash
#!/bin/bash
set -e
exec "$@"
```

### `docker/healthcheck.sh`

```bash
#!/bin/bash
curl -f http://localhost:${PORT:-8000}/health || exit 1
```

### `.dockerignore`

```
.git
.tox
.venv
.cache
.ruff_cache
.pytest_cache
.mypy_cache
__pycache__
*.pyc
coverage/
tests/
docs/
.claude/
*.md
!README.md
.env
.env.*
!.env.example
```

## Kubernetes Considerations

The Docker image is designed for Kubernetes deployment:

1. **Non-root user**: Runs as `livoia` (UID 1000)
2. **Health check**: `/health` endpoint for liveness/readiness probes
3. **Environment variables**: All configuration via env vars (no config files to mount)
4. **Secrets**: AWS credentials and API keys injected as Kubernetes secrets -> env vars
5. **Single port**: Only exposes 8000
6. **Stateless**: No local state (sessions are in-memory and ephemeral)
7. **Graceful shutdown**: uvicorn handles SIGTERM

### Kubernetes Probe Configuration (reference)

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

Note: Kubernetes configuration files are managed in a separate repository, not in this project.

## Local Development

### Running Locally

```bash
# Install dependencies
uv sync --group dev

# Set environment variables
export GOOGLE_API_KEY="..."
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."

# Run with auto-reload
uv run uvicorn livoia.app:create_app --factory --reload --host 0.0.0.0 --port 8000
```

### Running with Docker

```bash
# Build
docker build -t livoia .

# Run
docker run -p 8000:8000 \
  -e GOOGLE_API_KEY="..." \
  -e AWS_ACCESS_KEY_ID="..." \
  -e AWS_SECRET_ACCESS_KEY="..." \
  -e AWS_SESSION_TOKEN="..." \
  livoia
```
