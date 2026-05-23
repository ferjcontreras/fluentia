# Code Style Guide for New Developers

This document provides comprehensive guidance on the coding conventions, architectural patterns, and style preferences used in the Fluentia repository. Following these guidelines ensures consistency, maintainability, and clarity across the codebase.

## Automated Code Quality Checks

The repository includes a `check_code.sh` script that automatically runs all code quality tools:

```bash
./check_code.sh
```

This script runs four essential checks in sequence:
1. **ruff format**: Automatically formats code according to our style
2. **ruff check --fix**: Identifies and fixes linting issues
3. **mypy**: Performs static type checking
4. **pylint**: Analyzes code quality and enforces standards

Running this script before committing ensures your code meets all quality standards. Many of the guidelines below are automatically enforced by these tools.

## Table of Contents

1. [Python Language Features](#python-language-features)
2. [Type Hints and Annotations](#type-hints-and-annotations)
3. [Import Organization](#import-organization)
4. [Configuration and Data Models](#configuration-and-data-models)
5. [Architectural Patterns](#architectural-patterns)
6. [Error Handling](#error-handling)
7. [Documentation and Naming](#documentation-and-naming)
8. [Class and Interface Design](#class-and-interface-design)
9. [Code Organization](#code-organization)

## Python Language Features

### Modern Python 3.13 Syntax

Use modern Python 3.13 features and syntax patterns:

```python
# ✅ Preferred: Union syntax with |
def process_data(items: list[str] | None = None) -> dict[str, Any]:
    pass

# ❌ Avoid: Legacy typing imports
from typing import List, Optional, Dict, Union
def process_data(items: Optional[List[str]] = None) -> Dict[str, Union[str, int]]:
    pass
```

### Built-in Collection Types

Use built-in collection types instead of typing imports:

```python
# ✅ Preferred
def get_results() -> list[dict[str, Any]]:
    return [{"name": "example", "values": [1, 2, 3]}]

# ❌ Avoid
from typing import List, Dict, Any
def get_results() -> List[Dict[str, Any]]:
    return [{"name": "example", "values": [1, 2, 3]}]
```

### Exception: Any and Abstract Types

Import `Any` and abstract types from `typing`:

```python
# ✅ Correct: Import Any from typing
from typing import Any

# ✅ Correct: Import ClassVar for class variables
from typing import ClassVar

class Strategy:
    REQUIRED_FIELDS: ClassVar[dict[str, dict[str, Any]]] = {
        "id": {"type": "keyword", "index": True}
    }
```

## Type Hints and Annotations

### Comprehensive Type Coverage

**All functions, methods, class attributes, and variables should have type hints.** This includes local variables, loop variables, and any other variable assignments:

```python
class BaseClient(abc.ABC):
    """Base class for clients."""

    def __init__(self, config: BaseClientConfig) -> None:
        self.config: BaseClientConfig = config
        self.timeout: float = config.timeout

    @abc.abstractmethod
    async def fetch(self, url: str) -> dict[str, Any]:
        """Fetch data from URL."""
        raise NotImplementedError("Subclasses must implement `fetch()`")

    async def _process_response(self, data: dict[str, Any]) -> list[str]:
        """Example showing variable type hints."""
        results: list[str] = []

        for item in data.get("items", []):
            key: str = item["key"]
            value: str = item["value"]
            formatted: str = f"{key}: {value}"
            results.append(formatted)

        return results
```

### Variable Type Hints

**Every variable assignment should include a type hint**, even when the type might seem obvious:

```python
# ✅ Preferred: All variables have type hints
def process_response(response_data: dict[str, Any]) -> dict[str, str]:
    """Process response with comprehensive type hints."""
    result: dict[str, str] = {}

    for key, value in response_data.items():
        key_str: str = str(key)
        value_str: str = str(value)

        processed_value: str = value_str.strip() if isinstance(value, str) else str(value)
        result[key_str] = processed_value

    keys: list[str] = [k for k in result.keys() if len(k) > 0]

    return result

# ❌ Avoid: Missing variable type hints
def process_response_bad(response_data):
    result = {}
    for key, value in response_data.items():
        processed_value = value.strip() if isinstance(value, str) else str(value)
        result[key] = processed_value
    return result
```

### Union Types with Proper Ordering

When using union types, order from most specific to most general:

```python
# ✅ Preferred: Specific types first
ClientConfig = (
    HTTPClientConfig
    | RedisClientConfig
    | DatabaseClientConfig
)

# ✅ String or None pattern with explicit type hints
api_key: str | None = None
base_url: str | None = None
timeout_seconds: float | None = None
```

## Import Organization

### Import Grouping and Ordering

Follow strict import organization with three groups, sorted alphabetically within each:

```python
"""Module docstring describing the module's purpose."""

# Standard library imports
import abc
import logging
from pathlib import Path
from typing import Any
from typing import ClassVar
from typing import Literal

# Third-party imports
import httpx
from pydantic import BaseModel
from pydantic import Field

# Local imports
import fluentia.utils.env as env_utils
from fluentia.clients import BaseClient
from fluentia.modules import DataProcessor
from fluentia.utils.helper import load_config
```

**Important**: We use **one import per line** (configured via `force-single-line = true` in pyproject.toml). This provides several benefits:
- **Clearer git diffs**: When adding or removing an import, only one line changes
- **Easier merge conflict resolution**: Import conflicts are simpler to resolve
- **Better code review**: Changes to imports are more visible and easier to understand

### Absolute Imports Only

Always use absolute imports starting with the project root. **Prefer the shortest possible import path** - use imports via `__init__.py` when available:

```python
# ✅ Preferred: Shortest absolute imports via __init__.py
from fluentia.clients import BaseClient, HTTPClient
from fluentia.modules import DataProcessor

# ✅ Acceptable: Direct imports when not available via __init__.py
from fluentia.utils.helper import load_config
from fluentia.utils.env import load_env

# ❌ Never use relative imports
from .base import BaseClient
from ..modules.processor import DataProcessor
```

## Configuration and Data Models

### Pydantic over Dataclasses

Always use Pydantic models instead of dataclasses for configuration and data structures:

```python
# ✅ Preferred: Pydantic models
class BaseClientConfig(BaseModel):
    """Base configuration for clients."""

    url: str
    timeout: float = Field(default=30.0, ge=0.0)
    max_retries: int = Field(default=3, ge=0)

# ❌ Avoid: Dataclasses
from dataclasses import dataclass

@dataclass
class ClientConfig:
    url: str
    timeout: float = 30.0
```

### Field Validation and Documentation

Use Pydantic Field with validation and descriptions:

```python
class APIConfig(BaseModel):
    """Configuration for API service."""

    host: str = Field(default="localhost", description="API host address")
    port: int = Field(default=8000, ge=1, le=65535, description="API port")
    timeout: float = Field(default=30.0, ge=0.0, description="Request timeout in seconds")
```

## Architectural Patterns

### Abstract Base Classes

Use ABC pattern extensively for defining interfaces:

```python
class BaseClient(abc.ABC):
    """Base class for all clients."""

    @abc.abstractmethod
    async def fetch(self, url: str) -> dict[str, Any]:
        """Fetch data from URL."""
        raise NotImplementedError("Subclasses must implement `fetch()`")

    @abc.abstractmethod
    async def close(self) -> None:
        """Close client connections."""
        raise NotImplementedError("Subclasses must implement `close()`")
```

### Composition over Inheritance

Prefer composition and delegation:

```python
class DataProcessor:
    """Data processing module."""

    def __init__(self, config: ProcessorConfig) -> None:
        self.config: ProcessorConfig = config

        # Compose with specialized components
        self.client: HTTPClient = HTTPClient(config.client_config)
        self.cache: Cache = Cache(config.cache_config)
```

## Error Handling

### Specific Exception Types

Raise specific exceptions with clear messages:

```python
async def fetch(self, url: str) -> dict[str, Any]:
    """Fetch data from URL."""
    stripped_url: str = url.strip()
    if not stripped_url:
        error_msg: str = "URL cannot be empty"
        raise ValueError(error_msg)

    response: dict[str, Any] = await self._send_request(stripped_url)
    return response
```

### Graceful Degradation

Handle failures gracefully with fallbacks:

```python
async def _initialize_cache(self) -> None:
    """Initialize cache with graceful degradation."""
    try:
        cache_config: CacheConfig = self.config.cache_config
        self.cache: RedisCache = RedisCache(cache_config)
    except Exception as e:
        error_msg: str = f"Failed to initialize cache: {e}"
        logger.warning(error_msg)
        self.cache: None = None
```

## Documentation and Naming

### Comprehensive Docstrings

All classes and public methods must have detailed docstrings:

```python
class BaseClient(abc.ABC):
    """Base class for clients.

    This abstract class defines the common interface that all clients
    must implement, ensuring consistent interaction patterns.
    """

    async def fetch(self, url: str) -> dict[str, Any]:
        """Fetch data from URL.

        Args:
            url: The URL to fetch data from

        Returns:
            The fetched data as a dictionary.
        """
```

### Descriptive Variable Names

Use clear, descriptive names:

```python
# ✅ Good: Descriptive names with comprehensive type hints
async def _process_items(self, items: list[dict[str, Any]]) -> list[str]:
    processed_items: list[str] = []

    for item in items:
        item_id: str = item["id"]
        item_value: str = item["value"]
        formatted_item: str = f"{item_id}: {item_value}"
        processed_items.append(formatted_item)

    return processed_items

# ❌ Avoid: Unclear abbreviations
async def _proc_itms(itms):
    result = []
    for i in itms:
        result.append(f"{i['id']}: {i['value']}")
    return result
```

## Class and Interface Design

### Interface Segregation

Keep interfaces focused and cohesive:

```python
class BaseClient(abc.ABC):
    """Base class for clients."""

    @abc.abstractmethod
    async def fetch(self, url: str) -> dict[str, Any]:
        """Fetch data from URL."""

    @abc.abstractmethod
    async def close(self) -> None:
        """Close client connections."""
```

## Code Organization

### Module Structure

Organize modules with clear separation of concerns:

```
src/fluentia/
├── __init__.py
├── clients/
│   ├── __init__.py          # Exports and type aliases
│   ├── base.py              # Abstract base classes
│   ├── http.py              # HTTP client implementation
│   └── redis.py             # Redis client implementation
├── modules/
│   ├── __init__.py
│   ├── base.py              # Base module classes
│   └── processor.py         # Data processor
└── utils/
    ├── __init__.py
    ├── env.py               # Environment utilities
    └── helper.py            # Helper functions
```

### Clean Module Exports

Use explicit `__all__` exports in `__init__.py` files:

```python
"""Client interfaces."""

from fluentia.clients.base import BaseClient, BaseClientConfig
from fluentia.clients.http import HTTPClient, HTTPClientConfig

__all__ = [
    "BaseClient",
    "BaseClientConfig",
    "HTTPClient",
    "HTTPClientConfig",
]
```

## Additional Guidelines

### Logging

Use structured logging with appropriate levels:

```python
import logging

logger: logging.Logger = logging.getLogger(__name__)

class HTTPClient(BaseClient):
    async def fetch(self, url: str) -> dict[str, Any]:
        try:
            logger.info(f"Fetching data from: {url}")
            response: dict[str, Any] = await self._request(url)
            return response
        except Exception as e:
            error_msg: str = f"Failed to fetch from {url}: {e}"
            logger.error(error_msg)
            raise
```

### Line Length and Formatting

Follow these formatting guidelines:

- Maximum line length: 100 characters
- Use trailing commas in multi-line structures
- Use `ruff format` for consistent formatting
- Break long lines at logical points

```python
# ✅ Good formatting with type hints
async def fetch_data(self, urls: list[str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for url in urls:
        response: dict[str, Any] = await self.client.fetch(
            url=url,
            timeout=self.config.timeout,
            retries=self.config.max_retries,
        )
        results.append(response)

    return results
```

By following these guidelines, code will be consistent, maintainable, and easy to understand for both new and experienced developers working on the Fluentia repository.
