# Production Redesign (GPT) - 2026-03-16

This package defines a production-oriented redesign for a new repository that preserves stage 1 functionality of the current web demo (Google + Bedrock live voice conversation, prompt configuration, conversation/settings UI), while intentionally excluding camera/image support.

## Reading order

1. `main.md` - scope, requirements, non-goals
2. `target-repo-tree.md` - proposed structure for the new repo
3. `architecture.md` - recommended architecture and component boundaries
4. `runtime-flows.md` - key runtime/session flows
5. `configuration-and-secrets.md` - environment and config strategy
6. `ci-cd-and-quality.md` - CI/CD and engineering quality baseline
7. `migration-inventory.md` - keep/adapt/drop decisions from current repo
8. `roadmap.md` - staged extension plan after stage 1

## Deliverable intent

- This is design documentation, not implementation.
- It is intended to be directly actionable for creating a new production repository.
- It includes explicit extension points for future Prompt/Tool transparency and tool orchestration.
