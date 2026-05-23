# 8. Observability

## Principles

1. **Observability is a stage-1 requirement**, not a future enhancement. A real-time voice application without structured logging and health checks is not production-ready.
2. **Log-based metrics first.** Ship metrics as structured log events. This works with any log aggregation tool and avoids adding Prometheus or StatsD as stage-1 dependencies.
3. **Correlation IDs everywhere.** Every log entry within a session includes the session ID, enabling trace-like debugging across the session lifecycle.

## Structured Logging

### Configuration

Use `structlog` (or `python-json-logger`) for JSON-formatted log output:

```python
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,    # Include context vars (session_id)
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        mask_sensitive_values,                       # Redact secrets
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(log_level),
)
```

### Log Fields

Every log entry includes:

| Field | Source | Example |
|-------|--------|---------|
| `timestamp` | Auto | `"2026-03-17T14:30:00.123Z"` |
| `level` | Auto | `"info"` |
| `event` | Logger call | `"session_started"` |
| `session_id` | Context var | `"a1b2c3d4-..."` |
| `user_id` | Context var | `"user-123"` |
| `provider` | Context var | `"google"` |
| `agent` | Context var | `"interviewer"` |

### Session Context Binding

When a WebSocket session starts, bind context variables that persist for all log entries within that session:

```python
structlog.contextvars.clear_contextvars()
structlog.contextvars.bind_contextvars(
    session_id=session_id,
    user_id=user_id,
    provider=provider,
    agent=agent_name,
)
```

### Key Log Events

| Event | Level | When |
|-------|-------|------|
| `app_started` | info | Application startup, includes config summary (secrets redacted) |
| `session_started` | info | WebSocket session begins |
| `session_ended` | info | Session ends (includes duration) |
| `session_error` | error | Unrecoverable session error |
| `provider_connected` | info | Connected to external voice service |
| `provider_disconnected` | warning | Lost connection to external service |
| `provider_reconnecting` | info | Attempting reconnection |
| `tool_executed` | info | Tool execution completed (includes tool name, duration, success) |
| `prompt_rendered` | debug | Prompt template rendered (includes template name, variable keys) |
| `audio_interrupted` | info | Barge-in detected |

### Sensitive Value Redaction

A structlog processor masks values for keys matching:
- `*_key*`, `*_secret*`, `*_token*`, `*_password*`, `*_credential*`

Replacement: `"***REDACTED***"`

### Health Endpoint Log Suppression

Health check requests (`/health`, `/ready`) generate high-volume, low-value log entries. These are suppressed by a uvicorn access log filter:

```python
class HealthCheckFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message: str = record.getMessage()
        return "/health" not in message and "/ready" not in message
```

## Health Endpoints

### Liveness: `/health`

Returns 200 if the process is running. Used by Kubernetes liveness probe.

```json
{
    "status": "ok",
    "version": "1.0.0",
    "uptime_seconds": 3600
}
```

### Readiness: `/ready`

Returns 200 if the application is ready to serve traffic. Checks that configuration is loaded and providers can be initialized.

```json
{
    "status": "ready",
    "providers": {
        "google": "available",
        "bedrock": "available"
    }
}
```

If a provider is not configured (e.g., no Google API key), it reports `"not_configured"` but the endpoint still returns 200 -- the application can serve sessions for the other provider.

### Kubernetes Probe Configuration

```yaml
livenessProbe:
    httpGet:
        path: /health
        port: 8000
    initialDelaySeconds: 10
    periodSeconds: 30
readinessProbe:
    httpGet:
        path: /ready
        port: 8000
    initialDelaySeconds: 5
    periodSeconds: 10
```

## Metrics

### MetricsCollector Protocol

Define a protocol (structural typing) for metrics collection. This allows swapping implementations without changing call sites.

```python
class MetricsCollector(Protocol):
    """Interface for collecting application metrics."""

    def session_started(self, provider: str, agent: str) -> None: ...
    def session_ended(self, provider: str, agent: str, duration_seconds: float) -> None: ...
    def session_error(self, provider: str, agent: str, error_type: str) -> None: ...
    def tool_executed(self, tool_name: str, duration_seconds: float, success: bool) -> None: ...
    def provider_reconnection(self, provider: str, success: bool) -> None: ...
```

### Stage 1: LoggingMetricsCollector

Metrics are emitted as structured log events with a `metric` prefix:

```python
class LoggingMetricsCollector:
    """Emits metrics as structured log events."""

    def session_started(self, provider: str, agent: str) -> None:
        log.info("metric.session_started", provider=provider, agent=agent)

    def session_ended(self, provider: str, agent: str, duration_seconds: float) -> None:
        log.info("metric.session_ended", provider=provider, agent=agent, duration=duration_seconds)

    def tool_executed(self, tool_name: str, duration_seconds: float, success: bool) -> None:
        log.info("metric.tool_executed", tool=tool_name, duration=duration_seconds, success=success)
    ...
```

This works with any log aggregation system (ELK, CloudWatch Logs, Datadog) and requires zero additional infrastructure.

### Future: PrometheusMetricsCollector

When the ops team is ready for Prometheus, add an implementation that uses `prometheus_client`:

```python
class PrometheusMetricsCollector:
    def __init__(self) -> None:
        self._sessions_total = Counter("livoia_sessions_total", "Total sessions", ["provider", "agent"])
        self._session_duration = Histogram("livoia_session_duration_seconds", "Session duration", ["provider", "agent"])
        self._tool_duration = Histogram("livoia_tool_duration_seconds", "Tool execution duration", ["tool"])
        ...
```

No call sites change -- only the implementation wired in the lifespan handler.

## What Is Not Included in Stage 1

- **Distributed tracing** (OpenTelemetry): Valuable for multi-service debugging but not needed when the system is a single service. Add when Orchestrator integration creates cross-service calls.
- **Alerting rules**: Defined in the deployment platform (Kubernetes, Datadog, PagerDuty), not in the application.
- **Dashboards**: Created in the monitoring platform based on the structured log events and/or Prometheus metrics.
