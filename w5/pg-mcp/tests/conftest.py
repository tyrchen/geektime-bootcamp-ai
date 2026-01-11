"""Pytest configuration and shared fixtures.

This module provides shared fixtures and configuration for all tests.
"""

import os

import pytest

from pg_mcp.config.settings import (
    CacheConfig,
    DatabaseConfig,
    OpenAIConfig,
    ResilienceConfig,
    SecurityConfig,
    Settings,
    ValidationConfig,
    reset_settings,
)
from pg_mcp.models.schema import ColumnInfo, DatabaseSchema, TableInfo


@pytest.fixture(autouse=True)
def reset_config() -> None:
    """Reset global settings before each test."""
    reset_settings()


@pytest.fixture(autouse=True)
def disable_metrics_for_tests():
    """Disable metrics for tests to avoid port conflicts."""
    os.environ["OBSERVABILITY_METRICS_ENABLED"] = "false"
    yield
    # Clean up
    if "OBSERVABILITY_METRICS_ENABLED" in os.environ:
        del os.environ["OBSERVABILITY_METRICS_ENABLED"]


@pytest.fixture
def test_db_config():
    """Test database configuration."""
    return DatabaseConfig(
        name="test_db",
        host="localhost",
        port=5432,
        database="test_database",
        user="test_user",
        password="test_password",
        min_pool_size=1,
        max_pool_size=5,
        pool_timeout=10.0,
        command_timeout=10.0,
    )


@pytest.fixture
def test_settings(test_db_config):
    """Test application settings."""
    return Settings(
        environment="development",
        databases=[test_db_config],
        openai=OpenAIConfig(
            api_key="sk-test-key-12345",
            model="gpt-4",
            temperature=0.0,
            max_tokens=1000,
            timeout=30.0,
        ),
        security=SecurityConfig(
            max_execution_time=30.0,
            max_rows=1000,
            readonly_role="readonly",
            safe_search_path="public",
            blocked_functions=["pg_sleep"],
            blocked_tables=[],
            blocked_columns=[],
            allow_explain=False,
        ),
        validation=ValidationConfig(
            min_confidence_threshold=70,
            max_question_length=500,
        ),
        cache=CacheConfig(
            enabled=True,
            schema_ttl=3600,
            max_size=100,
        ),
        resilience=ResilienceConfig(
            max_retries=3,
            retry_delay=1.0,
            circuit_breaker_threshold=5,
            circuit_breaker_timeout=60.0,
        ),
    )


@pytest.fixture
def sample_schema():
    """Sample database schema for testing."""
    return DatabaseSchema(
        database_name="test_db",
        tables=[
            TableInfo(
                schema_name="public",
                table_name="users",
                columns=[
                    ColumnInfo(
                        name="id",
                        data_type="integer",
                        is_nullable=False,
                        is_primary_key=True,
                    ),
                    ColumnInfo(
                        name="email",
                        data_type="character varying",
                        is_nullable=False,
                    ),
                    ColumnInfo(
                        name="name",
                        data_type="character varying",
                        is_nullable=True,
                    ),
                    ColumnInfo(
                        name="created_at",
                        data_type="timestamp with time zone",
                        is_nullable=False,
                        default_value="CURRENT_TIMESTAMP",
                    ),
                ],
            ),
            TableInfo(
                schema_name="public",
                table_name="posts",
                columns=[
                    ColumnInfo(
                        name="id",
                        data_type="integer",
                        is_nullable=False,
                        is_primary_key=True,
                    ),
                    ColumnInfo(
                        name="user_id",
                        data_type="integer",
                        is_nullable=False,
                    ),
                    ColumnInfo(
                        name="title",
                        data_type="character varying",
                        is_nullable=False,
                    ),
                    ColumnInfo(
                        name="content",
                        data_type="text",
                        is_nullable=True,
                    ),
                    ColumnInfo(
                        name="published_at",
                        data_type="timestamp with time zone",
                        is_nullable=True,
                    ),
                ],
            ),
        ],
    )

