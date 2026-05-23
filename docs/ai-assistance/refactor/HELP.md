# Refactor Directory

## Purpose

Documents refactoring plans, progress tracking, and validation for code restructuring or architecture changes.

## When to Create Refactor Documents

Use this directory when:
- Planning restructuring of existing code
- Documenting multi-phase refactoring efforts
- Tracking migration from old to new architecture
- Recording refactoring decisions and validation
- Managing backward compatibility during transitions

## Document Organization

See `refactor/llm-guided-sam/` for example structure.

Simple refactorings:
```
refactor/
  component-name-refactor.md
```

Complex refactorings:
```
refactor/
  refactor-name/
    README.md            # Overview and context
    00-high-level-plan.md
    01-phase-1-plan.md
    02-phase-2-plan.md
    PROGRESS.md          # Current status
```

## Typical Content

Refactor documents include:
- Motivation and objectives
- Current architecture and limitations
- Target architecture and benefits
- Implementation phases with steps
- Validation criteria per phase
- Progress tracking
- Backward compatibility approach
- Migration path for existing code

## Progressive Implementation

Complex refactorings benefit from phase-based planning:
1. High-level plan: All phases, dependencies, success criteria
2. Phase plans: Detailed steps, validation, prerequisites
3. Progress tracking: Current phase, completed work, remaining work

Each phase is small enough to complete and validate independently.

## Refactor vs Feature

Refactoring documents focus on restructuring existing functionality:
- No new user-facing features
- Same external behavior with improved internal structure
- Migration path from old to new implementation
- Validation that behavior is preserved

Feature documents (in `feature/`) focus on adding new functionality.

## Progress Tracking

PROGRESS.md documents:
- Current phase and step
- Completed phases with validation status
- Current work in progress
- Remaining phases
- Key decisions made during implementation
- References to design documents

## Notes

Refactoring documents enable safe, incremental restructuring across multiple sessions. They provide clear checkpoints and validation criteria to ensure correctness at each step.
