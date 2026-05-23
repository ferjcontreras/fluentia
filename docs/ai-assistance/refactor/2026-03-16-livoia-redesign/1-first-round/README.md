# First Round — Independent Redesign Proposals

Each AI assistant independently produced a production redesign specification for the Livoia web demo, given the same requirements and full codebase context. No AI saw another's output at this stage.

## Proposals

| Directory | AI | Key Characteristics |
|-----------|----|---------------------|
| [`claude/`](claude/) | Claude Opus | Focused and pragmatic — minimal viable production system with a flat `src/livoia/` layout, unified WebSocket endpoint, and clear migration path |
| [`gpt/`](gpt/) | GPT-4o | Broadest scope — 5-phase roadmap, protocol versioning, detailed event taxonomy, and forward-looking extensibility |
| [`gemini/`](gemini/) | Gemini 2.5 Pro | Domain-driven — enterprise infrastructure focus (Kubernetes, multi-stage Docker), async tool orchestration, and strict statelessness |
