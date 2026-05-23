# --- Builder stage ---
FROM python:3.13-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv

# Copy dependency and build metadata files first (layer caching)
COPY pyproject.toml uv.lock README.md ./

# Install production dependencies only
RUN uv sync --no-dev --frozen

# Copy source code
COPY src/ src/

# Build wheel
RUN uv build --wheel


# --- Production stage ---
FROM python:3.13-slim

# Create non-root user
RUN groupadd -r fluentia && useradd -r -u 1000 -g fluentia -m -d /home/fluentia fluentia

WORKDIR /app

# Install runtime dependencies (curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install wheel from builder
COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HOME=/home/fluentia

# Expose port
EXPOSE 8000

# Switch to non-root user
USER fluentia

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run with single uvicorn worker (WebSocket sessions are stateful)
CMD ["uvicorn", "fluentia.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
