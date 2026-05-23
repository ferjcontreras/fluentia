# Testing

## Overview

The test suite is organized in three tiers (unit, integration, e2e) with a directory structure that mirrors the source code. Tests use a four-layer approach for unit testing, fluent mock builders, and auto-mocked environment fixtures. The comprehensive testing guide is at `docs/guides/test-development-guide.md`.

---

## Test Organization

```
tests/
├── conftest.py              # Global fixtures (auto-mocked env, provider configs)
├── fixtures/
│   ├── builders.py          # Fluent mock builders
│   └── data/                # Test templates and data files
├── unit/                    # Fast, fully mocked (runs by default)
│   ├── clients/llm/         # One test file per client implementation
│   ├── clients/embedding/
│   ├── clients/speech/
│   ├── modules/
│   ├── api/
│   ├── agent/
│   ├── audio/
│   ├── tools/
│   └── utils/
├── integration/             # Real external services (marked @pytest.mark.integration)
│   ├── clients/llm/
│   ├── clients/embedding/
│   ├── clients/speech/
│   ├── modules/
│   └── api/
└── e2e/                     # Full workflows (marked @pytest.mark.e2e)
    ├── test_health_e2e.py
    ├── test_error_scenarios_e2e.py
    └── test_observability_e2e.py
```

---

## Global Fixtures

**File**: `tests/conftest.py`

- `mock_load_env` (line 27, **autouse**): Mocks `load_env()` for all unit tests. Tests marked `@pytest.mark.real_env` bypass this.
- `mock_openai_client_full` (line 46): Full OpenAI client mock with async methods
- `mock_aiobotocore_session` (line 59): AWS aiobotocore session mock with async context manager
- Provider config fixtures (lines 83-125): Pre-built configs for Bedrock, OpenAI, Skynet (both LLM and embedding)

---

## Mock Builders (Fluent Interface)

**File**: `tests/fixtures/builders.py`

### LLMClientMockBuilder (line 8)
```python
mock = LLMClientMockBuilder().with_response("test").build()
mock = LLMClientMockBuilder().with_structured_response(pydantic_obj).build()
mock = LLMClientMockBuilder().with_decision("option_a").build()
mock = LLMClientMockBuilder().with_error(SomeException()).build()
mock = LLMClientMockBuilder().with_timeout(5.0).build()
mock = LLMClientMockBuilder().with_multiple_responses(["a", "b"]).build()
mock = LLMClientMockBuilder().with_slow_response(0.5, "content").build()
```

### EmbeddingClientMockBuilder (line 66)
```python
mock = EmbeddingClientMockBuilder().with_embeddings([[0.1, 0.2]]).build()
mock = EmbeddingClientMockBuilder().with_error().build()
```

### CacheStoreMockBuilder (line 106)
```python
mock = CacheStoreMockBuilder().with_cache_hit("key", {"data": 1}).build()
mock = CacheStoreMockBuilder().with_cache_miss("key").build()
mock = CacheStoreMockBuilder().with_cache_error(SomeException()).build()
```

### Convenience Functions (lines 156-166)
- `create_llm_mock_with_response(content)`: Quick LLM mock
- `create_embedding_mock_with_embeddings(embeddings)`: Quick embedding mock
- `create_cache_mock_with_data(cache_data)`: Quick cache mock

---

## Test Markers

| Marker | Purpose | Runs by default? |
|--------|---------|-----------------|
| (none) | Unit tests | Yes |
| `@pytest.mark.manual` | Manual-only tests | No |
| `@pytest.mark.integration` | Real external services | No |
| `@pytest.mark.e2e` | End-to-end workflows | No |
| `@pytest.mark.real_env` | Uses real env vars (bypasses mock_load_env) | Yes |
| `@pytest.mark.performance` | Performance benchmarks | No |

---

## Running Tests

```bash
uv run pytest                           # Unit tests only (default)
uv run pytest -m integration            # Integration tests
uv run pytest -m e2e                    # End-to-end tests
uv run pytest tests/unit/clients/llm/   # Specific directory
uv run pytest tests/unit/.../file.py    # Single file
uv run pytest ...::TestClass::test_fn   # Single test
uv run tox                              # All checks (lint, typecheck, tests)
uv run tox -e py313                     # Unit tests via tox
```

---

## Four-Layer Unit Test Approach

Each unit test file typically covers:

1. **Configuration tests**: Pydantic model validation, defaults, constraints
2. **Method tests**: Public interface methods with mocked dependencies
3. **Helper tests**: Private/static method behavior
4. **Behavior tests**: Lifecycle, state management, error handling

See `docs/guides/test-development-guide.md` for comprehensive patterns and examples.
