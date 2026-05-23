# Design Directory

## Purpose

Documents architecture decisions, technical specifications, and design explorations before implementation begins.

## When to Create Design Documents

Use this directory when:
- Planning new system components or modules
- Designing integration between subsystems
- Evaluating architectural alternatives
- Specifying interfaces and data models
- Documenting design requirements and constraints

## Document Organization

See `refactor/llm-guided-sam/` for example structure.

Simple designs:
```
design/
  feature-name.md
```

Complex designs:
```
design/
  feature-name/
    main.md                  # High-level overview and objectives
    summary.md               # Design intuition and key decisions
    detailed-design.md       # Component specifications
    details-subsystem-a.md   # Deep dive into specific area
    details-subsystem-b.md   # Deep dive into another area
```

## Progressive Disclosure

Complex designs use layered documents to manage LLM context limits:
1. Main document: Problem statement, requirements, high-level approach
2. Summary document: Design intuition, key concepts, trade-offs
3. Detailed design: Component architecture, interfaces, data flows
4. Detail documents: Subsystem-specific specifications

LLMs load only relevant layers based on current task.

## Typical Content

Design documents include:
- Problem statement and objectives
- Requirements and constraints
- Architecture overview
- Component specifications
- Interface definitions
- Data model designs
- Configuration approach
- Open questions and decisions needed
- Trade-off analysis

## Design vs Implementation

Design documents specify "what" and "why", not "how":
- What components exist and their responsibilities
- Why specific architectural choices were made
- Interface contracts and data formats
- Requirements that must be satisfied

Implementation details belong in code and code comments.

## Notes

Design documents created here may inform future content in `docs/guides/` after implementation is complete and validated.
