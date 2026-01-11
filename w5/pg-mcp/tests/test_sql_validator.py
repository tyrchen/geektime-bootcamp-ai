"""Unit tests for SQLValidator."""

import pytest

from pg_mcp.config.settings import SecurityConfig
from pg_mcp.models.errors import SecurityViolationError, SQLParseError
from pg_mcp.services.sql_validator import SQLValidator


class TestSQLValidator:
    """Test suite for SQLValidator."""

    @pytest.fixture
    def validator(self):
        """Create SQL validator with default config."""
        config = SecurityConfig(
            max_execution_time=30.0,
            max_rows=1000,
            readonly_role="readonly",
            safe_search_path="public",
            blocked_functions=["custom_dangerous_func"],
            blocked_tables=[],
            blocked_columns=[],
            allow_explain=False,
        )
        return SQLValidator(config)

    def test_valid_select_query(self, validator):
        """Test that valid SELECT queries pass validation."""
        sql = "SELECT id, name FROM users WHERE active = true"
        validator.validate_or_raise(sql)  # Should not raise

    def test_select_with_join(self, validator):
        """Test that SELECT with JOIN passes validation."""
        sql = """
        SELECT u.id, u.name, p.title
        FROM users u
        JOIN posts p ON u.id = p.user_id
        WHERE u.active = true
        """
        validator.validate_or_raise(sql)  # Should not raise

    def test_select_with_cte(self, validator):
        """Test that CTEs (WITH) pass validation."""
        sql = """
        WITH active_users AS (
            SELECT id, name FROM users WHERE active = true
        )
        SELECT * FROM active_users
        """
        validator.validate_or_raise(sql)  # Should not raise

    def test_reject_insert(self, validator):
        """Test that INSERT is rejected."""
        sql = "INSERT INTO users (name) VALUES ('test')"
        with pytest.raises(SecurityViolationError) as exc_info:
            validator.validate_or_raise(sql)
        assert "INSERT" in str(exc_info.value)

    def test_reject_update(self, validator):
        """Test that UPDATE is rejected."""
        sql = "UPDATE users SET active = false WHERE id = 1"
        with pytest.raises(SecurityViolationError) as exc_info:
            validator.validate_or_raise(sql)
        assert "UPDATE" in str(exc_info.value)

    def test_reject_delete(self, validator):
        """Test that DELETE is rejected."""
        sql = "DELETE FROM users WHERE id = 1"
        with pytest.raises(SecurityViolationError) as exc_info:
            validator.validate_or_raise(sql)
        assert "DELETE" in str(exc_info.value)

    def test_reject_drop(self, validator):
        """Test that DROP is rejected."""
        sql = "DROP TABLE users"
        with pytest.raises(SecurityViolationError) as exc_info:
            validator.validate_or_raise(sql)
        assert "DROP" in str(exc_info.value)

    def test_reject_multiple_statements(self, validator):
        """Test that multiple statements are rejected."""
        sql = "SELECT * FROM users; SELECT * FROM posts"
        with pytest.raises(SecurityViolationError) as exc_info:
            validator.validate_or_raise(sql)
        assert "Multiple statements" in str(exc_info.value)

    def test_reject_pg_sleep(self, validator):
        """Test that pg_sleep function is blocked."""
        sql = "SELECT pg_sleep(10)"
        with pytest.raises(SecurityViolationError) as exc_info:
            validator.validate_or_raise(sql)
        assert "pg_sleep" in str(exc_info.value)

    def test_reject_custom_blocked_function(self, validator):
        """Test that custom blocked functions are rejected."""
        sql = "SELECT custom_dangerous_func()"
        with pytest.raises(SecurityViolationError) as exc_info:
            validator.validate_or_raise(sql)
        assert "custom_dangerous_func" in str(exc_info.value)

    def test_reject_blocked_table(self):
        """Test that blocked tables are rejected."""
        config = SecurityConfig(
            blocked_tables=["sensitive_data"],
        )
        validator = SQLValidator(config, blocked_tables=["sensitive_data"])
        
        sql = "SELECT * FROM sensitive_data"
        with pytest.raises(SecurityViolationError) as exc_info:
            validator.validate_or_raise(sql)
        assert "sensitive_data" in str(exc_info.value)

    def test_reject_blocked_column(self):
        """Test that blocked columns are rejected."""
        config = SecurityConfig(
            blocked_columns=["password"],
        )
        validator = SQLValidator(config, blocked_columns=["password"])
        
        sql = "SELECT id, password FROM users"
        with pytest.raises(SecurityViolationError) as exc_info:
            validator.validate_or_raise(sql)
        assert "password" in str(exc_info.value)

    def test_reject_explain_when_disabled(self, validator):
        """Test that EXPLAIN is rejected when disabled."""
        sql = "EXPLAIN SELECT * FROM users"
        with pytest.raises(SecurityViolationError) as exc_info:
            validator.validate_or_raise(sql)
        assert "EXPLAIN" in str(exc_info.value)

    def test_allow_explain_when_enabled(self):
        """Test that EXPLAIN is allowed when enabled."""
        config = SecurityConfig(allow_explain=True)
        validator = SQLValidator(config, allow_explain=True)
        
        sql = "EXPLAIN SELECT * FROM users"
        validator.validate_or_raise(sql)  # Should not raise

    def test_empty_sql(self, validator):
        """Test that empty SQL is rejected."""
        with pytest.raises(SQLParseError):
            validator.validate_or_raise("")

    def test_invalid_sql(self, validator):
        """Test that invalid SQL is rejected."""
        sql = "SELECT FROM WHERE"
        with pytest.raises(SQLParseError):
            validator.validate_or_raise(sql)

    def test_subquery_safety(self, validator):
        """Test that subqueries are validated."""
        # Valid subquery
        sql = "SELECT * FROM (SELECT id FROM users) AS subquery"
        validator.validate_or_raise(sql)  # Should not raise

        # Invalid subquery with DELETE
        sql = "SELECT * FROM (DELETE FROM users) AS subquery"
        with pytest.raises(SecurityViolationError):
            validator.validate_or_raise(sql)

    def test_case_insensitive_validation(self, validator):
        """Test that validation is case-insensitive."""
        # Uppercase
        sql = "SELECT * FROM USERS"
        validator.validate_or_raise(sql)  # Should not raise

        # Mixed case INSERT should still be rejected
        sql = "InSeRt INTO users (name) VALUES ('test')"
        with pytest.raises(SecurityViolationError):
            validator.validate_or_raise(sql)
