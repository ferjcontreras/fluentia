# Livoia Production Redesign Specification

**Date**: 2026-03-17
**Status**: Proposed

## Purpose

This specification defines the architecture, implementation plan, and delivery roadmap for a new production-grade repository replacing the current Live Voice Agent PoC. The new system provides real-time bidirectional voice conversations over WebSocket, supporting multiple voice providers and multiple agent types.

## Scope

**In scope (Stage 1)**:
- Real-time voice conversations with Google Gemini and AWS Bedrock Nova Sonic
- Interviewer agent (current use case) as the first agent definition
- Browser-based web UI with prompt customization
- Production-grade CI/CD, Docker, structured logging, health checks
- Extensible architecture for future agents and tools

**Out of scope (Stage 1)**:
- LLM text generation, embedding, and caching features from the PoC
- CLI-based voice agents
- Camera/image capabilities
- Authentication and authorization (handled at infrastructure level)
- Redis or any external state store

## Documents

| File | Description |
|------|-------------|
| [01-architecture.md](01-architecture.md) | Package structure, dependency flow, layer responsibilities |
| [02-providers.md](02-providers.md) | Provider abstraction, Google and Bedrock adapters |
| [03-session-and-events.md](03-session-and-events.md) | WebSocket session management, event protocol, protocol versioning |
| [04-agents-and-prompts.md](04-agents-and-prompts.md) | Agent definition framework, prompt rendering, multi-agent support |
| [05-tools.md](05-tools.md) | Tool framework, async state machine, provider-specific formatting |
| [06-configuration.md](06-configuration.md) | Environment variables, Pydantic settings, secret handling |
| [07-frontend.md](07-frontend.md) | Web UI, AudioWorklet, static file serving |
| [08-observability.md](08-observability.md) | Structured logging, health endpoints, metrics hooks |
| [09-ci-cd.md](09-ci-cd.md) | Pipeline, Docker, pre-commit, quality gates |
| [10-migration-plan.md](10-migration-plan.md) | Phased migration with validation checkpoints |
| [11-roadmap.md](11-roadmap.md) | Post-launch evolution phases |
