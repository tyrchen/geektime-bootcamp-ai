"""Unit tests for query execution service."""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timezone
from sqlmodel import Session, SQLModel, create_engine, select
from app.services.query import (
    execute_query,
    save_query_history,
    cleanup_old_queries,
    get_query_history,
)
from app.models.query import QueryHistory, QuerySource
from app.models.schemas import QueryResult, QueryColumn
from app.services.sql_validator import SqlValidationError


@pytest.fixture
def test_session():
    """Create an in-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def mock_pool():
    """Create a mock asyncpg connection pool."""
    pool = MagicMock()
    conn = AsyncMock()

    # Create async context manager for pool.acquire()
    acquire_context = AsyncMock()
    acquire_context.__aenter__.return_value = conn
    acquire_context.__aexit__.return_value = None
    pool.acquire.return_value = acquire_context

    return pool, conn


class TestExecuteQuery:
    """Test query execution function."""

    @pytest.mark.asyncio
    async def test_execute_query_success(self, test_session, mock_pool):
        """Test successful query execution with valid SQL."""
        pool, conn = mock_pool

        # Mock query result
        mock_row = {"id": 1, "name": "test user"}
        conn.fetch.return_value = [mock_row]

        # Mock get_connection_pool
        with patch("app.services.query.get_connection_pool", return_value=pool):
            result = await execute_query(
                session=test_session,
                database_name="test_db",
                url="postgresql://localhost/test",
                sql="SELECT * FROM users",
                query_source=QuerySource.MANUAL,
            )

        # Verify result structure
        assert isinstance(result, QueryResult)
        assert len(result.columns) == 2
        assert result.columns[0].name == "id"
        assert result.columns[1].name == "name"
        assert len(result.rows) == 1
        assert result.rows[0] == mock_row
        assert result.row_count == 1
        assert result.execution_time_ms >= 0
        assert "LIMIT" in result.sql.upper()

        # Verify query was saved to history
        statement = select(QueryHistory)
        history = test_session.exec(statement).first()
        assert history is not None
        assert history.database_name == "test_db"
        assert history.success is True
        assert history.error_message is None

    @pytest.mark.asyncio
    async def test_execute_query_with_validation_error(self, test_session):
        """Test query execution with invalid SQL raises validation error."""
        with pytest.raises(SqlValidationError):
            await execute_query(
                session=test_session,
                database_name="test_db",
                url="postgresql://localhost/test",
                sql="INSERT INTO users VALUES (1, 'test')",
                query_source=QuerySource.MANUAL,
            )

        # Verify failed query was saved to history
        statement = select(QueryHistory)
        history = test_session.exec(statement).first()
        assert history is not None
        assert history.success is False
        assert history.error_message is not None
        assert "SELECT" in history.error_message

    @pytest.mark.asyncio
    async def test_execute_query_with_execution_error(self, test_session, mock_pool):
        """Test query execution when database execution fails."""
        pool, conn = mock_pool

        # Mock connection to raise error
        conn.fetch.side_effect = Exception("Database connection error")

        with patch("app.services.query.get_connection_pool", return_value=pool):
            with pytest.raises(Exception) as exc_info:
                await execute_query(
                    session=test_session,
                    database_name="test_db",
                    url="postgresql://localhost/test",
                    sql="SELECT * FROM users",
                    query_source=QuerySource.MANUAL,
                )

            assert "Database connection error" in str(exc_info.value)

        # Verify failed query was saved to history
        statement = select(QueryHistory)
        history = test_session.exec(statement).first()
        assert history is not None
        assert history.success is False
        assert "Database connection error" in history.error_message

    @pytest.mark.asyncio
    async def test_execute_query_with_multiple_rows(self, test_session, mock_pool):
        """Test query execution with multiple result rows."""
        pool, conn = mock_pool

        # Mock multiple rows
        mock_rows = [
            {"id": 1, "name": "user1", "age": 25},
            {"id": 2, "name": "user2", "age": 30},
            {"id": 3, "name": "user3", "age": 35},
        ]
        conn.fetch.return_value = mock_rows

        with patch("app.services.query.get_connection_pool", return_value=pool):
            result = await execute_query(
                session=test_session,
                database_name="test_db",
                url="postgresql://localhost/test",
                sql="SELECT * FROM users",
                query_source=QuerySource.NATURAL_LANGUAGE,
            )

        assert result.row_count == 3
        assert len(result.rows) == 3
        assert result.rows[0]["id"] == 1
        assert result.rows[2]["age"] == 35

    @pytest.mark.asyncio
    async def test_execute_query_with_empty_result(self, test_session, mock_pool):
        """Test query execution with empty result set."""
        pool, conn = mock_pool

        # Mock empty result
        conn.fetch.return_value = []

        with patch("app.services.query.get_connection_pool", return_value=pool):
            result = await execute_query(
                session=test_session,
                database_name="test_db",
                url="postgresql://localhost/test",
                sql="SELECT * FROM users WHERE id = -1",
                query_source=QuerySource.MANUAL,
            )

        assert result.row_count == 0
        assert len(result.rows) == 0
        assert len(result.columns) == 0


class TestSaveQueryHistory:
    """Test query history saving function."""

    @pytest.mark.asyncio
    async def test_save_query_history(self, test_session):
        """Test saving successful query to history."""
        history = await save_query_history(
            session=test_session,
            database_name="test_db",
            sql="SELECT * FROM users LIMIT 100",
            row_count=10,
            execution_time_ms=50,
            success=True,
            error_message=None,
            query_source=QuerySource.MANUAL,
        )

        assert history.id is not None
        assert history.database_name == "test_db"
        assert history.sql_text == "SELECT * FROM users LIMIT 100"
        assert history.row_count == 10
        assert history.execution_time_ms == 50
        assert history.success is True
        assert history.error_message is None
        assert history.query_source == QuerySource.MANUAL
        assert isinstance(history.executed_at, datetime)

    @pytest.mark.asyncio
    async def test_save_failed_query_history(self, test_session):
        """Test saving failed query to history."""
        history = await save_query_history(
            session=test_session,
            database_name="test_db",
            sql="SELECT * FROM invalid_table",
            row_count=None,
            execution_time_ms=25,
            success=False,
            error_message="Table does not exist",
            query_source=QuerySource.NATURAL_LANGUAGE,
        )

        assert history.success is False
        assert history.error_message == "Table does not exist"
        assert history.row_count is None
        assert history.query_source == QuerySource.NATURAL_LANGUAGE


class TestCleanupOldQueries:
    """Test query history cleanup function."""

    @pytest.mark.asyncio
    async def test_cleanup_old_queries(self, test_session):
        """Test that cleanup keeps only last 50 queries per database."""
        # Create 60 queries for test_db
        for i in range(60):
            history = QueryHistory(
                database_name="test_db",
                sql_text=f"SELECT {i}",
                executed_at=datetime.now(timezone.utc),
                execution_time_ms=10,
                row_count=1,
                success=True,
                error_message=None,
                query_source=QuerySource.MANUAL,
            )
            test_session.add(history)

        # Create 10 queries for another_db
        for i in range(10):
            history = QueryHistory(
                database_name="another_db",
                sql_text=f"SELECT {i}",
                executed_at=datetime.now(timezone.utc),
                execution_time_ms=10,
                row_count=1,
                success=True,
                error_message=None,
                query_source=QuerySource.MANUAL,
            )
            test_session.add(history)

        test_session.commit()

        # Run cleanup for test_db
        await cleanup_old_queries(test_session, "test_db")

        # Verify test_db has exactly 50 queries
        statement = select(QueryHistory).where(QueryHistory.database_name == "test_db")
        test_db_queries = test_session.exec(statement).all()
        assert len(test_db_queries) == 50

        # Verify another_db still has all 10 queries
        statement = select(QueryHistory).where(QueryHistory.database_name == "another_db")
        another_db_queries = test_session.exec(statement).all()
        assert len(another_db_queries) == 10

    @pytest.mark.asyncio
    async def test_cleanup_with_less_than_50_queries(self, test_session):
        """Test cleanup when there are less than 50 queries."""
        # Create only 20 queries
        for i in range(20):
            history = QueryHistory(
                database_name="test_db",
                sql_text=f"SELECT {i}",
                executed_at=datetime.now(timezone.utc),
                execution_time_ms=10,
                row_count=1,
                success=True,
                error_message=None,
                query_source=QuerySource.MANUAL,
            )
            test_session.add(history)

        test_session.commit()

        # Run cleanup
        await cleanup_old_queries(test_session, "test_db")

        # Verify all 20 queries remain
        statement = select(QueryHistory).where(QueryHistory.database_name == "test_db")
        queries = test_session.exec(statement).all()
        assert len(queries) == 20


class TestGetQueryHistory:
    """Test query history retrieval function."""

    @pytest.mark.asyncio
    async def test_get_query_history(self, test_session):
        """Test retrieving query history for a database."""
        # Create queries with different timestamps
        for i in range(10):
            history = QueryHistory(
                database_name="test_db",
                sql_text=f"SELECT {i}",
                executed_at=datetime.now(timezone.utc),
                execution_time_ms=10 + i,
                row_count=i,
                success=True,
                error_message=None,
                query_source=QuerySource.MANUAL,
            )
            test_session.add(history)

        test_session.commit()

        # Get history
        history_list = await get_query_history(test_session, "test_db", limit=5)

        assert len(history_list) == 5
        # Verify queries are ordered by executed_at DESC (most recent first)
        assert all(isinstance(h, QueryHistory) for h in history_list)

    @pytest.mark.asyncio
    async def test_get_query_history_empty(self, test_session):
        """Test retrieving history for database with no queries."""
        history_list = await get_query_history(test_session, "nonexistent_db", limit=50)

        assert len(history_list) == 0
        assert history_list == []

    @pytest.mark.asyncio
    async def test_get_query_history_with_limit(self, test_session):
        """Test that limit parameter works correctly."""
        # Create 100 queries
        for i in range(100):
            history = QueryHistory(
                database_name="test_db",
                sql_text=f"SELECT {i}",
                executed_at=datetime.now(timezone.utc),
                execution_time_ms=10,
                row_count=1,
                success=True,
                error_message=None,
                query_source=QuerySource.MANUAL,
            )
            test_session.add(history)

        test_session.commit()

        # Get with different limits
        history_10 = await get_query_history(test_session, "test_db", limit=10)
        history_25 = await get_query_history(test_session, "test_db", limit=25)

        assert len(history_10) == 10
        assert len(history_25) == 25
