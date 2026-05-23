# Codemap: Hierarchical Navigation for AI Coding Agents

## Problem

When an AI coding agent begins a task in an unfamiliar or partially familiar repository, it must locate the relevant files before it can do useful work. The typical approach is a broad search: glob for file patterns, grep for keywords, and read files until the right area is found. This has two costs:

1. **Token waste**: The agent reads many irrelevant files before finding the right one.
2. **Missed context**: Broad searches may not surface files that are relevant but use different terminology than the search query.

For example, if asked "how does the system choose which LLM provider to use?", an agent might search for "provider", "select", or "choose" across the codebase. The answer is in the discriminated union pattern in `modules/llm_caller.py`, but the code uses the term "discriminator" and `Field(discriminator="provider")`, which may not match the agent's initial search terms.

## Approach

The codemap is a hierarchical navigation structure that works like a search tree with natural-language keys. At each level, semantic descriptions help the agent decide which branch to follow, narrowing from the entire repository to the exact file and line number in two steps.

### Structure

```
Level 0 (CODEMAP.md)          ~130 lines    "Which area of the repo?"
    |
Level 1 (codemap/*.md)        ~70-130 lines  "Which file, class, or function?"
    |
Level 2 (actual source code)  varies          "What are the exact details?"
```

**Level 0** is a single index file with 11 entries. Each entry has:
- A descriptive title
- A "When to look here" annotation listing the kinds of tasks and questions that point to this area
- Key concepts mentioned in this area
- A pointer to the Level 1 file

**Level 1** files (one per area) contain:
- A brief overview of the area's purpose
- Subsections for each component
- File paths with line numbers for classes and key functions
- Cross-references to related areas

**Level 2** is the source code itself. No additional documentation is needed at this level.

### Navigation Cost

For any given task, the agent reads:
- CODEMAP.md (~130 lines) to pick an area
- One L1 file (~100 lines) to find specific file:line references
- The targeted source file

Total navigation overhead: approximately 230 lines. This replaces an unbounded search that might read thousands of lines across many files.

### Design Decisions

**Why separate files instead of one large document?**
A single document containing all L1 detail would exceed 1,000 lines. The agent would need to read content about testing, Docker, and the web demo when looking for LLM client details. Separate files let the agent read only the relevant section.

**Why "When to look here" annotations?**
These serve as the semantic matching keys. The agent compares the user's request against these descriptions to decide which branch to follow. Without them, the agent must infer relevance from titles alone, which is less reliable.

**Why file:line references?**
Line numbers let the agent jump directly to a class or function definition. Without them, the agent would need to grep or scan the file after opening it. Line numbers may drift as code changes, but approximate locations (within a few lines) are still useful for orientation.

**Why a cross-reference table in CODEMAP.md?**
Some tasks span multiple areas. "Add a new LLM provider" requires changes in both the clients layer and the modules layer. The cross-reference table at the bottom of CODEMAP.md handles these multi-area tasks by listing the recommended reading order.

## Maintenance

The codemap is only useful if it reflects the current state of the codebase. Stale references (wrong line numbers, missing new components, outdated descriptions) reduce trust and may misdirect agents.

### When to Update

Update the codemap when any of the following changes occur:

- **New file or module added**: Add it to the relevant L1 file with a description and line references.
- **File moved or renamed**: Update the path in the L1 file.
- **Class or function added/removed/renamed**: Update the L1 file's references.
- **New area or subsystem introduced**: Add a new L0 entry in CODEMAP.md and create a new L1 file.
- **Architecture pattern changed**: Update `architecture.md` and any affected L1 files.
- **Significant line number drift**: Re-check line numbers if a file has been heavily modified. Small drift (a few lines) is acceptable; large drift (50+ lines) should be corrected.

### When Not to Update

- Minor edits within existing functions (line numbers may shift slightly, but this is tolerable).
- Documentation-only changes that do not affect code structure.
- Test additions that follow existing patterns (the testing L1 file describes the pattern, not individual test files).

### How to Update

