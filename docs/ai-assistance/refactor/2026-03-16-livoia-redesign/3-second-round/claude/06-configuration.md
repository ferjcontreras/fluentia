# 6. Configuration

## Configuration Layers

Configuration is organized in three layers, each serving a different purpose:

| Layer | Source | Scope | Examples |
|-------|--------|-------|---------|
| **Environment variables** | Kubernetes, `.env` (dev only) | Per-deployment, includes secrets | API keys, AWS credentials, region |
| **Typed settings** | Pydantic BaseSettings | Application-wide, validated at startup | Host, port, log level, model IDs |
| **Per-session config** | Client WebSocket message | Per-session, non-secret | Agent name, company name, questions |

## Typed Settings (Pydantic BaseSettings)

### Configuration Hierarchy

```python
class AppConfig(BaseSettings):
    """Root application configuration."""

    model_config = SettingsConfigDict(
        env_prefix="LIVOIA_",
        env_nested_delimiter="__",
    )

    # Application
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    default_provider: str = "google"
    default_agent: str = "interviewer"

    # Provider configs
    google: GoogleProviderConfig = GoogleProviderConfig()
    bedrock: BedrockProviderConfig = BedrockProviderConfig()


class GoogleProviderConfig(BaseSettings):
    """Google ADK provider configuration."""

    model_config = SettingsConfigDict(env_prefix="GOOGLE_")

    api_key: str = ""
    cloud_project: str = ""
    model: str = "gemini-2.5-flash-native-audio-preview-09-2025"


class BedrockProviderConfig(BaseSettings):
    """AWS Bedrock Nova Sonic provider configuration."""

    model_config = SettingsConfigDict(env_prefix="BEDROCK_")

    region: str = "us-east-1"
    model_id: str = "amazon.nova-2-sonic-v1:0"
    voice_id: str = "matthew"
    input_sample_rate: int = 16000
    output_sample_rate: int = 24000
    language: str | None = None

    # AWS credentials: optional in production (IRSA provides them)
    # Set explicitly only for local development
    access_key_id: str | None = None
    secret_access_key: str | None = None
```

### Environment Variable Reference

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LIVOIA_HOST` | `str` | `"0.0.0.0"` | Server bind address |
| `LIVOIA_PORT` | `int` | `8000` | Server port |
| `LIVOIA_LOG_LEVEL` | `str` | `"INFO"` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `LIVOIA_DEFAULT_PROVIDER` | `str` | `"google"` | Default voice provider |
| `LIVOIA_DEFAULT_AGENT` | `str` | `"interviewer"` | Default agent definition |
| `GOOGLE_API_KEY` | `str` | `""` | Google API key (Gemini) |
| `GOOGLE_CLOUD_PROJECT` | `str` | `""` | Google Cloud project (Vertex AI) |
| `GOOGLE_MODEL` | `str` | `"gemini-2.5-flash-native-audio-preview-09-2025"` | Gemini model ID |
| `BEDROCK_REGION` | `str` | `"us-east-1"` | AWS region |
| `BEDROCK_MODEL_ID` | `str` | `"amazon.nova-2-sonic-v1:0"` | Nova Sonic model ID |
| `BEDROCK_VOICE_ID` | `str` | `"matthew"` | Voice for speech synthesis |
| `BEDROCK_INPUT_SAMPLE_RATE` | `int` | `16000` | Input audio sample rate (Hz) |
| `BEDROCK_OUTPUT_SAMPLE_RATE` | `int` | `24000` | Output audio sample rate (Hz) |
| `BEDROCK_LANGUAGE` | `str?` | `None` | Language code (e.g., `"en-US"`) |
| `BEDROCK_ACCESS_KEY_ID` | `str?` | `None` | AWS access key (dev only) |
| `BEDROCK_SECRET_ACCESS_KEY` | `str?` | `None` | AWS secret key (dev only) |

### Startup Validation

Configuration is loaded and validated at application startup (in the FastAPI lifespan handler). If validation fails, the application exits immediately with a clear error message indicating which variable is invalid and what was expected.

```python
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    config: AppConfig = AppConfig()
    log_config_summary(config)  # Logs all settings with secrets redacted
    app.state.config = config
    yield
```

## Secret Handling Policy

1. **Never log raw API keys or credentials.** The `log_config_summary()` function redacts values for fields named `*_key*`, `*_secret*`, `*_token*`, `*_password*`.
2. **Zero baked credentials in Docker images.** The Dockerfile does not copy `.env` files or set secret environment variables. All secrets are injected at runtime by Kubernetes.
3. **AWS credentials are optional.** In production, IAM Roles for Service Accounts (IRSA) provides Bedrock credentials automatically. The `access_key_id` and `secret_access_key` fields are only set for local development.
4. **`.env` files are development-only.** The `.env` file is in `.gitignore`. An `.env.example` is provided with placeholder values.

## Per-Session Runtime Configuration

The `prompt_config` WebSocket message (described in [04-agents-and-prompts.md](04-agents-and-prompts.md)) provides per-session customization. These values are:

- **Non-secret**: Agent name, company name, questions, guidelines.
- **Per-session**: Different values for each WebSocket connection.
- **Optional**: All fields have defaults in the agent definition.
- **Agent-specific**: Each agent type defines its own set of configurable fields.

This layer exists because these values change per session and per user, making them unsuitable for environment variables. They are not secrets, so they can be sent over the WebSocket without concern.

## Adding Configuration for New Features

When a new provider or feature needs configuration:

1. **Add a Pydantic model** with its own `env_prefix`.
2. **Add it as a field** on `AppConfig` (or the relevant provider config).
3. **Document the new variables** in the table above.
4. **Provide sensible defaults** for all non-secret values.

Example for a future Orchestrator integration:

```python
class OrchestratorConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ORCHESTRATOR_")

    api_url: str = ""
    auth_token: str = ""
    timeout_seconds: int = 30
```
