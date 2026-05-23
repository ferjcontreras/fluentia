# Test Development Guide

This document provides comprehensive guidance on testing practices, patterns, and conventions used in the Fluentia repository. Following these guidelines ensures thorough test coverage, maintainable test code, and consistent testing practices across the codebase.

## Automated Test Execution

The repository includes a `check_code.sh` script that runs code quality checks (ruff, mypy, pylint):

```bash
./check_code.sh
```

To run tests:

```bash
# Run unit tests only (default)
uv run pytest

# Run all tests including integration and e2e
uv run pytest -m ""

# Run integration tests
uv run pytest -m "integration and manual and real_env"

# Run specific test file
uv run pytest tests/unit/providers/bedrock/test_client.py -v

# Run all checks via tox (recommended before committing)
uv run tox
```

## Table of Contents

1. [Test Organization](#test-organization)
2. [Unit Testing](#unit-testing)
3. [Integration Testing](#integration-testing)
4. [End-to-End Testing](#end-to-end-testing)
5. [Fixtures and Configuration](#fixtures-and-configuration)
6. [Test Markers](#test-markers)
7. [Assertions and Patterns](#assertions-and-patterns)
8. [Documentation and Naming](#documentation-and-naming)
9. [Common Anti-Patterns](#common-anti-patterns)

## Test Organization

### Directory Structure

Tests are organized by type and mirror the source code structure:

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (fast, no external dependencies)
│   ├── agents/
│   │   └── test_agents.py
│   ├── config/
│   │   └── test_config.py
│   ├── observability/
│   │   ├── test_health.py
│   │   ├── test_logging.py
│   │   └── test_metrics.py
│   ├── providers/
│   │   ├── test_base.py
│   │   ├── test_google.py
│   │   └── bedrock/
│   │       ├── test_client.py
│   │       ├── test_config.py
│   │       └── test_provider.py
│   ├── session/
│   │   ├── test_events.py
│   │   └── test_manager.py
│   ├── tools/
│   │   ├── test_date_time.py
│   │   └── test_processor.py
│   └── test_app.py
├── integration/             # Integration tests (external dependencies)
└── e2e/                     # End-to-end tests
```

### File Naming Conventions

- **Unit tests**: `test_<module_name>.py` or `test_<module_name>.PROD.py` (async version)
- **Integration tests**: `test_<module_name>.py` or `test_<module_name>.PROD.py`
- **E2E tests**: `test_<feature>_e2e.py`

The `.PROD.py` suffix indicates async versions of tests for production async implementations.

### When to Write Which Type of Test

**Unit Tests** - Write when:
- Testing configuration validation
- Testing business logic with mocked dependencies
- Testing helper methods and utilities
- Testing error handling and edge cases
- Tests should run in milliseconds

**Integration Tests** - Write when:
- Testing actual API calls to external services
- Testing database interactions
- Testing file system operations
- Verifying compatibility with external service versions
- Tests may take seconds to complete

**E2E Tests** - Write when (production repos only):
- Testing complete user workflows
- Testing API endpoint behaviors
- Testing system resilience and performance
- Verifying cross-component interactions
- Tests may take seconds to minutes

## Unit Testing

### Test Structure: The Four-Layer Approach

Comprehensive unit tests for a client follow this structure:

1. **Configuration Tests** - Validate Pydantic models
2. **Client Method Tests** - Test public interface
3. **Helper Method Tests** - Test private/static methods
4. **Behavior Tests** - Test lifecycle and state

```python
"""Unit tests for Bedrock client."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from fluentia.clients import BedrockLLMClient
from fluentia.clients import BedrockLLMClientConfig


class TestBedrockLLMClientConfig:
    """Tests for Bedrock LLM client configuration."""

    def test_default_values(self):
        """Test default configuration values."""
        config = BedrockLLMClientConfig(model_id="test-model", region="us-west-2")

        assert config.model_id == "test-model"
        assert config.region == "us-west-2"
        assert config.temperature == 0.0
        assert config.max_tokens == 2048
        assert config.top_p == 0.9

    def test_invalid_temperature(self):
        """Test temperature validation."""
        with pytest.raises(ValueError):
            BedrockLLMClientConfig(
                model_id="test", region="us-west-2", temperature=1.5
            )


class TestBedrockLLMClient:
    """Tests for Bedrock LLM client."""

    @pytest.mark.asyncio
    async def test_chat_success(
        self, client: BedrockLLMClient, mock_aiobotocore_session: MagicMock
    ):
        """Test successful chat completion."""
        # Arrange
        mock_response = MagicMock()
        mock_client = mock_aiobotocore_session.create_client.return_value
        mock_client.converse = AsyncMock(return_value=mock_response)

        client._extract_status_code = MagicMock(return_value=200)
        client._extract_chat_content = MagicMock(return_value="test response")

        # Act
        response = await client.chat(
            system_prompt="test system",
            messages=[{"role": "user", "content": {"text": "test"}}],
        )

        # Assert
        assert response == "test response"

    @pytest.mark.asyncio
    async def test_chat_api_error(
        self, client: BedrockLLMClient, mock_aiobotocore_session: MagicMock
    ):
        """Test chat with API error."""
        # Arrange
        mock_response = MagicMock()
        mock_client = mock_aiobotocore_session.create_client.return_value
        mock_client.converse = AsyncMock(return_value=mock_response)
        client._extract_status_code = MagicMock(return_value=500)

        # Act & Assert
        with pytest.raises(RuntimeError, match="Bedrock API error"):
            await client.chat(
                system_prompt="test system",
                messages=[{"role": "user", "content": {"text": "test"}}],
            )


class TestBedrockLLMClientHelperMethods:
    """Tests for Bedrock LLM client helper methods."""

    def test_extract_status_code(self):
        """Test _extract_status_code method."""
        # Arrange
        response = {"ResponseMetadata": {"HTTPStatusCode": 200}}

        # Act
        status_code = BedrockLLMClient._extract_status_code(response)

        # Assert
        assert status_code == 200

    def test_extract_chat_content(self):
        """Test _extract_chat_content method."""
        # Arrange
        response = {"output": {"message": {"content": [{"text": "Hello world"}]}}}

        # Act
        content = BedrockLLMClient._extract_chat_content(response)

        # Assert
        assert content == "Hello world"


class TestBedrockLLMClientBehavior:
    """Tests for Bedrock LLM client behavior."""

    def test_client_string_representation(
        self,
        example_bedrock_llm_config: BedrockLLMClientConfig,
        mock_aiobotocore_session: MagicMock,
    ):
        """Test string representation of the client."""
        # Arrange & Act
        client = BedrockLLMClient(
            config=example_bedrock_llm_config,
            session=mock_aiobotocore_session,
            env_file=None,
        )
        client_str = str(client)

        # Assert
        assert "BedrockLLMClient" in client_str

    @pytest.mark.asyncio
    async def test_multiple_chat_calls_independence(
        self,
        example_bedrock_llm_config: BedrockLLMClientConfig,
        mock_aiobotocore_session: MagicMock,
        env_file: str,
    ):
        """Test that multiple chat calls are independent."""
        # Arrange
        client = BedrockLLMClient(
            config=example_bedrock_llm_config,
            session=mock_aiobotocore_session,
            env_file=env_file,
        )

        mock_client = mock_aiobotocore_session.create_client.return_value
        mock_client.converse = AsyncMock(
            side_effect=[MockResponse("First response"), MockResponse("Second response")]
        )

        # Act
        system_prompt = "You are a helpful assistant."
        messages1 = [{"role": "user", "content": {"text": "First message"}}]
        messages2 = [{"role": "user", "content": {"text": "Second message"}}]
        result1 = await client.chat(system_prompt, messages1)
        result2 = await client.chat(system_prompt, messages2)

        # Assert
        assert result1 == "First response"
        assert result2 == "Second response"
        assert mock_client.converse.call_count == 2
```

### Mock Patterns

**Creating Mock Responses**:

```python
class MockResponse:
    """Mock response for Bedrock API calls."""

    def __init__(self, content: str | dict[str, Any]):
        if isinstance(content, str):
            self.output = {"message": {"content": [{"text": content}]}}
        else:
            self.body = MagicMock()
            self.body.read.return_value = content
        self.ResponseMetadata = {"HTTPStatusCode": 200}
```

**Mocking Async Context Managers**:

```python
@pytest.fixture
def mock_aiobotocore_session() -> MagicMock:
    """Fixture for mocked aiobotocore session."""
    session = MagicMock()
    client = MagicMock()

    # Mock async context manager behavior
    async def mock_aenter(self):
        return client

    async def mock_aexit(self, exc_type, exc_val, exc_tb):
        return None

    client.__aenter__ = mock_aenter
    client.__aexit__ = mock_aexit

    # Mock async methods
    client.converse = AsyncMock()
    client.invoke_model = AsyncMock()

    session.create_client = MagicMock(return_value=client)
    return session
```

**Mocking Sync Boto3 Sessions**:

```python
@pytest.fixture
def mock_boto3_session() -> MagicMock:
    """Fixture for mocked boto3 session."""
    session = MagicMock(spec=boto3.Session)
    client = MagicMock(spec=BotoBaseClient)
    client.converse = MagicMock()
    client.invoke_model = MagicMock()
    session.client = MagicMock(return_value=client)
    return session
```

### Async Testing

Always use `@pytest.mark.asyncio` for async tests:

```python
@pytest.mark.asyncio
async def test_async_operation(self, client: AsyncClient):
    """Test async operation."""
    result = await client.async_method()
    assert result is not None
```

### Testing Error Cases

Test both HTTP errors and business logic errors:

```python
@pytest.mark.asyncio
async def test_parse_http_error_status(
    self, client: BedrockLLMClient, mock_aiobotocore_session: MagicMock
):
    """Test parse method with HTTP error status."""
    # Arrange
    class TestFormat(BaseModel):
        field: str

    mock_response = MagicMock()
    mock_client = mock_aiobotocore_session.create_client.return_value
    mock_client.converse = AsyncMock(return_value=mock_response)
    client._extract_status_code = MagicMock(return_value=500)

    # Act & Assert
    with pytest.raises(RuntimeError, match=r"Unexpected status code|Bedrock API error"):
        await client.parse(
            system_prompt="test",
            messages=[{"role": "user", "content": {"text": "test"}}],
            response_format=TestFormat,
        )
```

### Type Ignore Comments in Tests

Use `# type: ignore[dict-item]` when test data structure differs from production interface:

```python
# Production code expects dict[str, str]
async def parse(self, system_prompt: str, messages: list[dict[str, str]], ...):
    pass

# Test uses nested structure and suppresses type error
result = await client.parse(
    system_prompt="test",
    messages=[{"role": "user", "content": {"text": "test"}}],  # type: ignore[dict-item]
    response_format=TestFormat,
)
```

This preserves the clean production interface while allowing realistic test data.

## Integration Testing

### Purpose and Structure

Integration tests verify behavior with real external services. They are marked as manual and require valid credentials.

```python
"""Integration tests for Bedrock LLM client.

These tests are meant to be run manually and require valid AWS credentials.
To run these tests:
    pytest tests/integration/providers/bedrock/test_provider.py -v
        -m "integration and manual and real_env"
"""

import pytest
from pydantic import BaseModel

from fluentia.clients import BedrockLLMClient
from fluentia.clients import BedrockLLMClientConfig


class SampleResponse(BaseModel):
    """Sample response model for parse tests."""

    sentiment: str
    confidence: float


@pytest.mark.integration
@pytest.mark.manual
@pytest.mark.real_env
class TestBedrockIntegration:
    """Integration tests for Bedrock LLM client.

    These tests require valid AWS credentials and will make actual API calls.
    They are marked as manual and will be skipped during normal test runs.
    """

    @pytest.mark.parametrize(
        "region,model_id",
        [
            ("us-east-1", "meta.llama3-8b-instruct-v1:0"),
            ("us-west-2", "meta.llama3-1-8b-instruct-v1:0"),
            ("us-east-2", "meta.llama3-3-70b-instruct-v1:0"),
            ("us-west-2", "anthropic.claude-3-5-sonnet-20241022-v2:0"),
        ],
    )
    @pytest.mark.asyncio
    async def test_chat(self, region: str, model_id: str):
        """Test chat functionality with different models."""
        config = BedrockLLMClientConfig(
            model_id=model_id, region=region, temperature=0.7, max_tokens=100
        )
        client = BedrockLLMClient(config)

        system_prompt = "You are a helpful assistant."
        messages = [{"role": "user", "content": [{"text": "What is the capital of France?"}]}]

        response = await client.chat(system_prompt, messages)
        assert "Paris" in response

    @pytest.mark.parametrize(
        "region,model_id",
        [
            ("us-west-2", "anthropic.claude-3-5-sonnet-20241022-v2:0"),
        ],
    )
    @pytest.mark.asyncio
    async def test_parse(self, region: str, model_id: str):
        """Test parse functionality with different models."""
        config = BedrockLLMClientConfig(
            model_id=model_id, region=region, temperature=0.1, max_tokens=100
        )
        client = BedrockLLMClient(config)

        system_prompt = "You are a sentiment analyzer."
        messages = [{"role": "user", "content": [{"text": "I love this product!"}]}]

        response = await client.parse(system_prompt, messages, SampleResponse)
        assert isinstance(response, SampleResponse)
        assert response.sentiment in ["positive", "negative", "neutral"]
        assert 0 <= response.confidence <= 1
```

### Key Integration Test Patterns

1. **Always use three markers**: `@pytest.mark.integration`, `@pytest.mark.manual`, `@pytest.mark.real_env`
2. **Parametrize model configurations**: Test multiple models/regions in single test
3. **Include run instructions**: Document exact pytest command in docstring
4. **Test real responses**: Verify actual API response structure and content
5. **Keep assertions realistic**: Don't assert exact strings, verify patterns

## End-to-End Testing

End-to-end tests are only included in production repositories that expose APIs or services. They test complete workflows from user perspective.

### FastAPI Application Testing

```python
"""End-to-end tests for health and status endpoints.

These tests verify the system monitoring and observability endpoints:
- Basic health check endpoint
- Detailed system status endpoint
- Metrics endpoint
- Service dependency health
- Error handling and resilience
"""

import os
import time

import pytest
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from xaloc.api.app import create_app


@pytest.fixture
def app():
    """Create FastAPI test application."""
    os.environ["ENABLE_METRICS"] = "true"

    # Clear the Prometheus registry to avoid conflicts between tests
    REGISTRY._collector_to_names.clear()
    REGISTRY._names_to_collectors.clear()

    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.mark.e2e
@pytest.mark.manual
class TestHealthEndpointsE2E:
    """End-to-end tests for health and monitoring endpoints."""

    def test_health_endpoint_basic(self, client: TestClient):
        """Test basic health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        response_data = response.json()

        # Verify response structure
        assert "status" in response_data
        assert "timestamp" in response_data

        # Verify health status
        assert response_data["status"] == "healthy"
        assert isinstance(response_data["timestamp"], int | float)
        assert response_data["timestamp"] > 0

    def test_health_endpoint_response_time(self, client: TestClient):
        """Test health endpoint response time."""
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()

        # Health check should be fast
        response_time = (end_time - start_time) * 1000
        assert response_time < 1000  # Should respond within 1 second

        # Verify successful response
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_health_endpoint_concurrent_requests(self, client: TestClient):
        """Test health endpoint under concurrent load."""
        import threading

        results = []

        def check_health():
            response = client.get("/health")
            results.append(
                {
                    "status_code": response.status_code,
                    "healthy": response.json().get("status") == "healthy",
                }
            )

        # Launch concurrent requests
        threads = []
        for _ in range(20):
            thread = threading.Thread(target=check_health)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all requests succeeded
        assert len(results) == 20
        for result in results:
            assert result["status_code"] == 200
            assert result["healthy"] is True
```

### E2E Test Patterns

1. **Test real workflows**: Complete user journeys from start to finish
2. **Test performance**: Measure response times and throughput
3. **Test concurrency**: Verify behavior under concurrent load
4. **Test resilience**: Verify graceful degradation when services fail
5. **Test observability**: Verify metrics, logging, and monitoring work correctly

## Fixtures and Configuration

### Fixture Organization

Fixtures are defined in `conftest.py` files at appropriate levels:

- `tests/conftest.py`: Fixtures shared across all test types
- `tests/unit/conftest.py`: Unit test specific fixtures (if needed)
- `tests/integration/conftest.py`: Integration test specific fixtures (if needed)

### Common Fixture Patterns

**Environment File Fixture**:

```python
@pytest.fixture
def env_file(tmp_path):
    """Create a temporary env file."""
    env_file = tmp_path / "test.env"
    env_file.write_text("ENV_VAR=value")
    return str(env_file)
```

**Auto-Mocking Environment**:

```python
@pytest.fixture(autouse=True)
def mock_load_env(request, monkeypatch):
    """Mock the load_env function to set fake environment variables."""
    if request.node.get_closest_marker("real_env"):
        # Skip mocking if real_env marker is present
        return

    def mock_load(env_file=None):
        if not env_file:
            os.environ["BAR"] = "foo"

        os.environ["OPENAI_API_KEY"] = ""
        os.environ["AWS_ACCESS_KEY_ID"] = ""
        os.environ["AWS_SECRET_ACCESS_KEY"] = ""
        os.environ["AWS_SESSION_TOKEN"] = ""

    monkeypatch.setattr("fluentia.utils.env.load_env", mock_load)
```

**Configuration Fixtures**:

```python
@pytest.fixture
def example_bedrock_llm_config() -> BedrockLLMClientConfig:
    """Fixture for Bedrock LLM configuration."""
    return BedrockLLMClientConfig(
        model_id="meta.llama3-3-70b-instruct-v1:0",
        region="us-west-2",
        temperature=0.1,
        max_tokens=100,
        top_p=0.9,
    )


@pytest.fixture
def example_openai_llm_config() -> OpenAILLMClientConfig:
    """Fixture for OpenAI LLM configuration."""
    return OpenAILLMClientConfig(
        model_id="gpt-4",
        temperature=0.1,
        max_tokens=100,
        top_p=0.9,
    )
```

**Client Fixtures**:

```python
@pytest.fixture
def client(
    example_bedrock_llm_config: BedrockLLMClientConfig,
    mock_aiobotocore_session: MagicMock,
    env_file: str,
) -> BedrockLLMClient:
    """Fixture for Bedrock client with mocked session."""
    return BedrockLLMClient(
        config=example_bedrock_llm_config,
        session=mock_aiobotocore_session,
        env_file=env_file,
    )
```

## Test Markers

### Standard Markers

All repositories use these pytest markers defined in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
markers = [
    "manual: marks tests that should only be run manually",
    "real_env: marks tests that should use real environment variables",
    "integration: marks tests as integration tests",
    "e2e: marks tests as end-to-end tests",
    "performance: marks tests as performance tests"
]
testpaths = ["tests"]
addopts = "-m 'not manual and not integration and not e2e and not performance'"
```

### Default Test Execution

By default, `pytest` runs only unit tests:

```bash
# Runs unit tests only (excludes manual, integration, e2e, performance)
uv run pytest
```

### Running Specific Test Categories

```bash
# Run integration tests with real environment
uv run pytest -m "integration and manual and real_env"

# Run e2e tests
uv run pytest -m "e2e and manual"

# Run all tests (remove default exclusions)
uv run pytest -m ""

# Run specific marker combination
uv run pytest -m "integration and not manual"
```

## Assertions and Patterns

### The Arrange-Act-Assert Pattern

Structure all tests using clear AAA sections:

```python
def test_example(self):
    """Test example functionality."""
    # Arrange
    config = ExampleConfig(param1="value1", param2="value2")
    client = ExampleClient(config)
    mock_response = MagicMock()

    # Act
    result = client.process(mock_response)

    # Assert
    assert result.status == "success"
    assert result.data is not None
```

For complex tests, use comments to mark sections:

```python
@pytest.mark.asyncio
async def test_complex_flow(self, client: Client):
    """Test complex multi-step flow."""
    # Arrange
    config = create_test_config()
    mock_service = setup_mock_service()
    expected_result = {"status": "completed", "items": [1, 2, 3]}

    # Act
    result = await client.execute_flow(config, mock_service)

    # Assert
    assert result["status"] == "completed"
    assert len(result["items"]) == 3
    assert result["items"] == expected_result["items"]
```

### Assertion Patterns

**Test nested structures**:

```python
def test_nested_response(self):
    """Test response with nested structure."""
    response = {
        "output": {
            "message": {
                "content": [{"text": "Hello world"}]
            }
        }
    }

    assert "output" in response
    assert "message" in response["output"]
    assert "content" in response["output"]["message"]
    assert response["output"]["message"]["content"][0]["text"] == "Hello world"
```

**Test type and structure**:

```python
def test_response_structure(self):
    """Test response structure and types."""
    result = client.get_embeddings(["text1", "text2"])

    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(emb, list) for emb in result)
    assert all(isinstance(val, float) for emb in result for val in emb)
```

**Test normalization**:

```python
def test_normalized_embeddings(self):
    """Test that embeddings are normalized."""
    import numpy as np

    embeddings = client.encode_texts(["test text"])
    embedding_array = np.array(embeddings[0])
    norm = np.linalg.norm(embedding_array)

    assert np.isclose(norm, 1.0, atol=1e-5)
```

## Documentation and Naming

### Test Class Naming

Use descriptive class names that indicate what is being tested:

```python
class TestBedrockLLMClientConfig:
    """Tests for Bedrock LLM client configuration."""

class TestBedrockLLMClient:
    """Tests for Bedrock LLM client."""

class TestBedrockLLMClientHelperMethods:
    """Tests for Bedrock LLM client helper methods."""

class TestBedrockLLMClientBehavior:
    """Tests for Bedrock LLM client behavior."""
```

### Test Method Naming

Use clear, descriptive names that explain what is being tested:

```python
# ✅ Good: Descriptive and specific
def test_default_configuration_values(self):
    """Test that default configuration values are set correctly."""

def test_chat_success(self):
    """Test successful chat completion."""

def test_chat_api_error(self):
    """Test chat with API error."""

def test_multiple_chat_calls_independence(self):
    """Test that multiple chat calls are independent."""

# ❌ Avoid: Vague or generic names
def test_config(self):
    """Test config."""

def test_chat(self):
    """Test chat."""

def test_error(self):
    """Test error."""
```

### Test Docstrings

All test methods must have concise docstrings:

```python
def test_temperature_validation(self):
    """Test temperature validation."""

def test_encode_single_text(self, region, model_id, embedding_dim):
    """Test encoding a single text with different models."""

@pytest.mark.asyncio
async def test_parse_http_error_status(self, client: Client):
    """Test parse method with HTTP error status."""
```

For integration tests, include run instructions:

```python
"""Integration tests for Bedrock LLM client.

These tests are meant to be run manually and require valid AWS credentials.
To run these tests:
    pytest tests/integration/providers/bedrock/test_provider.py -v
        -m "integration and manual and real_env"
"""
```

## Common Anti-Patterns

### Anti-Pattern: Testing Implementation Details

```python
# ❌ Bad: Testing internal implementation
def test_internal_cache_structure(self):
    """Test internal cache structure."""
    client = Client()
    client._internal_cache["key"] = "value"
    assert len(client._internal_cache) == 1

# ✅ Good: Testing public behavior
def test_caching_behavior(self):
    """Test that client caches repeated requests."""
    client = Client()
    result1 = client.get("key")
    result2 = client.get("key")
    assert result1 == result2
    assert client.api_call_count == 1  # Called once due to caching
```

### Anti-Pattern: Over-Mocking

```python
# ❌ Bad: Mocking everything including the code under test
def test_process_data(self):
    """Test process data."""
    mock_processor = MagicMock()
    mock_processor.process.return_value = "processed"
    result = mock_processor.process("data")
    assert result == "processed"  # We're testing the mock, not our code!

# ✅ Good: Mock only external dependencies
def test_process_data(self):
    """Test process data."""
    processor = DataProcessor()  # Real code under test
    mock_client = MagicMock()  # Mock external dependency
    mock_client.fetch.return_value = {"raw": "data"}

    result = processor.process(mock_client)
    assert result == {"processed": "data"}
```

### Anti-Pattern: Test Interdependence

```python
# ❌ Bad: Tests depend on each other
class TestClient:
    def test_1_create_client(self):
        """Test client creation."""
        self.client = Client()  # Stored in self
        assert self.client is not None

    def test_2_use_client(self):
        """Test client usage."""
        result = self.client.fetch()  # Depends on test_1
        assert result is not None

# ✅ Good: Each test is independent
class TestClient:
    @pytest.fixture
    def client(self):
        """Create client for each test."""
        return Client()

    def test_create_client(self, client):
        """Test client creation."""
        assert client is not None

    def test_use_client(self, client):
        """Test client usage."""
        result = client.fetch()
        assert result is not None
```

### Anti-Pattern: Unclear Assertions

```python
# ❌ Bad: Unclear what is being tested
def test_response(self):
    """Test response."""
    result = client.get()
    assert result

# ✅ Good: Clear, specific assertions
def test_response_contains_required_fields(self):
    """Test response contains all required fields."""
    result = client.get()
    assert "status" in result
    assert "data" in result
    assert result["status"] == "success"
    assert isinstance(result["data"], list)
```

### Anti-Pattern: Missing Error Tests

```python
# ❌ Bad: Only testing success path
class TestClient:
    def test_fetch_success(self):
        """Test successful fetch."""
        client = Client()
        result = client.fetch("valid_id")
        assert result is not None

# ✅ Good: Test both success and error paths
class TestClient:
    def test_fetch_success(self):
        """Test successful fetch."""
        client = Client()
        result = client.fetch("valid_id")
        assert result is not None

    def test_fetch_not_found(self):
        """Test fetch with invalid ID."""
        client = Client()
        with pytest.raises(NotFoundError):
            client.fetch("invalid_id")

    def test_fetch_api_error(self):
        """Test fetch with API error."""
        client = Client()
        with pytest.raises(APIError):
            client.fetch("error_trigger_id")
```

## Summary

Following these testing guidelines ensures:

- **Comprehensive coverage**: Testing configuration, methods, helpers, and behavior
- **Fast feedback**: Unit tests run in milliseconds
- **Reliable integration**: Integration tests verify real API compatibility
- **Production confidence**: E2E tests verify complete workflows
- **Maintainability**: Clear patterns and organization
- **Consistency**: Uniform approach across the codebase

When in doubt, study existing tests in similar modules and follow established patterns. Testing is a critical part of code quality and maintainability in the Fluentia repository.
