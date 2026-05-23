#!/bin/bash
#
# Docker entrypoint script for Live Voice Agent Poc
#
# This script runs before the application starts and handles initialization tasks.

set -e

echo "[Entrypoint] Starting Live Voice Agent Poc initialization..."

# Add any initialization tasks here
# Example: Check for required environment variables
# if [ -z "${REQUIRED_VAR}" ]; then
#     echo "[Entrypoint] ERROR: REQUIRED_VAR environment variable is not set"
#     exit 1
# fi

# Execute the main application
echo "[Entrypoint] Starting application..."
exec "$@"
