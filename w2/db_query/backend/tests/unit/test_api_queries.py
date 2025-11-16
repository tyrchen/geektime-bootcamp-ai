"""Unit tests for query API endpoints."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from app.main import app
from app.database import get_session
from app.models.database import DatabaseConnection, ConnectionStatus
from app.models.query import QueryHistory, QuerySource
from app.models.metadata import DatabaseMetadata
from app.models.schemas import QueryResult, QueryColumn
from app.services.sql_validator import SqlValidationError
import json


@pytest.fixture
def test_session():
    """Create an in-memory SQLite session for testing."""
    # Import all models to ensure tables are created
    from app.models.database import DatabaseConnection
    from app.models.metadata import DatabaseMetadata
    from app.models.query import QueryHistory

    # Use file::memory:?cache=shared to allow multiple connections to the same in-memory database
    engine = create_engine(
        "sqlite:///file:test_db?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False, "uri": True}
    )
    SQLModel.metadata.create_all(engine)
    session = Session(engine, expire_on_commit=False)
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def client(test_session):
    """Create TestClient with test database session."""

    def get_test_session():
        return test_session

    app.dependency_overrides[get_session] = get_test_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_connection(test_session):
    """Create a sample database connection."""
    conn = DatabaseConnection(
        name="test_db",
        url="postgresql://user:pass@localhost/testdb",
        description="Test database",
        status=ConnectionStatus.ACTIVE,
        last_connected_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    test_session.add(conn)
    test_session.commit()
    test_session.refresh(conn)
    return conn


@pytest.fixture
def sample_metadata(test_session):
    """Create sample cached metadata."""
    metadata_dict = {
        "tables": [
            {
                "name": "users",
                "type": "table",
                "schemaName": "public",
                "rowCount": 100,
                "columns": [
                    {
                        "name": "id",
                        "dataType": "integer",
                        "nullable": False,
                        "primaryKey": True,
                        "unique": False,
                        "defaultValue": None,
                    }
                ],
            }
        ],
        "views": [],
    }
    cached = DatabaseMetadata(
        database_name="test_db",
        metadata_json=json.dumps(metadata_dict),
        fetched_at=datetime.now(timezone.utc).replace(tzinfo=None),
        table_count=1,
    )
    test_session.add(cached)
    test_session.commit()
    return metadata_dict


class TestExecuteSqlQuery:
    """Test SQL query execution endpoint."""

    @patch("app.api.v1.queries.execute_query")
    def test_execute_sql_query_success(self, mock_execute, client, sample_connection):
        """Test successful SQL query execution."""
        # Mock query result
        mock_result = QueryResult(
            columns=[
                QueryColumn(name="id", dataType="integer"),
                QueryColumn(name="name", dataType="character varying"),
            ],
            rows=[
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ],
            rowCount=2,
            executionTimeMs=25,
            sql="SELECT * FROM users LIMIT 100",
        )
        mock_execute.return_value = mock_result

        response = client.post(
            "/api/v1/dbs/test_db/query",
            json={"sql": "SELECT * FROM users"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["columns"]) == 2
        assert data["columns"][0]["name"] == "id"
        assert data["rowCount"] == 2
        assert len(data["rows"]) == 2
        assert data["rows"][0]["name"] == "Alice"
        assert data["executionTimeMs"] == 25

        # Verify execute_query was called with correct parameters
        mock_execute.assert_called_once()
        call_args = mock_execute.call_args[0]  # Positional args
        # Args: session, database_name, url, sql, query_source
        assert call_args[1] == "test_db"  # database_name
        assert call_args[3] == "SELECT * FROM users"  # sql
        assert call_args[4] == QuerySource.MANUAL  # query_source

    def test_execute_sql_query_database_not_found(self, client):
        """Test query execution when database doesn't exist."""
        response = client.post(
            "/api/v1/dbs/nonexistent/query",
            json={"sql": "SELECT * FROM users"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch("app.api.v1.queries.execute_query")
    def test_execute_sql_query_validation_error(self, mock_execute, client, sample_connection):
        """Test query execution with SQL validation error."""
        # Mock validation error
        mock_execute.side_effect = SqlValidationError("Only SELECT queries are allowed")

        response = client.post(
            "/api/v1/dbs/test_db/query",
            json={"sql": "INSERT INTO users VALUES (1, 'test')"},
        )

        assert response.status_code == 400
        assert "Only SELECT queries are allowed" in response.json()["detail"]

    @patch("app.api.v1.queries.execute_query")
    def test_execute_sql_query_execution_error(self, mock_execute, client, sample_connection):
        """Test query execution with database error."""
        # Mock execution error
        mock_execute.side_effect = Exception("Table does not exist")

        response = client.post(
            "/api/v1/dbs/test_db/query",
            json={"sql": "SELECT * FROM invalid_table"},
        )

        assert response.status_code == 500
        assert "Query execution failed" in response.json()["detail"]
        assert "Table does not exist" in response.json()["detail"]

    @patch("app.api.v1.queries.execute_query")
    def test_execute_sql_query_empty_result(self, mock_execute, client, sample_connection):
        """Test query execution with empty result set."""
        # Mock empty result
        mock_result = QueryResult(
            columns=[],
            rows=[],
            rowCount=0,
            executionTimeMs=10,
            sql="SELECT * FROM users WHERE id = -1 LIMIT 100",
        )
        mock_execute.return_value = mock_result

        response = client.post(
            "/api/v1/dbs/test_db/query",
            json={"sql": "SELECT * FROM users WHERE id = -1"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rowCount"] == 0
        assert len(data["rows"]) == 0

    def test_execute_sql_query_missing_sql(self, client, sample_connection):
        """Test query execution with missing SQL parameter."""
        response = client.post(
            "/api/v1/dbs/test_db/query",
            json={},
        )

        assert response.status_code == 422  # Validation error


class TestGetQueryHistory:
    """Test query history retrieval endpoint."""

    def test_get_query_history(self, client, sample_connection, test_session):
        """Test retrieving query history for a database."""
        # Create some history entries
        for i in range(5):
            history = QueryHistory(
                database_name="test_db",
                sql_text=f"SELECT {i} FROM users",
                executed_at=datetime.now(timezone.utc).replace(tzinfo=None),
                execution_time_ms=10 + i,
                row_count=i * 10,
                success=True,
                error_message=None,
                query_source=QuerySource.MANUAL,
            )
            test_session.add(history)

        test_session.commit()

        response = client.get("/api/v1/dbs/test_db/history")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        assert all("id" in entry for entry in data)
        assert all("sqlText" in entry for entry in data)
        assert all("executedAt" in entry for entry in data)
        assert data[0]["databaseName"] == "test_db"

    def test_get_query_history_with_limit(self, client, sample_connection, test_session):
        """Test retrieving query history with custom limit."""
        # Create 20 history entries
        for i in range(20):
            history = QueryHistory(
                database_name="test_db",
                sql_text=f"SELECT {i}",
                executed_at=datetime.now(timezone.utc).replace(tzinfo=None),
                execution_time_ms=10,
                row_count=10,
                success=True,
                error_message=None,
                query_source=QuerySource.MANUAL,
            )
            test_session.add(history)

        test_session.commit()

        response = client.get("/api/v1/dbs/test_db/history?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10

    def test_get_query_history_empty(self, client, sample_connection):
        """Test retrieving history when no queries exist."""
        response = client.get("/api/v1/dbs/test_db/history")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0
        assert data == []

    def test_get_query_history_database_not_found(self, client):
        """Test retrieving history for non-existent database."""
        response = client.get("/api/v1/dbs/nonexistent/history")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_query_history_includes_errors(self, client, sample_connection, test_session):
        """Test that history includes both successful and failed queries."""
        # Create successful query
        success_history = QueryHistory(
            database_name="test_db",
            sql_text="SELECT * FROM users",
            executed_at=datetime.now(timezone.utc).replace(tzinfo=None),
            execution_time_ms=20,
            row_count=10,
            success=True,
            error_message=None,
            query_source=QuerySource.MANUAL,
        )
        test_session.add(success_history)

        # Create failed query
        failed_history = QueryHistory(
            database_name="test_db",
            sql_text="SELECT * FROM invalid_table",
            executed_at=datetime.now(timezone.utc).replace(tzinfo=None),
            execution_time_ms=5,
            row_count=None,
            success=False,
            error_message="Table does not exist",
            query_source=QuerySource.NATURAL_LANGUAGE,
        )
        test_session.add(failed_history)

        test_session.commit()

        response = client.get("/api/v1/dbs/test_db/history")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Find failed query in results
        failed = next(entry for entry in data if not entry["success"])
        assert failed["errorMessage"] == "Table does not exist"
        assert failed["rowCount"] is None
        assert failed["querySource"] == "natural_language"


class TestNaturalLanguageToSql:
    """Test natural language to SQL conversion endpoint."""

    @patch("app.api.v1.queries.nl2sql_service.generate_sql")
    def test_natural_language_to_sql(self, mock_generate, client, sample_connection, sample_metadata):
        """Test converting natural language to SQL."""
        # Mock SQL generation
        mock_generate.return_value = {
            "sql": "SELECT * FROM public.users LIMIT 100",
            "explanation": "Generated SQL from: Show me all users",
        }

        response = client.post(
            "/api/v1/dbs/test_db/query/natural",
            json={"prompt": "Show me all users"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sql"] == "SELECT * FROM public.users LIMIT 100"
        assert "explanation" in data
        assert "Show me all users" in data["explanation"]

        # Verify generate_sql was called
        mock_generate.assert_called_once_with(
            "Show me all users",
            sample_metadata,
        )

    def test_natural_language_to_sql_database_not_found(self, client):
        """Test NL to SQL when database doesn't exist."""
        response = client.post(
            "/api/v1/dbs/nonexistent/query/natural",
            json={"prompt": "Show all data"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_natural_language_to_sql_no_metadata(self, client, sample_connection):
        """Test NL to SQL when metadata doesn't exist."""
        response = client.post(
            "/api/v1/dbs/test_db/query/natural",
            json={"prompt": "Show me all users"},
        )

        assert response.status_code == 404
        assert "Metadata not found" in response.json()["detail"]
        assert "refresh metadata" in response.json()["detail"]

    @patch("app.api.v1.queries.nl2sql_service.generate_sql")
    def test_natural_language_to_sql_generation_error(self, mock_generate, client, sample_connection, sample_metadata):
        """Test NL to SQL when generation fails."""
        # Mock generation error
        mock_generate.side_effect = Exception("OpenAI API error")

        response = client.post(
            "/api/v1/dbs/test_db/query/natural",
            json={"prompt": "Show me all users"},
        )

        assert response.status_code == 500
        assert "Failed to generate SQL" in response.json()["detail"]

    def test_natural_language_to_sql_short_prompt(self, client, sample_connection):
        """Test NL to SQL with too short prompt."""
        response = client.post(
            "/api/v1/dbs/test_db/query/natural",
            json={"prompt": "test"},
        )

        # Should fail validation (min_length=5)
        assert response.status_code == 422

    def test_natural_language_to_sql_long_prompt(self, client, sample_connection):
        """Test NL to SQL with too long prompt."""
        response = client.post(
            "/api/v1/dbs/test_db/query/natural",
            json={"prompt": "a" * 501},
        )

        # Should fail validation (max_length=500)
        assert response.status_code == 422

    @patch("app.api.v1.queries.nl2sql_service.generate_sql")
    def test_natural_language_to_sql_chinese(self, mock_generate, client, sample_connection, sample_metadata):
        """Test NL to SQL with Chinese prompt."""
        # Mock SQL generation
        mock_generate.return_value = {
            "sql": "SELECT * FROM public.users LIMIT 100",
            "explanation": "Generated SQL from: 显示所有用户",
        }

        response = client.post(
            "/api/v1/dbs/test_db/query/natural",
            json={"prompt": "显示所有用户"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "sql" in data
        assert "explanation" in data


class TestQueryHistoryEntry:
    """Test query history entry schema conversion."""

    def test_to_history_entry(self, test_session):
        """Test conversion of QueryHistory to QueryHistoryEntry schema."""
        from app.api.v1.queries import to_history_entry

        # Create a query history entry
        history = QueryHistory(
            database_name="test_db",
            sql_text="SELECT * FROM users",
            executed_at=datetime.now(timezone.utc).replace(tzinfo=None),
            execution_time_ms=25,
            row_count=10,
            success=True,
            error_message=None,
            query_source=QuerySource.MANUAL,
        )
        test_session.add(history)
        test_session.commit()
        test_session.refresh(history)

        entry = to_history_entry(history)

        assert entry.id == history.id
        assert entry.database_name == "test_db"
        assert entry.sql_text == "SELECT * FROM users"
        assert entry.execution_time_ms == 25
        assert entry.row_count == 10
        assert entry.success is True
        assert entry.error_message is None
        assert entry.query_source == "manual"

    def test_to_history_entry_failed_query(self, test_session):
        """Test conversion of failed query history."""
        from app.api.v1.queries import to_history_entry

        history = QueryHistory(
            database_name="test_db",
            sql_text="SELECT * FROM invalid",
            executed_at=datetime.now(timezone.utc).replace(tzinfo=None),
            execution_time_ms=5,
            row_count=None,
            success=False,
            error_message="Table not found",
            query_source=QuerySource.NATURAL_LANGUAGE,
        )
        test_session.add(history)
        test_session.commit()
        test_session.refresh(history)

        entry = to_history_entry(history)

        assert entry.success is False
        assert entry.error_message == "Table not found"
        assert entry.row_count is None
        assert entry.query_source == "natural_language"