1. Read the affected L1 file.
2. Edit the relevant section to reflect the change.
3. If a new area was introduced, add an entry to CODEMAP.md and create a new L1 file following the existing format.
4. Verify that file:line references in the edited L1 file are approximately correct.

### Staleness Detection

An agent can detect that the codemap may be stale if:
- A referenced file path does not exist.
- A class or function is not found near the referenced line number.
- The L1 file does not mention a component the agent found through other means.

In these cases, the agent should update the codemap as part of its work.

## Applying to Other Repositories

This approach is not specific to this project. The structure can be applied to any repository where AI coding agents need to navigate unfamiliar code.

### Prerequisites

The repository should have:
- A clear directory structure (flat or nested).
- Identifiable areas of responsibility (e.g., by directory, module, or layer).
- Enough code that a flat list of files is insufficient for navigation (roughly 20+ source files or 3+ distinct subsystems).

For smaller repositories (under 10 files), a CODEMAP is unnecessary. A well-written CLAUDE.md with a project structure section is sufficient.

### Steps to Create a Codemap

1. **Identify areas**: Group the repository's content into 5-15 areas based on responsibility. Too few areas make L0 too vague; too many make it a flat list that defeats the purpose of hierarchical navigation.

2. **Write L0 entries**: For each area, write a title, a "When to look here" description, and list the key concepts. The "When to look here" text should use the vocabulary a user would use when asking about that area, not just internal code terminology.

3. **Write L1 files**: For each area, list the components (files, classes, functions) with brief descriptions and file:line references. Include cross-references to related areas.

4. **Add a cross-reference table**: At the bottom of CODEMAP.md, list common multi-area tasks and the recommended reading path.

5. **Add a reference in the project's AI agent configuration**: In CLAUDE.md (for Claude Code), or the equivalent file for other agents, add an instruction to read CODEMAP.md before exploring code.

### Calibration

The right level of detail depends on the codebase size:

| Codebase size | L0 entries | L1 detail |
|---------------|-----------|-----------|
| 20-50 files | 5-8 areas | File-level descriptions |
| 50-200 files | 8-12 areas | File + class-level descriptions |
| 200+ files | 10-15 areas, consider L1.5 sub-indexes | Class + method-level descriptions |

For very large repositories, a third intermediate level (L1.5) may be needed: L1 files that point to sub-area indexes rather than directly to source code. This adds one more navigation step but keeps each file readable.

## File Inventory

The codemap for this repository consists of:

```
.claude/
├── CODEMAP.md              Level 0 index (entry point)
└── codemap/
    ├── architecture.md     Design patterns, three-layer architecture, caching
    ├── clients.md          LLM, embedding, speech client implementations
    ├── modules.md          LLMCaller, EncoderCaller, SpeechCaller
    ├── api.md              FastAPI application, endpoints, configuration
    ├── voice-system.md     VoiceAgent, AudioStreamer, demo scripts
    ├── tools.md            Tool framework, built-in tools
    ├── utilities.md        Environment, file access, logging, templates
    ├── testing.md          Test organization, fixtures, mock builders
    ├── devops.md           Dependencies, linters, CI/CD, Docker
    ├── web-demo.md         Browser demo, WebSocket, frontend
    └── documentation.md    Existing guides and their content summaries
```

`CLAUDE.md` contains an instruction directing agents to read `CODEMAP.md` before exploring code.

## Limitations

- **Line numbers drift**: As code is edited, line numbers in L1 files become approximate. This is acceptable for orientation but may cause confusion if drift exceeds ~50 lines.
- **Maintenance burden**: The codemap is a form of documentation that can become stale. It adds overhead to structural changes.
- **Not a substitute for code reading**: The codemap helps agents find the right file, but understanding the code still requires reading it.
- **Assumes agent compliance**: The system depends on agents following the instruction to read CODEMAP.md first. If an agent ignores this instruction, the codemap provides no benefit.
- **Single-repo scope**: The codemap describes one repository. Cross-repository navigation (e.g., for monorepos with shared libraries) would require additional structure.
