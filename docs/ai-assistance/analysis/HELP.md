# Analysis Directory

## Purpose

Documents investigation and exploration of codebase areas, technical questions, or architectural concerns.

## When to Create Analysis Documents

Use this directory when:
- Investigating how a specific system component works
- Exploring trade-offs between technical approaches
- Analyzing performance characteristics or bottlenecks
- Understanding dependencies or integration points
- Researching third-party libraries or tools

## Document Organization

Single documents for focused investigations:
```
analysis/
  component-name-investigation.md
  performance-analysis-feature-x.md
```

Multiple documents for complex explorations:
```
analysis/
  topic-area/
    overview.md
    subsystem-a-details.md
    subsystem-b-details.md
```

## Progressive Disclosure

Complex analyses benefit from layered documents:
1. Overview document with high-level findings
2. Detail documents for specific areas requiring deep exploration
3. Allows LLMs to load relevant context without exceeding token limits

## Typical Content

Analysis documents include:
- Investigation goals and questions
- Findings organized by topic
- Code references with file paths and line numbers
- Trade-off comparisons
- Open questions requiring decisions
- References to related codebase areas

## Notes

Analysis documents capture understanding gained during exploration. They are not implementation specifications - those belong in `design/`.
