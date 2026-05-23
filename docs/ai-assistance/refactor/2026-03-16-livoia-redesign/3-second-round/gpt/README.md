# Production Redesign - 2026-03-17

This package defines a production-oriented redesign for a new repository that delivers stage 1 parity with the current live voice web experience and establishes a clear path to support multiple agent use cases over time.

## Reading order

1. `main.md` - scope, goals, requirements, non-goals
2. `agent-use-cases.md` - stage 1 and future agent/use-case model
3. `target-repo-tree.md` - proposed new repository structure
4. `architecture.md` - architecture, boundaries, runtime contracts
5. `runtime-flows.md` - end-to-end session and interaction flows
6. `configuration-and-secrets.md` - env/configuration and secret strategy
7. `ci-cd-and-quality.md` - CI/CD and quality baseline
8. `migration-inventory.md` - file-level keep/adapt/drop migration inventory
9. `roadmap.md` - staged delivery roadmap

## Deliverable intent

- This is design documentation, not implementation.
- It is intended to be directly actionable for creating a new production repository.
- It provides strict stage 1 boundaries while defining safe extension points for future agent types.
