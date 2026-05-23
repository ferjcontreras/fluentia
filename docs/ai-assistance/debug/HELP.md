# Debug Directory

## Purpose

Documents debugging processes, root cause analysis, and fix validation for bugs or unexpected behavior.

## When to Create Debug Documents

Use this directory when:
- Investigating non-trivial bugs requiring multiple investigation steps
- Performing root cause analysis for production issues
- Debugging complex interactions between components
- Tracking failed attempts and successful solutions
- Documenting reproduction steps and test cases

## Document Organization

Single documents for isolated bugs:
```
debug/
  bug-issue-456.md
  crash-in-component-x.md
```

Multiple documents for complex debugging:
```
debug/
  production-issue-789/
    investigation.md
    root-cause-analysis.md
    fix-validation.md
```

## Typical Content

Debug documents include:
- Bug description and symptoms
- Reproduction steps
- Investigation process (what was checked, what was ruled out)
- Root cause analysis
- Proposed fix with rationale
- Validation tests performed
- Related issues or similar bugs

## Investigation Process

Effective debug documents track:
1. Initial observations and error messages
2. Hypotheses tested
3. Data gathered (logs, stack traces, variable states)
4. Code paths examined
5. Root cause identification
6. Fix implementation
7. Validation results

## Notes

Debug documents capture investigation process and reasoning. They complement issue tracker entries but provide more detailed technical analysis. For simple bugs, issue tracker alone may be sufficient.
