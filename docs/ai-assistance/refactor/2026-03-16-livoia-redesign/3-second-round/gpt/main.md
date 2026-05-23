# Main Design

## Problem statement

The current repository demonstrates successful real-time bidirectional voice interaction in a web demo, but it is structured as a PoC with mixed concerns and extra code paths not required for production delivery. We need a new production-ready repository with strong boundaries, operational reliability, and clear extensibility.

## Product direction

The platform should support multiple conversational agents over time, starting with one concrete use case and evolving safely.

- **Stage 1 use case:** Interviewer Agent
- **Future use cases:** Scheduler Agent, Avature Assistant Agent, and other domain-specific assistants

The redesign must make adding new use cases incremental, not architectural rework.

## Stage 1 functional scope (must have)

1. Web app with two tabs:
   - `Conversation`
   - `Settings`
2. Real-time bidirectional conversation over WebSockets:
   - Google endpoint
   - Bedrock endpoint
3. Text input plus live audio input/output behavior equivalent to the current web experience.
4. Runtime prompt configuration from settings fields, injected at session start.
5. Provider selection plus provider-specific runtime flags needed in stage 1.
6. Event transparency via structured event console/log feed in the UI.
7. Health endpoint for platform checks.
8. Agent/use-case selection contract designed in backend, but only Interviewer enabled in stage 1.

## Explicit stage 1 non-goals

- Camera/image capture and image-to-model flow.
- End-user configurable tool registry/runtime tool execution.
- Prompt visualization tab (`Prompt`).
- Tool transparency tab (`Tool use`).
- External orchestrator-agent runtime calls.
- Kubernetes manifests (managed in another project).

## Production quality requirements

- Strong package boundaries and clear ownership by layer.
- Typed configuration with fail-fast startup validation.
- Environment-variable-first secrets/config strategy.
- Test strategy split by layers (`unit`, `integration`, `e2e`).
- CI gates aligned with current standards (`ruff`, `mypy`, `pylint`, `pytest`, `tox`).
- Docker build path first-class and reproducible.
- Structured logging and observability readiness.
- Session-scoped failure isolation (no process-wide crash from one session).

## Design constraints

- Preserve behavior users already rely on in the current web flow.
- Export only code needed for stage 1 scope.
- Keep compatibility with organizational GitLab CI conventions.
- Preserve `docs/ai-assistance` content recursively in the new repository.
- Keep stage 1 implementation small enough to ship quickly while leaving explicit extension points.

## Design principles

- Prefer a modular monolith for stage 1 speed and coherence.
- Separate provider-neutral session orchestration from provider-specific adapters.
- Treat agent/use-case behavior as a typed profile contract, not hard-coded branching.
- Keep UI protocol explicit, provider-neutral, and versionable.
- Design extension points now for future tools and multi-agent behavior without forcing early complexity.
