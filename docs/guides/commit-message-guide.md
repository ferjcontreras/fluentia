# Git Commit Message Guide

This guide defines the standard format for commit messages in the Fluentia repository. We follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification to maintain a clear and structured commit history.

## Why Conventional Commits?

- **Automated changelog generation**: Tools can generate changelogs automatically
- **Semantic versioning**: Commits clearly indicate breaking changes and features
- **Better navigation**: Easier to browse commit history and understand changes
- **Team communication**: Clear intent behind each change

## Commit Message Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Structure

1. **Type**: Describes the kind of change (required)
2. **Scope**: The area of codebase affected (optional)
3. **Description**: Brief summary of the change (required)
4. **Body**: Detailed explanation of the change (optional)
5. **Footer**: Breaking changes or issue references (optional)

## Commit Types

Type **must** be one of the following:

### Development Changes

- **feat**: A new feature for the user
  ```
  feat: add resume parsing endpoint
  feat(api): add rate limiting middleware
  ```

- **fix**: A bug fix
  ```
  fix: resolve memory leak in embedding cache
  fix(providers): handle timeout errors in Bedrock client
  ```

- **refactor**: Code changes that neither fix bugs nor add features
  ```
  refactor: simplify document conversion logic
  refactor(session): extract prompt config parsing to helper method
  ```

- **perf**: Performance improvements
  ```
  perf: optimize embedding batch processing
  perf(database): add index on frequently queried fields
  ```

### Code Quality

- **style**: Code formatting changes (white-space, formatting, missing semi-colons, etc.)
  ```
  style: apply ruff formatting to all files
  style(api): fix line length violations
  ```

- **test**: Adding or modifying tests
  ```
  test: add unit tests for LLM client
  test(integration): add end-to-end API tests
  ```

### Infrastructure & Tooling

- **build**: Changes to the build system or external dependencies
  ```
  build: update Python to 3.13
  build: add fastapi dependency
  ```

- **ci**: Changes to CI/CD configuration or scripts
  ```
  ci: add type checking to GitLab pipeline
  ci: enable parallel test execution
  ```

- **chore**: Other changes that don't modify source or test files
  ```
  chore: update .gitignore
  chore: scaffold project with ml-cookiecutter
  ```

### Documentation

- **docs**: Documentation changes only
  ```
  docs: update API usage examples
  docs: add architecture decision record for caching
  ```

## Scope Examples

Scope indicates which part of the codebase is affected. Common scopes:

- **api**: FastAPI endpoints and application factory
- **providers**: Voice provider implementations (Google, Bedrock)
- **session**: Session management and WebSocket protocol
- **agents**: Agent definitions and registry
- **tools**: Tool framework and implementations
- **observability**: Logging, health checks, and metrics
- **config**: Application configuration
- **tests**: Test files
- **ci**: CI/CD configuration
- **docker**: Docker configuration

## Description Guidelines

The description should:

- Use imperative mood: "add" not "added" or "adds"
- Start with lowercase (unless it's a proper noun)
- Not end with a period
- Be concise (50 characters or less)
- Clearly describe what the change does

### Good Examples

```
feat: add semantic search capability
fix: prevent duplicate cache entries
refactor: extract validation logic to separate module
```

### Bad Examples

```
feat: Added semantic search.  ❌ (not imperative, has period)
fix: fixed a bug  ❌ (not descriptive)
Update README  ❌ (missing type)
```

## Body Guidelines

Use the body to explain:

- **What** changed and **why** (not how - code shows that)
- Context that reviewers need
- Side effects or impacts
- Reasoning behind the approach

Wrap at 72 characters for better readability.

### Example with Body

```
feat(api): add request logging middleware

Add middleware to log all incoming requests with timestamps,
request IDs, and response times. This helps with debugging
production issues and understanding API usage patterns.

The middleware runs before other middleware to ensure all
requests are logged, even if they fail validation.
```

## Footer Guidelines

Use footers for:

1. **Breaking changes**: Start with `BREAKING CHANGE:`
2. **Issue references**: Reference GitHub/GitLab issues

### Breaking Changes

```
feat(api): change authentication to use JWT

BREAKING CHANGE: API now requires JWT tokens instead of API keys.
Clients must update their authentication mechanism.
```

### Issue References

```
fix(providers): handle connection timeout gracefully

Closes #123
See also #45, #67
```

## Complete Examples

### Simple Feature

```
feat: add document type detection
```

### Feature with Scope

```
feat(tools): add web search tool implementation
```

### Bug Fix with Body

```
fix(cache): prevent race condition in Redis operations

The cache store was not properly locking during write operations,
leading to inconsistent state when multiple requests tried to
update the same key simultaneously.

Added distributed locking using Redis SETNX command to ensure
atomic write operations.
```

### Breaking Change

```
feat(api)!: redesign error response format

BREAKING CHANGE: Error responses now use RFC 7807 Problem Details format.
Response structure has changed from:
  { "error": "message" }
to:
  { "type": "...", "title": "...", "detail": "...", "status": 400 }

Closes #234
```

### Chore with Scope

```
chore(deps): update pydantic to v2.10.6
```

## Multiple Changes

If your commit includes multiple logical changes:

1. **Preferred**: Split into multiple commits
2. **Alternative**: Use bullet points in the body

```
refactor: improve code organization

- Extract validation logic to utils module
- Simplify error handling in API endpoints
- Remove unused helper functions
```

## Commit Message Template

You can configure git to use a commit message template:

```bash
# Create template file
cat > ~/.gitmessage << 'EOF'
# <type>[optional scope]: <description>
#
# [optional body]
#
# [optional footer(s)]
#
# Types: feat, fix, refactor, perf, style, test, build, ci, chore, docs
EOF

# Configure git to use it
git config --global commit.template ~/.gitmessage
```

## Tools and Validation

### Pre-commit Hooks

This project uses [commitizen](https://commitizen-tools.github.io/commitizen/) with pre-commit hooks to enforce commit message format. To set up:

```bash
# Install pre-commit hooks (includes commitizen validation)
uv run pre-commit install
```

Once installed, commit messages are automatically validated against the Conventional Commits format. Invalid commits will be rejected with helpful error messages.

### IDE Extensions

- **VS Code**: [Conventional Commits](https://marketplace.visualstudio.com/items?itemName=vivaxy.vscode-conventional-commits)
- **JetBrains**: Built-in commit message templates

## Quick Reference

```
feat:      New feature
fix:       Bug fix
refactor:  Code change without fixing bugs or adding features
perf:      Performance improvement
style:     Formatting changes
test:      Adding or updating tests
build:     Build system or dependency changes
ci:        CI/CD changes
chore:     Other changes (configs, tools, etc.)
docs:      Documentation changes
```

## Examples from Fluentia

```
feat(agents): add customer support agent definition
fix(providers): handle WebSocket disconnect in Bedrock provider
refactor(session): extract prompt config parsing to helper method
perf(tools): cache tool spec generation
style: apply ruff formatting
test(providers): add unit tests for Google event conversion
build: upgrade to Python 3.13
ci: add dependency analysis job
chore: update .gitignore
docs: add WebSocket protocol reference
```

## Resources

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [Angular Commit Guidelines](https://github.com/angular/angular/blob/master/CONTRIBUTING.md#commit)
- [How to Write a Git Commit Message](https://chris.beams.io/posts/git-commit/)
