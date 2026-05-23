# Redesign Consolidation - Main

## Objective

Consolidate three redesign variants into one practical direction for building a new repository from scratch, while preserving stage 1 product behavior and minimizing migration risk.

## Compared variants

- `2026-03-16-prod-redesign-claude`
- `2026-03-16-prod-redesign-gemini`
- `2026-03-16-prod-redesign-gpt`

## Final synthesis decision

Adopt a **single recommended design**:

- **Architecture style:** modular monolith (stage 1)
- **Scope discipline:** strict stage 1 parity with current web demo
- **Migration execution:** file-level inventory + phased migration
- **Operational baseline:** preserve current CI/tooling conventions

In practice:

- Use GPT variant as strategic baseline (scope, architecture boundaries, migration inventory mindset).
- Use Claude variant for implementation-level migration details and CI/doc operational completeness.
- Use Gemini variant only as roadmap input for later phases (async orchestration/tool transparency), not stage 1 implementation.

## Stage 1 scope (locked)

### Must include

- Conversation + Settings tabs.
- Google and Bedrock websocket conversation routes.
- Real-time audio + text behavior parity.
- Prompt settings sent as first websocket message and rendered server-side.
- Provider options already used by current UI.
- Structured event console feed and `/health` endpoint.

### Must exclude

- Camera/image capture and image-to-model flow.
- Prompt tab and Tool Use tab.
- User-configurable runtime tools.
- Orchestrator-agent tool execution.

## Why this synthesis is stronger than any single variant

- More executable than GPT alone (inherits Claude migration concreteness).
- More scoped than Claude alone (removes remaining stage-1 ambiguity around image/tool-future concerns).
- Lower risk and faster to deliver than Gemini-heavy future-first architecture.

## Key architectural choices

1. Keep one deployable service and one frontend bundle.
2. Preserve explicit provider routes for stage 1 (`/ws/google/...`, `/ws/bedrock/...`).
3. Isolate provider SDK translation in adapters and keep UI protocol provider-neutral.
4. Enforce typed settings + startup validation using `pydantic-settings`.
5. Keep structured logging and redaction policy from day one.
6. Keep current CI quality gates and docker deployment posture.

## Deliverables in this consolidation package

- `01-variant-comparison.md`: detailed pros/cons and tradeoff analysis.
- `02-synthesized-architecture.md`: final architecture and runtime contracts.
- `03-target-repo-tree.md`: proposed target repository tree.
- `04-file-level-migration-inventory.md`: keep/adapt/drop inventory by file.

## Implementation note

This consolidation document is intentionally opinionated: it recommends one path to reduce decision churn and make repository creation directly actionable.
