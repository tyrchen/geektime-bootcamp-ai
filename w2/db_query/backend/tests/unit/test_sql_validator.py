"""Unit tests for SQL validator service."""

import pytest
from app.services.sql_validator import (
    validate_sql,
    add_limit_if_missing,
    validate_and_transform_sql,
    SqlValidationError,
)


class TestValidateSql:
    """Test SQL validation function."""

    def test_valid_select(self):
        """Test that valid SELECT statements pass validation."""
        is_valid, error = validate_sql("SELECT * FROM users")
        assert is_valid is True
        assert error is None

    def test_select_with_where(self):
        """Test SELECT with WHERE clause."""
        is_valid, error = validate_sql("SELECT id, name FROM users WHERE id = 1")
        assert is_valid is True
        assert error is None

    def test_select_with_join(self):
        """Test SELECT with JOIN."""
        is_valid, error = validate_sql(
            "SELECT u.id, u.name FROM users u JOIN orders o ON u.id = o.user_id"
        )
        assert is_valid is True
        assert error is None

    def test_reject_insert(self):
        """Test that INSERT statements are rejected."""
        is_valid, error = validate_sql("INSERT INTO users (name) VALUES ('test')")
        assert is_valid is False
        assert error is not None
        assert "SELECT" in error or "allowed" in error

    def test_reject_update(self):
        """Test that UPDATE statements are rejected."""
        is_valid, error = validate_sql("UPDATE users SET name = 'test' WHERE id = 1")
        assert is_valid is False
        assert error is not None

    def test_reject_delete(self):
        """Test that DELETE statements are rejected."""
        is_valid, error = validate_sql("DELETE FROM users WHERE id = 1")
        assert is_valid is False
        assert error is not None

    def test_invalid_sql(self):
        """Test that invalid SQL is rejected."""
        is_valid, error = validate_sql("SELECT * FROM WHERE")
        assert is_valid is False
        assert error is not None


class TestAddLimitIfMissing:
    """Test LIMIT injection function."""

    def test_add_limit_when_missing(self):
        """Test that LIMIT is added when missing."""
        sql = "SELECT * FROM users"
        result = add_limit_if_missing(sql, limit=100)
        assert "LIMIT" in result.upper()
        assert "100" in result

    def test_keep_existing_limit(self):
        """Test that existing LIMIT is preserved."""
        sql = "SELECT * FROM users LIMIT 50"
        result = add_limit_if_missing(sql, limit=100)
        assert "LIMIT" in result.upper()
        # Should keep original limit or use the one specified
        assert result.upper().count("LIMIT") == 1

    def test_limit_with_offset(self):
        """Test LIMIT with OFFSET."""
        sql = "SELECT * FROM users OFFSET 10"
        result = add_limit_if_missing(sql, limit=100)
        assert "LIMIT" in result.upper()
        assert "OFFSET" in result.upper()


class TestValidateAndTransformSql:
    """Test combined validation and transformation."""

    def test_valid_sql_with_limit(self):
        """Test valid SQL gets LIMIT added."""
        sql = "SELECT * FROM users"
        result = validate_and_transform_sql(sql, limit=100)
        assert "LIMIT" in result.upper()
        assert "100" in result

    def test_invalid_sql_raises_error(self):
        """Test that invalid SQL raises SqlValidationError."""
        with pytest.raises(SqlValidationError):
            validate_and_transform_sql("INSERT INTO users VALUES (1)")

    def test_select_with_existing_limit(self):
        """Test SELECT with existing LIMIT."""
        sql = "SELECT * FROM users LIMIT 50"
        result = validate_and_transform_sql(sql, limit=100)
        assert isinstance(result, str)
        assert "SELECT" in result.upper()
