"""Unit tests for SQLGenerator."""

import pytest
from unittest.mock import patch

from pg_mcp.config.settings import OpenAIConfig
from pg_mcp.models.errors import LLMError, LLMTimeoutError
from pg_mcp.services.sql_generator import SQLGenerator
from tests.mocks.openai import create_mock_openai_client


class TestSQLGenerator:
    """Test suite for SQLGenerator."""

    @pytest.fixture
    def openai_config(self):
        """Create OpenAI configuration."""
        return OpenAIConfig(
            api_key="sk-test-key",
            model="gpt-4",
            temperature=0.0,
            max_tokens=1000,
            timeout=30.0,
        )

    def test_generate_simple_query(self, openai_config, sample_schema):
        """Test generating a simple SQL query."""
        expected_sql = "SELECT COUNT(*) FROM users"
        mock_client = create_mock_openai_client(sql_response=f"```sql\n{expected_sql}\n```")
        
        with patch("pg_mcp.services.sql_generator.AsyncOpenAI", return_value=mock_client):
            generator = SQLGenerator(openai_config)
            result = asyncio.run(
                generator.generate(
                    question="How many users are there?",
                    schema=sample_schema,
                )
            )
        
        assert result == expected_sql
        assert mock_client.chat.completions.call_count == 1

    def test_generate_with_context(self, openai_config, sample_schema):
        """Test generating SQL with additional context."""
        expected_sql = "SELECT * FROM users WHERE active = true"
        mock_client = create_mock_openai_client(sql_response=expected_sql)
        
        with patch("pg_mcp.services.sql_generator.AsyncOpenAI", return_value=mock_client):
            generator = SQLGenerator(openai_config)
            result = asyncio.run(
                generator.generate(
                    question="List active users",
                    schema=sample_schema,
                    context="Only include active users",
                )
            )
        
        assert result == expected_sql

    def test_generate_with_retry_feedback(self, openai_config, sample_schema):
        """Test generating SQL with error feedback for retry."""
        expected_sql = "SELECT COUNT(*) FROM users WHERE active = true"
        mock_client = create_mock_openai_client(sql_response=expected_sql)
        
        with patch("pg_mcp.services.sql_generator.AsyncOpenAI", return_value=mock_client):
            generator = SQLGenerator(openai_config)
            result = asyncio.run(
                generator.generate(
                    question="Count active users",
                    schema=sample_schema,
                    previous_attempt="SELECT COUNT(*) FROM user",
                    error_feedback='relation "user" does not exist',
                )
            )
        
        assert result == expected_sql
        # Verify feedback was included in messages
        messages = mock_client.chat.completions.last_messages
        assert any("user" in str(msg).lower() for msg in messages)

    def test_extract_sql_from_code_block(self, openai_config, sample_schema):
        """Test extracting SQL from code blocks."""
        sql_with_block = "```sql\nSELECT * FROM users\n```"
        mock_client = create_mock_openai_client(sql_response=sql_with_block)
        
        with patch("pg_mcp.services.sql_generator.AsyncOpenAI", return_value=mock_client):
            generator = SQLGenerator(openai_config)
            result = asyncio.run(
                generator.generate(
                    question="List users",
                    schema=sample_schema,
                )
            )
        
        assert result == "SELECT * FROM users"
        assert "```" not in result

    def test_extract_sql_from_generic_code_block(self, openai_config, sample_schema):
        """Test extracting SQL from generic code blocks."""
        sql_with_block = "```\nSELECT * FROM posts\n```"
        mock_client = create_mock_openai_client(sql_response=sql_with_block)
        
        with patch("pg_mcp.services.sql_generator.AsyncOpenAI", return_value=mock_client):
            generator = SQLGenerator(openai_config)
            result = asyncio.run(
                generator.generate(
                    question="List posts",
                    schema=sample_schema,
                )
            )
        
        assert result == "SELECT * FROM posts"

    def test_extract_sql_from_plain_text(self, openai_config, sample_schema):
        """Test extracting SQL from plain text response."""
        plain_sql = "Here's the SQL: SELECT id, name FROM users WHERE active = true"
        mock_client = create_mock_openai_client(sql_response=plain_sql)
        
        with patch("pg_mcp.services.sql_generator.AsyncOpenAI", return_value=mock_client):
            generator = SQLGenerator(openai_config)
            result = asyncio.run(
                generator.generate(
                    question="Get active users",
                    schema=sample_schema,
                )
            )
        
        assert "SELECT" in result
        assert "FROM users" in result

    def test_remove_trailing_semicolon(self, openai_config, sample_schema):
        """Test that trailing semicolons are removed."""
        sql_with_semicolon = "SELECT * FROM users;"
        mock_client = create_mock_openai_client(sql_response=sql_with_semicolon)
        
        with patch("pg_mcp.services.sql_generator.AsyncOpenAI", return_value=mock_client):
            generator = SQLGenerator(openai_config)
            result = asyncio.run(
                generator.generate(
                    question="List users",
                    schema=sample_schema,
                )
            )
        
        assert result == "SELECT * FROM users"
        assert not result.endswith(";")

    def test_empty_response_error(self, openai_config, sample_schema):
        """Test error handling for empty responses."""
        mock_client = create_mock_openai_client(sql_response="")
        
        with patch("pg_mcp.services.sql_generator.AsyncOpenAI", return_value=mock_client):
            generator = SQLGenerator(openai_config)
            with pytest.raises(LLMError) as exc_info:
                asyncio.run(
                    generator.generate(
                        question="Test",
                        schema=sample_schema,
                    )
                )
        
        assert "Failed to extract SQL" in str(exc_info.value)


# Import asyncio for running async tests
import asyncio
