# AI Assistance Documentation

## Purpose

This directory contains markdown documents created by AI coding assistants (such as Claude Code) during development tasks. Documents serve as structured records of analysis, design decisions, implementation plans, and progress tracking.

## Directory Structure

- **analysis/**: Investigation and exploration of codebase areas or technical questions
- **code-review/**: Review findings and improvement suggestions for code changes
- **debug/**: Debugging processes, root cause analysis, and fix documentation
- **design/**: Architecture decisions, technical specifications, and design explorations
- **feature/**: Feature planning, implementation tracking, and completion documentation
- **refactor/**: Refactoring plans, progress tracking, and validation records

## Document Organization

Documents are organized by task type, then by feature or topic area. Complex tasks typically include multiple documents at different abstraction levels.

Example structure:
```
design/
  feature-name/
    main.md              # High-level overview
    detailed-design.md   # Detailed specifications
    details-*.md         # Specific subsystem details
```

## Usage Pattern

AI assistants create documents to:
1. Record design decisions and rationale
2. Track implementation progress through multi-step tasks
3. Enable progressive disclosure of complexity across sessions
4. Maintain context within LLM token limits
5. Provide searchable history of development reasoning

## Document Types by Task Complexity

**Simple tasks**: Single document with findings or analysis

**Complex tasks**: Multiple documents including:
- High-level plans
- Detailed specifications
- Progress tracking (PROGRESS.md, README.md)
- Phase-specific plans (numbered files)

## Notes

These documents complement, not replace, standard documentation in `docs/guides/`. AI assistance documents capture development process; guides document final architecture and usage.

This structure will evolve based on observed patterns and effectiveness.
