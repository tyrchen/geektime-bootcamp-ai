# Testing Guide

This document describes the testing infrastructure for the PostgreSQL MCP Server.

## Test Structure

```
tests/
├── __init__.py           # Test package initialization
├── conftest.py           # Shared pytest fixtures
├── mocks/                # Mock implementations
│   ├── __init__.py
│   ├── asyncpg.py       # Mock asyncpg pool and connection
│   └── openai.py        # Mock OpenAI client
├── test_sql_validator.py    # SQLValidator unit tests
├── test_sql_generator.py    # SQLGenerator unit tests
├── test_sql_executor.py     # SQLExecutor unit tests
└── test_orchestrator.py     # QueryOrchestrator integration tests
```

## Running Tests

### Basic Usage

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_sql_validator.py

# Run specific test class
pytest tests/test_sql_validator.py::TestSQLValidator

# Run specific test
pytest tests/test_sql_validator.py::TestSQLValidator::test_validate_select_query

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=pg_mcp --cov-report=html
```

### Using the Test Runner

```bash
# Run all tests via script
python run_tests.py
```

### Test Markers

Tests are organized with markers:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## Test Fixtures

Common fixtures are defined in `conftest.py`:

### `test_db_config`
Returns a `DatabaseConfig` instance for testing.

### `test_settings`
Returns a complete `Settings` instance with all configurations.

### `sample_schema`
Returns a sample database schema for testing SQL generation.

## Mock Infrastructure

### MockPool (asyncpg)

Mock PostgreSQL connection pool:

```python
from tests.mocks.asyncpg import create_mock_pool

# Create pool with test data
pool = create_mock_pool([
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"},
])

# Use in tests
async with pool.acquire() as conn:
    results = await conn.fetch("SELECT * FROM users")
    assert len(results) == 2
```

Features:
- Returns predefined records
- Tracks executed SQL
- Simulates connection lifecycle
- Supports transactions

### MockAsyncOpenAI

Mock OpenAI client for LLM testing:

```python
from tests.mocks.openai import create_mock_openai_client

# Create client with custom SQL response
client = create_mock_openai_client(
    sql_response="SELECT * FROM users WHERE active = true"
)

# Use in tests
response = await client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Show active users"}]
)

# Check call tracking
assert client.chat.completions.call_count == 1
assert client.chat.completions.last_model == "gpt-4o-mini"
```

Features:
- Configurable SQL responses
- SQL sequence for retry testing
- Token usage tracking
- Call count tracking
- Message history

## Test Coverage

Current test coverage:

| Component | Tests | Coverage |
|-----------|-------|----------|
| SQLValidator | 22 tests | Comprehensive |
| SQLGenerator | 10 tests | Comprehensive |
| SQLExecutor | 12 tests | Comprehensive |
| QueryOrchestrator | 15 tests | Comprehensive |

### Coverage Goals

- Unit tests: 80%+ coverage
- Integration tests: Key user flows
- Security tests: All validation paths

### Generating Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=pg_mcp --cov-report=html

# View report
open htmlcov/index.html

# Generate terminal report
pytest --cov=pg_mcp --cov-report=term-missing
```

## Test Categories

### Unit Tests

Test individual components in isolation:

- **SQLValidator**: Query security validation
- **SQLGenerator**: SQL generation from natural language
- **SQLExecutor**: Query execution and result serialization
- **SchemaCache**: Schema caching logic
- **RetryLogic**: Exponential backoff implementation

### Integration Tests

Test component interactions:

- **QueryOrchestrator**: End-to-end query processing
- **Multi-database routing**: Database selection and routing
- **Rate limiting**: LLM and DB rate limit enforcement
- **Metrics tracking**: Prometheus metrics collection

### Security Tests

Test security controls:

- Blocked tables/columns rejection
- Dangerous function detection
- Multiple statement prevention
- EXPLAIN query handling
- SQL injection prevention

## Writing New Tests

### Test Template

```python
"""Unit tests for MyComponent."""

import pytest
from pg_mcp.services.my_component import MyComponent


class TestMyComponent:
    """Test suite for MyComponent."""

    @pytest.fixture
    def component(self, test_settings):
        """Create component instance."""
        return MyComponent(test_settings)

    def test_basic_functionality(self, component):
        """Test basic component functionality."""
        result = component.do_something()
        assert result is not None

    def test_error_handling(self, component):
        """Test error handling."""
        with pytest.raises(ValueError):
            component.do_invalid_thing()
```

### Best Practices

1. **Use descriptive test names**: `test_validate_rejects_drop_table`
2. **One assertion per test**: Focus on single behavior
3. **Use fixtures**: Reuse common setup code
4. **Test edge cases**: Empty inputs, None, large values
5. **Test error paths**: Exceptions and error states
6. **Mock external dependencies**: Use mocks for I/O
7. **Keep tests fast**: Unit tests should be < 100ms
8. **Document complex tests**: Add docstrings explaining intent

## Continuous Integration

Tests run automatically on:

- Push to main/develop branches
- Pull requests
- GitHub Actions workflow

See `.github/workflows/tests.yml` for configuration.

### CI Test Matrix

- Python 3.11
- Python 3.12
- Linting (ruff)
- Type checking (mypy)
- Coverage reporting

## Troubleshooting

### Common Issues

**Import Errors**

```bash
# Install package in development mode
pip install -e ".[dev]"
```

**Async Test Failures**

```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio>=1.3.0
```

**Coverage Not Working**

```bash
# Reinstall with coverage support
pip install pytest-cov
```

### Debug Mode

```bash
# Run with debug output
pytest -vv --log-cli-level=DEBUG

# Drop into debugger on failure
pytest --pdb

# Print statements visible
pytest -s
```

## Performance Testing

For performance-sensitive code:

```python
import time

def test_performance(benchmark):
    """Test execution performance."""
    def run_query():
        # Code to benchmark
        pass
    
    result = benchmark(run_query)
    assert result is not None
```

## Future Enhancements

- [ ] Property-based testing with Hypothesis
- [ ] Performance benchmarks with pytest-benchmark
- [ ] E2E tests with real PostgreSQL (Docker)
- [ ] Mutation testing with mutmut
- [ ] Snapshot testing for SQL generation

## References

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
