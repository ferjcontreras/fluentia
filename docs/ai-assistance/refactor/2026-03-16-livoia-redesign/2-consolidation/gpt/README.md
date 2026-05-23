# Redesign Consolidation (2026-03-16)

This package consolidates the three redesign variants in:

- `docs/ai-assistance/design/2026-03-16-prod-redesign-claude`
- `docs/ai-assistance/design/2026-03-16-prod-redesign-gemini`
- `docs/ai-assistance/design/2026-03-16-prod-redesign-gpt`

It compares strengths and weaknesses, then proposes one synthesis design suitable for a new production repository.

## Reading order

1. `00-main.md` - Executive synthesis and final recommendation
2. `01-variant-comparison.md` - Side-by-side analysis (pros/cons)
3. `02-synthesized-architecture.md` - Chosen architecture and runtime contracts
4. `03-target-repo-tree.md` - Proposed target repository tree
5. `04-file-level-migration-inventory.md` - Keep/adapt/drop migration inventory

## Consolidation principles

- Keep stage 1 scope tightly aligned to current web demo parity.
- Exclude camera/image support in stage 1.
- Prefer one clear architecture (no A/B alternatives).
- Keep the migration plan concrete at file level.
- Preserve current quality and CI conventions to reduce delivery risk.
