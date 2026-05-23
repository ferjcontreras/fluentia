# Feature Directory

## Purpose

Documents feature planning, implementation tracking, and completion records for new functionality.

## When to Create Feature Documents

Use this directory when:
- Planning implementation of new features
- Tracking multi-step feature development
- Documenting feature completion and validation
- Recording design decisions made during implementation
- Managing feature scope and requirements

## Document Organization

Simple features (completed in single session):
```
feature/
  feature-name-implementation.md
```

Complex features (multi-session or multi-phase):
```
feature/
  feature-name/
    plan.md          # Implementation plan
    progress.md      # Status tracking
    phase-*.md       # Phase-specific details
    completion.md    # Final validation
```

## Typical Content

Feature documents include:
- Feature description and requirements
- Implementation plan with steps or phases
- Progress tracking (completed steps, current work, remaining work)
- Design decisions and rationale
- Test coverage and validation
- Known limitations or future enhancements
- Completion criteria

## Feature vs Design

Feature documents focus on implementation:
- Step-by-step implementation plans
- Progress tracking across sessions
- Validation and testing
- Practical decisions during development

Design documents (in `design/`) specify architecture before implementation begins.

## Progress Tracking

Use PROGRESS.md or progress.md to track:
- Current phase or step
- Completed work with validation status
- Current work in progress
- Remaining work
- Blockers or questions
- References to design documents

## Notes

Feature documents enable continuation across multiple sessions by providing clear progress tracking and context. They supplement commit messages and pull request descriptions with detailed implementation narrative.
