# Docker Local Deployment

This tutorial describes how to build and run Fluentia locally using Docker. This approach packages the application and its dependencies into a container, which avoids manual Python environment setup.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed and running
- [Docker Compose](https://docs.docker.com/compose/install/) (included with Docker Desktop)
- API credentials for at least one provider (Google Gemini or AWS Bedrock)

## Setup

### 1. Create Environment File

Copy the example configuration:

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```bash
# Application settings
FLUENTIA_LOG_LEVEL=INFO
FLUENTIA_DEFAULT_PROVIDER=google
FLUENTIA_DEFAULT_AGENT=interviewer

# Google Gemini provider
GOOGLE_API_KEY=your-google-api-key-here

# AWS Bedrock provider
BEDROCK_REGION=us-east-1

# AWS credentials (used by the Bedrock SDK directly)
# Obtain these from https://aws-global.example.com/
AWS_ACCESS_KEY_ID=your-aws-access-key-here
AWS_SECRET_ACCESS_KEY=your-aws-secret-key-here
AWS_SESSION_TOKEN=your-aws-session-token-here
```

You only need credentials for the provider you plan to use.

### 2. Build the Docker Image

```bash
docker compose build
```

The build uses a multi-stage Dockerfile:

1. **Builder stage**: Installs `uv`, syncs dependencies, builds a Python wheel
2. **Production stage**: Installs the wheel into a minimal Python 3.13 image, runs as non-root user `fluentia` (UID 1000)

### 3. Start the Container

```bash
docker compose up
```

The container starts a single uvicorn worker on port 8000. You should see:

```
fluentia-1  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
fluentia-1  | INFO:     Application startup complete.
```

To run in the background:

```bash
docker compose up -d
```

### 4. Open the Web UI

Navigate to [http://localhost:8000](http://localhost:8000) in your browser.

## Verifying the Deployment

### Health Check

The container includes a built-in health check that polls `/health` every 30 seconds. Check status with:

```bash
docker compose ps
```

The `STATUS` column should show `healthy` after the 10-second start period.

You can also query the endpoints directly:

```bash
# Liveness probe
curl http://localhost:8000/health

# Readiness probe (shows provider availability)
curl http://localhost:8000/ready
```

### Logs

View container logs:

```bash
docker compose logs -f
```

Logs use structured JSON format via `structlog`. To increase verbosity, set `FLUENTIA_LOG_LEVEL=DEBUG` in your `.env` file.

## Docker Compose Configuration

The `docker-compose.yml` file defines a single service:

```yaml
services:
  fluentia:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLUENTIA_LOG_LEVEL=DEBUG
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - BEDROCK_REGION=us-east-1
      - BEDROCK_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - BEDROCK_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    volumes:
      - ./src:/app/src  # Hot reload (development only)
```

The `volumes` mount enables source code changes to be reflected without rebuilding. Remove this line for production-like behavior.

## Development Workflow

For iterative development with Docker:

1. Start the container: `docker compose up`
2. Edit source files locally (changes reflected via volume mount)
3. The server does not auto-reload inside Docker by default. Restart the container to apply changes: `docker compose restart`

For faster iteration, consider running the server directly with `uv run` instead of Docker (see the [web demo tutorial](voice-interview-agent-web-demo.md)).

## Stopping and Cleanup

```bash
# Stop the container
docker compose down

# Stop and remove built images
docker compose down --rmi local

# Remove all Docker artifacts (images, volumes, cache)
docker compose down --rmi all --volumes
```

## Troubleshooting

### Port Already in Use

If port 8000 is occupied, change the port mapping in `docker-compose.yml`:

```yaml
ports:
  - "9000:8000"
```

Then access the UI at `http://localhost:9000`.

### Container Exits Immediately

Check logs for startup errors:

```bash
docker compose logs
```

Common causes:
- Invalid Python syntax or missing dependencies (rebuild with `docker compose build --no-cache`)
- Missing required configuration (check `.env` file)

### Health Check Failing

If the container status shows `unhealthy`:

```bash
# Check application logs
docker compose logs fluentia

# Test health endpoint manually
docker compose exec fluentia python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read())"
```

### AWS Credentials Not Working

AWS session credentials from Avature's portal expire after a few hours. If Bedrock connections fail:

1. Obtain fresh credentials from [https://aws-global.example.com/](https://aws-global.example.com/)
2. Update `.env` with the new values
3. Restart: `docker compose restart`
