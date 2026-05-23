# Iterative Redesign: Documentation Strategy

## 1. Directory Structure

The new repository will maintain the `docs/ai-assistance` structure to support continuous AI-assisted development, alongside standard developer documentation.

```text
docs/
├── ai-assistance/
│   └── design/
│       └── 2026-03-16-prod-redesign/  # (These current documents)
├── guides/
│   ├── about-avature.md               # Domain context (Ported as-is)
│   ├── technical-writing-guide.md     # Documentation standards (Ported as-is)
│   ├── code-style-guide.md            # Overhauled for production
│   ├── commit-message-guide.md        # Overhauled for production
│   └── test-development-guide.md      # Overhauled for production
├── reference/
│   └── architecture.md                # New: Systems architecture and event flow
└── tutorials/
    └── local-development.md           # New: How to run the app via docker-compose
```

## 2. Porting Strategy for Guides

### 2.1 Preserved Guides (Literal Copy)
- **`about-avature.md`**: Provides critical domain knowledge about Avature's records, workflows, and portals. This is essential for both human developers and AI agents to understand the ultimate use cases of the Orchestrator tools.
- **`technical-writing-style-guide.md`**: Maintains consistency in how we write documentation across the company.

### 2.2 Re-versioned Guides (The "Spirit", but Improved)

The following guides will be rewritten to reflect the stricter production standards of the new repository:

#### 2.2.1 Code Style Guide
- **Current PoC:** Focuses on general Python tips.
- **New Production Version:** Will strictly mandate `ruff` configurations, `mypy` strict typing, and Dependency Injection patterns (especially for FastAPI routes). It will also establish clear boundaries for async programming (e.g., when to use `asyncio.Task` for background tool processing vs standard `await`).

#### 2.2.2 Test Development Guide
- **Current PoC:** Mentions `pytest` and basic mocking.
- **New Production Version:** Will mandate a strict "Testing Pyramid."
  - **Unit Tests:** Must achieve 90%+ coverage. Strict use of dependency injection to avoid `unittest.mock.patch` where possible.
  - **Integration Tests:** Must use test containers or mocked WebSocket clients (like FastAPI's `TestClient.websocket_connect`) to simulate the frontend sending audio.
  - **E2E Tests:** Defined contracts for how tools behave when receiving simulated Orchestrator latency.

#### 2.2.3 Commit Message Guide
- **Current PoC:** Uses basic conventional commits.
- **New Production Version:** Will enforce `commitizen` via pre-commit hooks, requiring Jira/Ticket numbers in scopes (e.g., `feat(LIV-123): add orchestrator tool adapter`) to ensure traceability in the CI/CD pipeline.

## 3. Onboarding Experience

The README.md of the new repository will be streamlined:
1. **Architecture Diagram:** A Mermaid.js diagram illustrating the WebSocket flow from Browser -> FastAPI -> Bedrock/Google.
2. **Quickstart:** A simplified 3-step process using `docker-compose up` to launch the database/redis mocks and the application server simultaneously, reducing first-day setup friction.
