# Main Design

## Problem statement

The current web demo proves live bidirectional voice interaction with two providers (Google Gemini and AWS Bedrock), but it is organized as a PoC. We need a production-ready redesign in a new repository that keeps stage 1 behavior, improves maintainability and operational quality, and remains extensible for future prompt/tool transparency and user-configurable tool use.

## Stage 1 functional scope (must have)

1. Web app with two tabs:
   - `Conversation`
   - `Settings`
2. Real-time bidirectional conversation over WebSockets:
   - Google endpoint
   - Bedrock endpoint
3. Text input + live audio input/output behavior equivalent to current demo.
4. Runtime prompt configuration from settings fields and injection at session start.
5. Provider selection and provider-specific runtime flags needed in stage 1.
6. Event transparency via structured event console/log feed in the UI.
7. Health endpoint for platform checks.

## Explicit stage 1 non-goals

- Camera/image capture and image-to-model flow.
- End-user configurable tool registry/runtime tool execution.
- Prompt visualization tab (`Prompt`).
- Tool transparency tab (`Tool use`).
- Kubernetes manifests (managed in another project).

## Production quality requirements

- Strong package boundaries and clear ownership of responsibilities.
- Typed configuration and fail-fast startup validation.
- Environment-variable first secrets/config strategy for container deployment.
- Test strategy split by layers (`unit`, `integration`, `e2e`).
- CI gates aligned with current standards (`ruff`, `mypy`, `pylint`, `pytest`, `tox`).
- Docker build path first-class and reproducible.
- Structured logging and basic observability readiness.

## Design constraints

- Preserve behavior users already rely on in the current web demo.
- Export only the code needed for stage 1 scope.
- Keep compatibility with current organizational CI conventions (GitLab-based jobs).
- Keep docs structure consistent with the current repo and preserve `docs/ai-assistance` content recursively in the new repository.

## Design principles

- Prefer a modular monolith for stage 1 to maximize delivery speed and coherence.
- Separate provider-neutral session orchestration from provider-specific adapters.
- Keep UI protocol explicit and versionable.
- Design extension points now for future tool orchestration without forcing early complexity.
