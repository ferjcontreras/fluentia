# Production Redesign (2026-03-16)

Design documentation for migrating the Livoia web demo from PoC to a production-ready repository.

## Documents

| # | Document | Description |
|---|----------|-------------|
| 00 | [main.md](00-main.md) | Problem statement, objectives, what to include/exclude |
| 01 | [architecture.md](01-architecture.md) | Package layout, layer design, dependency flow |
| 02 | [backend.md](02-backend.md) | FastAPI app, providers, WebSocket protocol |
| 03 | [frontend.md](03-frontend.md) | UI design, tabs, audio architecture |
| 04 | [tools.md](04-tools.md) | Tool framework, future tools (Orchestrator, web search) |
| 05 | [configuration.md](05-configuration.md) | Env vars, Docker, Kubernetes |
| 06 | [ci-cd.md](06-ci-cd.md) | CI pipeline, code quality, testing strategy |
| 07 | [documentation.md](07-documentation.md) | Docs structure, what to copy/adapt/create |
| 08 | [migration-plan.md](08-migration-plan.md) | Step-by-step migration phases |

## Reading Order

1. Start with **00-main.md** for the full picture
2. Read **01-architecture.md** for the new project structure
3. Read other documents based on what you're implementing

## Status

- [x] Initial design complete
- [ ] Design review
- [ ] Implementation started
