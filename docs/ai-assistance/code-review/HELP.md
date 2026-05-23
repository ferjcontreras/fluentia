# Code Review Directory

## Purpose

Documents findings, suggestions, and tracking for code review tasks.

## When to Create Code Review Documents

Use this directory when:
- Reviewing pull requests or branches
- Conducting architecture reviews
- Analyzing code quality or technical debt
- Evaluating security implications
- Assessing test coverage

## Document Organization

Single documents for individual reviews:
```
code-review/
  pr-123-review.md
  branch-feature-x-review.md
```

Multiple documents for large-scale reviews:
```
code-review/
  refactor-y/
    summary.md
    security-findings.md
    performance-findings.md
    test-coverage-analysis.md
```

## Typical Content

Code review documents include:
- Review scope and objectives
- Findings organized by severity or category
- Specific code references (file:line)
- Improvement suggestions with examples
- Questions for code author
- Approval status or blocking issues

## Review Categories

Common review focuses:
- Correctness: Logic errors, edge cases, error handling
- Performance: Algorithmic complexity, resource usage
- Security: Vulnerabilities, input validation, authorization
- Maintainability: Code clarity, documentation, test coverage
- Architecture: Design patterns, coupling, separation of concerns

## Notes

Code review documents record detailed findings. Summary findings should be communicated to the author through the project's code review process (pull request comments, issue tracker).
