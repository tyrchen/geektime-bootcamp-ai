"""Unit tests for database API endpoints."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from app.main import app
from app.database import get_session
from app.models.database import DatabaseConnection, ConnectionStatus
from app.models.metadata import DatabaseMetadata
from app.models.query import QueryHistory, QuerySource
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


class TestCreateDatabaseConnection:
    """Test creating database connections."""

    @patch("app.api.v1.databases.test_connection")
    def test_create_database_connection(self, mock_test_conn, client):
        """Test creating a new database connection successfully."""
        # Mock successful connection test
        mock_test_conn.return_value = (True, None)

        response = client.put(
            "/api/v1/dbs/my_database",
            json={
                "url": "postgresql://user:pass@localhost/mydb",
                "description": "My test database",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "my_database"
        assert data["url"] == "postgresql://user:pass@localhost/mydb"
        assert data["description"] == "My test database"
        assert data["status"] == "active"
        assert "createdAt" in data
        assert "updatedAt" in data

        # Verify test_connection was called
        mock_test_conn.assert_called_once_with("postgresql://user:pass@localhost/mydb")

    @patch("app.api.v1.databases.test_connection")
    def test_create_database_connection_invalid_name(self, mock_test_conn, client):
        """Test that invalid database names are rejected."""
        response = client.put(
            "/api/v1/dbs/invalid@name!",
            json={"url": "postgresql://localhost/test"},
        )

        assert response.status_code == 400
        assert "alphanumeric" in response.json()["detail"]

    @patch("app.api.v1.databases.test_connection")
    def test_create_database_connection_test_fails(self, mock_test_conn, client):
        """Test that connection creation fails when connection test fails."""
        # Mock failed connection test
        mock_test_conn.return_value = (False, "Connection refused")

        response = client.put(
            "/api/v1/dbs/failing_db",
            json={"url": "postgresql://localhost/baddb"},
        )

        assert response.status_code == 400
        assert "Connection test failed" in response.json()["detail"]
        assert "Connection refused" in response.json()["detail"]

    @patch("app.api.v1.databases.test_connection")
    def test_update_existing_database_connection(self, mock_test_conn, client, sample_connection):
        """Test updating an existing database connection."""
        # Mock successful connection test
        mock_test_conn.return_value = (True, None)

        response = client.put(
            "/api/v1/dbs/test_db",
            json={
                "url": "postgresql://newuser:newpass@localhost/newdb",
                "description": "Updated description",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_db"
        assert data["url"] == "postgresql://newuser:newpass@localhost/newdb"
        assert data["description"] == "Updated description"

    @patch("app.api.v1.databases.test_connection")
    def test_create_database_connection_with_hyphen_underscore(self, mock_test_conn, client):
        """Test that names with hyphens and underscores are allowed."""
        mock_test_conn.return_value = (True, None)

        response = client.put(
            "/api/v1/dbs/test-db_name",
            json={"url": "postgresql://localhost/test"},
        )

        assert response.status_code == 200


class TestListDatabases:
    """Test listing database connections."""

    def test_list_databases(self, client, sample_connection):
        """Test listing all database connections."""
        # Create another connection
        conn2 = DatabaseConnection(
            name="another_db",
            url="postgresql://localhost/another",
            description="Another database",
            status=ConnectionStatus.ACTIVE,
        )
        client.app.dependency_overrides[get_session]().add(conn2)
        client.app.dependency_overrides[get_session]().commit()

        response = client.get("/api/v1/dbs")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert any(db["name"] == "test_db" for db in data)
        assert any(db["name"] == "another_db" for db in data)

    def test_list_databases_empty(self, client):
        """Test listing databases when none exist."""
        response = client.get("/api/v1/dbs")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0
        assert data == []


class TestGetDatabaseMetadata:
    """Test getting database metadata."""

    @patch("app.api.v1.databases.fetch_metadata")
    def test_get_database_metadata(self, mock_fetch, client, sample_connection):
        """Test retrieving database metadata."""
        # Mock metadata response
        mock_metadata = {
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
        mock_fetch.return_value = mock_metadata

        # Create cached metadata
        cached = DatabaseMetadata(
            database_name="test_db",
            metadata_json=json.dumps(mock_metadata),
            fetched_at=datetime.now(timezone.utc).replace(tzinfo=None),
            table_count=1,
        )
        client.app.dependency_overrides[get_session]().add(cached)
        client.app.dependency_overrides[get_session]().commit()

        response = client.get("/api/v1/dbs/test_db")

        assert response.status_code == 200
        data = response.json()
        assert data["databaseName"] == "test_db"
        assert len(data["tables"]) == 1
        assert data["tables"][0]["name"] == "users"
        assert len(data["views"]) == 0
        assert "fetchedAt" in data
        assert "isStale" in data

    def test_get_database_metadata_not_found(self, client):
        """Test getting metadata for non-existent database."""
        response = client.get("/api/v1/dbs/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch("app.api.v1.databases.fetch_metadata")
    def test_get_database_metadata_with_refresh(self, mock_fetch, client, sample_connection):
        """Test getting metadata with force refresh."""
        mock_metadata = {"tables": [], "views": []}
        mock_fetch.return_value = mock_metadata

        # Create cached metadata
        cached = DatabaseMetadata(
            database_name="test_db",
            metadata_json=json.dumps(mock_metadata),
            fetched_at=datetime.now(timezone.utc).replace(tzinfo=None),
            table_count=0,
        )
        client.app.dependency_overrides[get_session]().add(cached)
        client.app.dependency_overrides[get_session]().commit()

        response = client.get("/api/v1/dbs/test_db?refresh=true")

        assert response.status_code == 200
        # Verify force_refresh was passed to fetch_metadata
        mock_fetch.assert_called_once()
        call_args = mock_fetch.call_args[1]
        assert call_args["force_refresh"] is True


class TestDeleteDatabase:
    """Test deleting database connections."""

    @patch("app.api.v1.databases.close_connection_pool")
    def test_delete_database(self, mock_close_pool, client, sample_connection):
        """Test deleting a database connection."""
        response = client.delete("/api/v1/dbs/test_db")

        assert response.status_code == 204

        # Verify connection pool was closed
        mock_close_pool.assert_called_once_with("test_db")

        # Verify database was deleted
        get_response = client.get("/api/v1/dbs")
        databases = get_response.json()
        assert len(databases) == 0

    def test_delete_database_not_found(self, client):
        """Test deleting non-existent database."""
        response = client.delete("/api/v1/dbs/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestRefreshDatabaseMetadata:
    """Test refreshing database metadata."""

    @patch("app.api.v1.databases.fetch_metadata")
    def test_refresh_database_metadata(self, mock_fetch, client, sample_connection):
        """Test forcing a metadata refresh."""
        # Mock fresh metadata
        fresh_metadata = {
            "tables": [
                {
                    "name": "new_table",
                    "type": "table",
                    "schemaName": "public",
                    "columns": [],
                }
            ],
            "views": [],
        }
        mock_fetch.return_value = fresh_metadata

        # Create cached metadata
        old_metadata = {"tables": [], "views": []}
        cached = DatabaseMetadata(
            database_name="test_db",
            metadata_json=json.dumps(old_metadata),
            fetched_at=(datetime.now(timezone.utc) - timedelta(hours=1)).replace(tzinfo=None),
            table_count=0,
        )
        client.app.dependency_overrides[get_session]().add(cached)
        client.app.dependency_overrides[get_session]().commit()

        response = client.post("/api/v1/dbs/test_db/refresh")

        assert response.status_code == 200
        data = response.json()
        assert data["databaseName"] == "test_db"
        assert len(data["tables"]) == 1
        assert data["tables"][0]["name"] == "new_table"
        assert data["isStale"] is False

        # Verify force_refresh was used
        mock_fetch.assert_called_once()
        call_args = mock_fetch.call_args[1]
        assert call_args["force_refresh"] is True

    def test_refresh_database_metadata_not_found(self, client):
        """Test refreshing metadata for non-existent database."""
        response = client.post("/api/v1/dbs/nonexistent/refresh")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestDatabaseResponseSchema:
    """Test database response schema conversion."""

    def test_to_response(self, sample_connection):
        """Test conversion of DatabaseConnection to response schema."""
        from app.api.v1.databases import to_response

        response = to_response(sample_connection)

        assert response.name == "test_db"
        assert response.url == "postgresql://user:pass@localhost/testdb"
        assert response.description == "Test database"
        assert response.status == "active"
        assert isinstance(response.created_at, datetime)
        assert isinstance(response.updated_at, datetime)
        assert isinstance(response.last_connected_at, datetime)
