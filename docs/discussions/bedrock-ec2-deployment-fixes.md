# Bedrock EC2 Deployment Fixes

This document records two issues discovered during EC2 deployment of the Bedrock provider and how they were resolved. Both fixes drew on the legacy codebase (`src_legacy/`) and the AWS Nova Sonic reference implementation.

## Issue 1: Credential resolver fails on EC2 with IAM role

### Problem

The Bedrock client used `EnvironmentCredentialsResolver` which only reads `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` from environment variables. On an EC2 instance with an IAM instance profile, credentials are provided by the Instance Metadata Service (IMDS), not env vars. The container failed at import time with:

```
ModuleNotFoundError: No module named 'smithy_aws_core.aio.credentials'
```

The original tutorial (Step 8) instructed users to manually replace the resolver with `DefaultIdentityResolverConfiguration` from `smithy_aws_core.aio.credentials`, but that module does not exist in the installed package.

### Root cause

The tutorial referenced a non-existent class. The `smithy_aws_core` package provides individual resolvers (`EnvironmentCredentialsResolver`, `IMDSCredentialsResolver`) and a `ChainedIdentityResolver` from `smithy_core.aio.identity`, but no `DefaultIdentityResolverConfiguration`.

### Solution

Created `src/fluentia/providers/bedrock/auth.py`, adapted from the legacy `src_legacy/livoia/clients/speech/bedrock_auth.py`. The module uses `ChainedIdentityResolver` to try env vars first and fall back to IMDS:

```python
from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver
from smithy_aws_core.identity.imds import IMDSCredentialsResolver
from smithy_core.aio.identity import ChainedIdentityResolver
from smithy_http.aio.aiohttp import AIOHTTPClient

def _create_sigv4_credentials_resolver():
    env_resolver = EnvironmentCredentialsResolver()
    http_client = AIOHTTPClient()
    imds_resolver = IMDSCredentialsResolver(http_client)
    return ChainedIdentityResolver([env_resolver, imds_resolver])
```

Key details:
- `IMDSCredentialsResolver` requires an `http_client` argument (`AIOHTTPClient` instance)
- `AIOHTTPClient()` requires a running event loop, which is available because `_initialize_bedrock_client` is called from the async `connect()` method
- `ChainedIdentityResolver` tries resolvers in order and uses the first one that succeeds
- This supports both local development (env vars) and EC2 deployment (IMDS) transparently

The tutorial's Step 8 (manual code edit) was removed since the fix is now built into the codebase. Steps were renumbered accordingly.

### Files changed

- `src/fluentia/providers/bedrock/auth.py` — new module
- `src/fluentia/providers/bedrock/client.py` — replaced inline `EnvironmentCredentialsResolver` with `create_bedrock_config()` call
- `docs/tutorials/ec2-deployment.md` — removed Step 8, renumbered Steps 9-11 to 8-10

---

## Issue 2: Bedrock tools block the event loop

### Problem

When the Nova Sonic model requested a tool (e.g., `get_date_time`), the Bedrock session appeared to hang. The server logs showed a 55-second inactivity timeout:

```
InternalErrorCode=532::Timed out waiting for audio bytes or interactive content.
Please ensure gaps between audio bytes and interactive content are less than 55 seconds.
```

### Root cause

In `provider.py`, the `downstream()` coroutine **awaited** `_handle_tool_call()` synchronously:

```python
async for event in client.receive_events():
    if isinstance(event, _InternalToolUseEvent):
        await self._handle_tool_call(client, event, session_context)  # BLOCKS
```

While `_handle_tool_call` was running (executing the tool and sending the result), the downstream loop was paused. No audio or text events from Bedrock could be emitted to the WebSocket client. Although the upstream audio and response processing tasks continued independently, the model could be generating audio ("Let me check that for you...") that never reached the client. If the tool took any noticeable time, Bedrock would time out.

### How the AWS reference handles it

The AWS `nova_sonic_tool_use.py` reference implementation uses fire-and-forget via `asyncio.create_task()` (line 688):

```python
task = asyncio.create_task(self._execute_tool_and_send_result(
    tool_name, tool_content, tool_use_id, tool_content_name))
self.pending_tool_tasks[tool_content_name] = task
```

The response processing loop returns immediately and keeps processing events while the tool runs in the background.

### Solution

Changed the downstream loop to spawn tool handling as a background task:

```python
async for event in client.receive_events():
    if isinstance(event, _InternalToolUseEvent):
        task = asyncio.create_task(
            self._handle_tool_call(client, event, session_context)
        )
        pending_tool_tasks.add(task)
        task.add_done_callback(pending_tool_tasks.discard)
```

Also added:
- Tracking of pending tool tasks in a `set[asyncio.Task]` for cleanup on session end
- A catch-all exception handler in `_handle_tool_call` so errors in background tasks are logged and an error result is sent back to Bedrock (matching the reference implementation's error handling pattern)

### Files changed

- `src/fluentia/providers/bedrock/provider.py` — non-blocking tool handling, task tracking, error recovery

---

## Issue 3: Standard library logging silently dropped in Docker

### Problem

After deploying fixes for Issues 1 and 2, diagnostic `logger.info(...)` calls added to the Bedrock provider produced no output in container logs. Bedrock conversations worked (audio flowed, the model responded), but zero log lines from `fluentia.providers.*`, `fluentia.session.*`, or `fluentia.tools.*` appeared. Only structlog JSON messages (metrics) and uvicorn access logs were visible.

This made it impossible to diagnose whether tools were being sent to the model.

### Root cause

`configure_logging()` in `src/fluentia/observability/logging.py` only configured **structlog** (via `structlog.configure(...)` with `PrintLoggerFactory`). It never attached a handler to the standard library `logging` root logger.

All provider, session, and client code uses:
```python
logger = logging.getLogger(__name__)
logger.info("Nova Sonic stream initialized")
```

Without a root handler, these calls were silently dropped. Only code using `structlog.get_logger()` (metrics, config summary) produced output.

### Solution

Added a `StreamHandler` with `structlog.stdlib.ProcessorFormatter` to the root logger so that standard library `logging` calls produce the same JSON format as structlog:

```python
root = logging.getLogger()
root.setLevel(numeric_level)
root.handlers.clear()
handler = logging.StreamHandler()
handler.setFormatter(structlog.stdlib.ProcessorFormatter(
    processor=structlog.processors.JSONRenderer(),
    foreign_pre_chain=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        mask_sensitive_values,
    ],
))
root.addHandler(handler)
```

### Files changed

- `src/fluentia/observability/logging.py` — added root logger handler configuration

---

## Key takeaways

1. **`smithy_aws_core` credential resolvers**: Use `ChainedIdentityResolver` with `[EnvironmentCredentialsResolver, IMDSCredentialsResolver]` for code that must work both locally and on EC2. `IMDSCredentialsResolver` requires an `AIOHTTPClient` instance.

2. **Nova Sonic tool handling must be non-blocking**: The bidirectional HTTP/2 stream has a 55-second inactivity timeout. Tool execution must not block the event processing loop, or the stream will time out. Always use `asyncio.create_task` for tool execution.

3. **Standard library logging requires explicit handler setup**: Configuring structlog alone is not enough. If application code uses `logging.getLogger(__name__)`, the root logger needs a handler. Use `structlog.stdlib.ProcessorFormatter` to unify output format.

4. **Legacy codebase as reference**: The `src_legacy/livoia/clients/speech/bedrock_auth.py` module had the correct credential chain pattern. The AWS `nova_sonic_tool_use.py` sample confirmed the fire-and-forget tool handling pattern.
