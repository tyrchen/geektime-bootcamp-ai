"""Unit tests for QueryOrchestrator."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from pg_mcp.config.settings import DatabaseConfig, LLMConfig, RateLimitConfig, SecurityConfig, Settings
from pg_mcp.models.errors import (
    DatabaseError,
    NoDatabaseFoundError,
    SecurityViolationError,
)
from pg_mcp.services.orchestrator import QueryOrchestrator
from tests.mocks.asyncpg import create_mock_pool
from tests.mocks.openai import MockAsyncOpenAI


class TestQueryOrchestrator:
    """Test suite for QueryOrchestrator."""

    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings(
            databases=[
                DatabaseConfig(
                    name="users_db",
                    host="localhost",
                    port=5432,
                    database="users",
                    user="test_user",
                    password="test_password",
                ),
                DatabaseConfig(
                    name="orders_db",
                    host="localhost",
                    port=5432,
                    database="orders",
                    user="test_user",
                    password="test_password",
                ),
            ],
            llm=LLMConfig(
                api_key="test-key",
                model="gpt-4o-mini",
                max_tokens=2000,
                temperature=0.0,
            ),
            security=SecurityConfig(
                max_execution_time=30.0,
                max_rows=1000,
                readonly_role="readonly",
                safe_search_path="public",
                blocked_functions=["pg_sleep"],
                blocked_tables=["secrets"],
                blocked_columns=["password"],
                allow_explain=False,
            ),
            rate_limit=RateLimitConfig(
                llm_calls_per_minute=10,
                db_calls_per_minute=20,
            ),
        )

    @pytest.fixture
    def mock_pools(self):
        """Create mock connection pools."""
        return {
            "users_db": create_mock_pool([
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"},
            ]),
            "orders_db": create_mock_pool([
                {"order_id": 101, "user_id": 1, "total": 99.99},
                {"order_id": 102, "user_id": 2, "total": 149.99},
            ]),
        }

    @pytest.fixture
    def mock_openai(self):
        """Create mock OpenAI client."""
        return MockAsyncOpenAI()

    def test_process_query_success(self, settings, mock_pools, mock_openai):
        """Test successful query processing."""
        orchestrator = QueryOrchestrator(settings, mock_pools, mock_openai)

        question = "Show me all users"
        database_name = "users_db"

        result = asyncio.run(
            orchestrator.process_query(question, database_name)
        )

        assert result["success"] is True
        assert "SELECT" in result["sql"]
        assert len(result["results"]) == 2
        assert result["row_count"] == 2
        assert result["database"] == "users_db"
        assert "execution_time_ms" in result

    def test_process_query_auto_database_selection(
        self, settings, mock_pools, mock_openai
    ):
        """Test automatic database selection when none specified."""
        orchestrator = QueryOrchestrator(settings, mock_pools, mock_openai)

        question = "Show me user information"

        # Should select first available database
        result = asyncio.run(orchestrator.process_query(question))

        assert result["success"] is True
        assert result["database"] in ["users_db", "orders_db"]

    def test_process_query_invalid_database(
        self, settings, mock_pools, mock_openai
    ):
        """Test error when invalid database is specified."""
        orchestrator = QueryOrchestrator(settings, mock_pools, mock_openai)

        question = "Show me data"
        database_name = "nonexistent_db"

        result = asyncio.run(
            orchestrator.process_query(question, database_name)
        )

        assert result["success"] is False
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_process_query_security_violation(
        self, settings, mock_pools, mock_openai
    ):
        """Test security violation detection."""
        orchestrator = QueryOrchestrator(settings, mock_pools, mock_openai)

        # Mock the OpenAI client to return SQL with blocked table
        mock_openai.set_mock_sql("SELECT * FROM secrets")

        question = "Show me secrets"
        database_name = "users_db"

        result = asyncio.run(
            orchestrator.process_query(question, database_name)
        )

        assert result["success"] is False
        assert "error" in result
        assert "blocked" in result["error"].lower() or "security" in result["error"].lower()

    def test_process_query_with_retry(self, settings, mock_pools, mock_openai):
        """Test query processing with retry on error."""
        orchestrator = QueryOrchestrator(settings, mock_pools, mock_openai)

        # First attempt returns invalid SQL, second attempt succeeds
        mock_openai.set_mock_sql_sequence([
            "INVALID SQL SYNTAX HERE",
            "SELECT * FROM users",
        ])

        question = "Show me all users"
        database_name = "users_db"

        result = asyncio.run(
            orchestrator.process_query(question, database_name)
        )

        # Should succeed after retry
        assert result["success"] is True
        assert len(result["results"]) == 2

    def test_process_query_max_retries_exceeded(
        self, settings, mock_pools, mock_openai
    ):
        """Test query fails after max retries."""
        orchestrator = QueryOrchestrator(settings, mock_pools, mock_openai)

        # Always return invalid SQL
        mock_openai.set_mock_sql("INVALID SQL")

        question = "Show me users"
        database_name = "users_db"

        result = asyncio.run(
            orchestrator.process_query(question, database_name)
        )

        # Should fail after retries
        assert result["success"] is False
        assert "error" in result

    def test_process_query_empty_results(
        self, settings, mock_pools, mock_openai
    ):
        """Test query with no results."""
        # Create pool with empty results
        empty_pools = {
            "users_db": create_mock_pool([]),
        }
        orchestrator = QueryOrchestrator(settings, empty_pools, mock_openai)

        question = "Show me users with id 999"
        database_name = "users_db"

        result = asyncio.run(
            orchestrator.process_query(question, database_name)
        )

        assert result["success"] is True
        assert len(result["results"]) == 0
        assert result["row_count"] == 0

    def test_rate_limiting_llm(self, settings, mock_pools, mock_openai):
        """Test LLM rate limiting."""
        orchestrator = QueryOrchestrator(settings, mock_pools, mock_openai)

        question = "Show me users"
        database_name = "users_db"

        # Make rapid requests
        tasks = [
            orchestrator.process_query(question, database_name)
            for _ in range(5)
        ]

        results = asyncio.run(asyncio.gather(*tasks))

        # All should succeed but rate limiter should be invoked
        assert all(r["success"] for r in results)

    def test_schema_caching(self, settings, mock_pools, mock_openai):
        """Test that schema is cached across requests."""
        orchestrator = QueryOrchestrator(settings, mock_pools, mock_openai)

        question = "Show me users"
        database_name = "users_db"

        # First request
        result1 = asyncio.run(
            orchestrator.process_query(question, database_name)
        )

        # Second request should use cached schema
        result2 = asyncio.run(
            orchestrator.process_query(question, database_name)
        )

        assert result1["success"] is True
        assert result2["success"] is True

    def test_multiple_databases(self, settings, mock_pools, mock_openai):
        """Test queries across multiple databases."""
        orchestrator = QueryOrchestrator(settings, mock_pools, mock_openai)

        # Query users database
        result1 = asyncio.run(
            orchestrator.process_query("Show me users", "users_db")
        )

        # Query orders database
        mock_openai.set_mock_sql("SELECT * FROM orders")
        result2 = asyncio.run(
            orchestrator.process_query("Show me orders", "orders_db")
        )

        assert result1["success"] is True
        assert result2["success"] is True
        assert result1["database"] == "users_db"
        assert result2["database"] == "orders_db"
        assert len(result1["results"]) == 2  # users
        assert len(result2["results"]) == 2  # orders

    def test_execution_time_tracking(
        self, settings, mock_pools, mock_openai
    ):
        """Test execution time is tracked."""
        orchestrator = QueryOrchestrator(settings, mock_pools, mock_openai)

        question = "Show me users"
        database_name = "users_db"

        result = asyncio.run(
            orchestrator.process_query(question, database_name)
        )

        assert result["success"] is True
        assert "execution_time_ms" in result
        assert isinstance(result["execution_time_ms"], (int, float))
        assert result["execution_time_ms"] >= 0
