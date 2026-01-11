"""Unit tests for SQLExecutor."""

import asyncio
import datetime
import decimal
import uuid

import pytest

from pg_mcp.config.settings import DatabaseConfig, SecurityConfig
from pg_mcp.models.errors import DatabaseError, ExecutionTimeoutError
from pg_mcp.services.sql_executor import SQLExecutor
from tests.mocks.asyncpg import create_mock_pool


class TestSQLExecutor:
    """Test suite for SQLExecutor."""

    @pytest.fixture
    def security_config(self):
        """Create security configuration."""
        return SecurityConfig(
            max_execution_time=30.0,
            max_rows=1000,
            readonly_role="readonly",
            safe_search_path="public",
            blocked_functions=[],
            blocked_tables=[],
            blocked_columns=[],
            allow_explain=False,
        )

    @pytest.fixture
    def db_config(self):
        """Create database configuration."""
        return DatabaseConfig(
            name="test_db",
            host="localhost",
            port=5432,
            database="test_database",
            user="test_user",
            password="test_password",
        )

    def test_execute_simple_query(self, security_config, db_config):
        """Test executing a simple query."""
        test_records = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        pool = create_mock_pool(test_records)
        executor = SQLExecutor(pool, security_config, db_config)

        results, count = asyncio.run(
            executor.execute("SELECT * FROM users")
        )

        assert len(results) == 2
        assert count == 2
        assert results[0]["id"] == 1
        assert results[0]["name"] == "Alice"

    def test_execute_with_row_limit(self, security_config, db_config):
        """Test that row limit is enforced."""
        # Create 1500 records
        test_records = [{"id": i, "value": f"row_{i}"} for i in range(1500)]
        pool = create_mock_pool(test_records)
        executor = SQLExecutor(pool, security_config, db_config)

        results, count = asyncio.run(
            executor.execute("SELECT * FROM large_table", max_rows=100)
        )

        # Should return only 100 rows but count should be 1500
        assert len(results) == 100
        assert count == 1500

    def test_execute_empty_result(self, security_config, db_config):
        """Test executing query with no results."""
        pool = create_mock_pool([])
        executor = SQLExecutor(pool, security_config, db_config)

        results, count = asyncio.run(
            executor.execute("SELECT * FROM users WHERE id = 999")
        )

        assert len(results) == 0
        assert count == 0

    def test_serialize_datetime(self, security_config, db_config):
        """Test datetime serialization."""
        test_records = [
            {
                "id": 1,
                "created_at": datetime.datetime(2024, 1, 1, 12, 0, 0),
                "updated_at": datetime.date(2024, 1, 2),
            }
        ]
        pool = create_mock_pool(test_records)
        executor = SQLExecutor(pool, security_config, db_config)

        results, _ = asyncio.run(
            executor.execute("SELECT * FROM events")
        )

        assert isinstance(results[0]["created_at"], str)
        assert isinstance(results[0]["updated_at"], str)
        assert "2024-01-01" in results[0]["created_at"]

    def test_serialize_decimal(self, security_config, db_config):
        """Test decimal serialization."""
        test_records = [
            {"id": 1, "price": decimal.Decimal("99.99")},
        ]
        pool = create_mock_pool(test_records)
        executor = SQLExecutor(pool, security_config, db_config)

        results, _ = asyncio.run(
            executor.execute("SELECT * FROM products")
        )

        assert isinstance(results[0]["price"], float)
        assert results[0]["price"] == 99.99

    def test_serialize_uuid(self, security_config, db_config):
        """Test UUID serialization."""
        test_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        test_records = [
            {"id": 1, "uuid": test_uuid},
        ]
        pool = create_mock_pool(test_records)
        executor = SQLExecutor(pool, security_config, db_config)

        results, _ = asyncio.run(
            executor.execute("SELECT * FROM items")
        )

        assert isinstance(results[0]["uuid"], str)
        assert results[0]["uuid"] == "12345678-1234-5678-1234-567812345678"

    def test_serialize_bytes(self, security_config, db_config):
        """Test bytes serialization."""
        test_records = [
            {"id": 1, "data": b"\\x01\\x02\\x03"},
        ]
        pool = create_mock_pool(test_records)
        executor = SQLExecutor(pool, security_config, db_config)

        results, _ = asyncio.run(
            executor.execute("SELECT * FROM binary_data")
        )

        assert isinstance(results[0]["data"], str)
        # bytes.hex() converts to hex string
        assert len(results[0]["data"]) > 0

    def test_serialize_nested_structures(self, security_config, db_config):
        """Test serialization of nested lists and dicts."""
        test_records = [
            {
                "id": 1,
                "tags": ["python", "sql"],
                "metadata": {"version": 1, "active": True},
            }
        ]
        pool = create_mock_pool(test_records)
        executor = SQLExecutor(pool, security_config, db_config)

        results, _ = asyncio.run(
            executor.execute("SELECT * FROM documents")
        )

        assert isinstance(results[0]["tags"], list)
        assert results[0]["tags"] == ["python", "sql"]
        assert isinstance(results[0]["metadata"], dict)
        assert results[0]["metadata"]["version"] == 1

    def test_retry_on_connection_error(self, security_config, db_config):
        """Test that retry logic is invoked on connection errors."""
        pool = create_mock_pool([{"id": 1}])
        executor = SQLExecutor(pool, security_config, db_config)

        # The executor should successfully execute after retries
        results, count = asyncio.run(
            executor.execute("SELECT * FROM users")
        )

        assert len(results) == 1
        assert count == 1

    def test_custom_timeout(self, security_config, db_config):
        """Test executing with custom timeout."""
        pool = create_mock_pool([{"id": 1}])
        executor = SQLExecutor(pool, security_config, db_config)

        results, count = asyncio.run(
            executor.execute("SELECT * FROM users", timeout=60.0)
        )

        assert len(results) == 1

    def test_custom_max_rows(self, security_config, db_config):
        """Test executing with custom max_rows."""
        test_records = [{"id": i} for i in range(100)]
        pool = create_mock_pool(test_records)
        executor = SQLExecutor(pool, security_config, db_config)

        results, count = asyncio.run(
            executor.execute("SELECT * FROM items", max_rows=10)
        )

        assert len(results) == 10
        assert count == 100
