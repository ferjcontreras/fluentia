#!/bin/bash
#
# Health check script for Live Voice Agent Poc
#
# This script performs a health check on the running application.

set -e

# Default values
HOST="${FLUENTIA_API__HOST:-0.0.0.0}"
PORT="${FLUENTIA_API__PORT:-8000}"
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-/health}"

# Perform health check
curl -f "http://localhost:${PORT}${HEALTH_ENDPOINT}" || exit 1
