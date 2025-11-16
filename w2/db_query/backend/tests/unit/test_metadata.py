"""Unit tests for metadata extraction service."""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from sqlmodel import Session, SQLModel, create_engine, select
from app.services.metadata import (
    extract_metadata,
    get_cached_metadata,
    cache_metadata,
    fetch_metadata,
)
from app.models.metadata import DatabaseMetadata


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


@pytest.fixture
def sample_metadata():
    """Sample metadata dictionary."""
    return {
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
                    },
                    {
                        "name": "name",
                        "dataType": "character varying",
                        "nullable": False,
                        "primaryKey": False,
                        "unique": False,
                        "defaultValue": None,
                    },
                ],
            }
        ],
        "views": [
            {
                "name": "user_summary",
                "type": "view",
                "schemaName": "public",
                "columns": [
                    {
                        "name": "total_users",
                        "dataType": "bigint",
                        "nullable": True,
                        "primaryKey": False,
                        "unique": False,
                        "defaultValue": None,
                    }
                ],
            }
        ],
    }


class TestExtractMetadata:
    """Test metadata extraction from PostgreSQL."""

    @pytest.mark.asyncio
    async def test_extract_metadata_tables(self, mock_pool):
        """Test extracting table metadata from database."""
        pool, conn = mock_pool

        # Mock tables query result
        conn.fetch.side_effect = [
            # Tables query
            [
                {"schemaname": "public", "tablename": "users", "type": "table"},
                {"schemaname": "public", "tablename": "orders", "type": "table"},
            ],
            # Columns for users table
            [
                {
                    "column_name": "id",
                    "data_type": "integer",
                    "character_maximum_length": None,
                    "is_nullable": "NO",
                    "column_default": "nextval('users_id_seq'::regclass)",
                    "ordinal_position": 1,
                    "is_primary_key": True,
                    "is_unique": False,
                },
                {
                    "column_name": "email",
                    "data_type": "character varying",
                    "character_maximum_length": 255,
                    "is_nullable": "NO",
                    "column_default": None,
                    "ordinal_position": 2,
                    "is_primary_key": False,
                    "is_unique": True,
                },
            ],
            # Columns for orders table
            [
                {
                    "column_name": "id",
                    "data_type": "integer",
                    "character_maximum_length": None,
                    "is_nullable": "NO",
                    "column_default": None,
                    "ordinal_position": 1,
                    "is_primary_key": True,
                    "is_unique": False,
                },
            ],
        ]

        # Mock row count queries - asyncpg returns Record objects that support indexing
        # The code accesses count_result[0] so we need to return a tuple-like object
        mock_row_1 = MagicMock()
        mock_row_1.__getitem__ = lambda self, idx: 100
        mock_row_2 = MagicMock()
        mock_row_2.__getitem__ = lambda self, idx: 50
        conn.fetchrow.side_effect = [
            mock_row_1,  # users count
            mock_row_2,  # orders count
        ]

        metadata = await extract_metadata("test_db", pool)

        assert "tables" in metadata
        assert "views" in metadata
        assert len(metadata["tables"]) == 2

        # Check first table
        users_table = metadata["tables"][0]
        assert users_table["name"] == "users"
        assert users_table["type"] == "table"
        assert users_table["schemaName"] == "public"
        assert users_table["rowCount"] == 100
        assert len(users_table["columns"]) == 2

        # Check column metadata
        id_column = users_table["columns"][0]
        assert id_column["name"] == "id"
        assert id_column["dataType"] == "integer"
        assert id_column["nullable"] is False
        assert id_column["primaryKey"] is True

        email_column = users_table["columns"][1]
        assert email_column["name"] == "email"
        assert email_column["dataType"] == "character varying(255)"
        assert email_column["unique"] is True

    @pytest.mark.asyncio
    async def test_extract_metadata_with_views(self, mock_pool):
        """Test extracting view metadata from database."""
        pool, conn = mock_pool

        # Mock tables query result with a view
        conn.fetch.side_effect = [
            # Tables query
            [
                {"schemaname": "public", "tablename": "user_stats", "type": "view"},
            ],
            # Columns for view
            [
                {
                    "column_name": "total",
                    "data_type": "bigint",
                    "character_maximum_length": None,
                    "is_nullable": "YES",
                    "column_default": None,
                    "ordinal_position": 1,
                    "is_primary_key": False,
                    "is_unique": False,
                },
            ],
        ]

        metadata = await extract_metadata("test_db", pool)

        assert len(metadata["views"]) == 1
        assert len(metadata["tables"]) == 0

        view = metadata["views"][0]
        assert view["name"] == "user_stats"
        assert view["type"] == "view"
        assert "rowCount" not in view  # Views don't have row counts

    @pytest.mark.asyncio
    async def test_extract_metadata_handles_count_errors(self, mock_pool):
        """Test that metadata extraction handles row count errors gracefully."""
        pool, conn = mock_pool

        # Mock tables query
        conn.fetch.side_effect = [
            [{"schemaname": "public", "tablename": "test_table", "type": "table"}],
            [  # Columns
                {
                    "column_name": "id",
                    "data_type": "integer",
                    "character_maximum_length": None,
                    "is_nullable": "NO",
                    "column_default": None,
                    "ordinal_position": 1,
                    "is_primary_key": True,
                    "is_unique": False,
                },
            ],
        ]

        # Mock row count to raise error
        conn.fetchrow.side_effect = Exception("Permission denied")

        metadata = await extract_metadata("test_db", pool)

        # Should still return metadata but without row count
        assert len(metadata["tables"]) == 1
        table = metadata["tables"][0]
        assert "rowCount" not in table or table["rowCount"] is None


class TestGetCachedMetadata:
    """Test cached metadata retrieval."""

    @pytest.mark.asyncio
    async def test_get_cached_metadata_returns_fresh(self, test_session, sample_metadata):
        """Test that fresh metadata is returned from cache."""
        # Create fresh metadata (just fetched)
        cached = DatabaseMetadata(
            database_name="test_db",
            metadata_json=json.dumps(sample_metadata),
            fetched_at=datetime.now(timezone.utc).replace(tzinfo=None),
            table_count=2,
        )
        test_session.add(cached)
        test_session.commit()

        result = await get_cached_metadata(test_session, "test_db")

        assert result is not None
        assert result.database_name == "test_db"
        assert result.is_stale is False

    @pytest.mark.asyncio
    async def test_get_cached_metadata_returns_none_when_stale(self, test_session, sample_metadata):
        """Test that stale metadata returns None."""
        # Create stale metadata (fetched 25 hours ago, default cache is 24 hours)
        stale_time = (datetime.now(timezone.utc) - timedelta(hours=25)).replace(tzinfo=None)
        cached = DatabaseMetadata(
            database_name="test_db",
            metadata_json=json.dumps(sample_metadata),
            fetched_at=stale_time,
            table_count=2,
        )
        test_session.add(cached)
        test_session.commit()

        result = await get_cached_metadata(test_session, "test_db")

        # Should return None because cache is stale
        assert result is None or result.is_stale is True

    @pytest.mark.asyncio
    async def test_get_cached_metadata_returns_none_when_not_exists(self, test_session):
        """Test that None is returned when no cache exists."""
        result = await get_cached_metadata(test_session, "nonexistent_db")

        assert result is None


class TestCacheMetadata:
    """Test metadata caching."""

    @pytest.mark.asyncio
    async def test_cache_metadata_creates_new(self, test_session, sample_metadata):
        """Test creating new metadata cache entry."""
        result = await cache_metadata(test_session, "test_db", sample_metadata)

        assert result.database_name == "test_db"
        assert result.table_count == 2  # 1 table + 1 view
        assert isinstance(result.fetched_at, datetime)

        # Verify stored JSON
        stored_metadata = json.loads(result.metadata_json)
        assert stored_metadata == sample_metadata

        # Verify it's in the database
        statement = select(DatabaseMetadata).where(DatabaseMetadata.database_name == "test_db")
        cached = test_session.exec(statement).first()
        assert cached is not None

    @pytest.mark.asyncio
    async def test_cache_metadata_updates_existing(self, test_session, sample_metadata):
        """Test updating existing metadata cache."""
        # Create initial cache
        old_metadata = {"tables": [], "views": []}
        initial = DatabaseMetadata(
            database_name="test_db",
            metadata_json=json.dumps(old_metadata),
            fetched_at=(datetime.now(timezone.utc) - timedelta(hours=1)).replace(tzinfo=None),
            table_count=0,
        )
        test_session.add(initial)
        test_session.commit()
        old_id = initial.id

        # Update cache
        result = await cache_metadata(test_session, "test_db", sample_metadata)

        # Should have same ID (updated, not created new)
        assert result.id == old_id
        assert result.table_count == 2
        assert json.loads(result.metadata_json) == sample_metadata

        # Verify only one entry exists
        statement = select(DatabaseMetadata).where(DatabaseMetadata.database_name == "test_db")
        all_entries = test_session.exec(statement).all()
        assert len(all_entries) == 1


class TestFetchMetadata:
    """Test metadata fetching with caching."""

    @pytest.mark.asyncio
    async def test_fetch_metadata_uses_cache(self, test_session, sample_metadata):
        """Test that fetch uses cache when available and fresh."""
        # Create fresh cache
        cached = DatabaseMetadata(
            database_name="test_db",
            metadata_json=json.dumps(sample_metadata),
            fetched_at=datetime.now(timezone.utc).replace(tzinfo=None),
            table_count=2,
        )
        test_session.add(cached)
        test_session.commit()

        # Mock get_connection_pool to ensure it's not called
        with patch("app.services.metadata.get_connection_pool") as mock_pool:
            result = await fetch_metadata(
                test_session,
                "test_db",
                "postgresql://localhost/test",
                force_refresh=False,
            )

            # Should not have called get_connection_pool
            mock_pool.assert_not_called()

        assert result == sample_metadata

    @pytest.mark.asyncio
    async def test_fetch_metadata_refreshes_when_stale(self, test_session, sample_metadata, mock_pool):
        """Test that fetch refreshes when cache is stale."""
        pool, conn = mock_pool

        # Create stale cache
        stale_time = (datetime.now(timezone.utc) - timedelta(hours=25)).replace(tzinfo=None)
        cached = DatabaseMetadata(
            database_name="test_db",
            metadata_json=json.dumps({"tables": [], "views": []}),
            fetched_at=stale_time,
            table_count=0,
        )
        test_session.add(cached)
        test_session.commit()

        # Mock extract_metadata
        with patch("app.services.metadata.get_connection_pool", return_value=pool):
            with patch("app.services.metadata.extract_metadata", return_value=sample_metadata) as mock_extract:
                result = await fetch_metadata(
                    test_session,
                    "test_db",
                    "postgresql://localhost/test",
                    force_refresh=False,
                )

                # Should have called extract_metadata
                mock_extract.assert_called_once()

        assert result == sample_metadata

    @pytest.mark.asyncio
    async def test_fetch_metadata_force_refresh(self, test_session, sample_metadata, mock_pool):
        """Test that force_refresh bypasses cache."""
        pool, conn = mock_pool

        # Create fresh cache
        cached = DatabaseMetadata(
            database_name="test_db",
            metadata_json=json.dumps({"tables": [], "views": []}),
            fetched_at=datetime.now(timezone.utc).replace(tzinfo=None),
            table_count=0,
        )
        test_session.add(cached)
        test_session.commit()

        # Mock extract_metadata
        with patch("app.services.metadata.get_connection_pool", return_value=pool):
            with patch("app.services.metadata.extract_metadata", return_value=sample_metadata) as mock_extract:
                result = await fetch_metadata(
                    test_session,
                    "test_db",
                    "postgresql://localhost/test",
                    force_refresh=True,
                )

                # Should have called extract_metadata even with fresh cache
                mock_extract.assert_called_once()

        assert result == sample_metadata

    @pytest.mark.asyncio
    async def test_fetch_metadata_no_cache(self, test_session, sample_metadata, mock_pool):
        """Test fetching metadata when no cache exists."""
        pool, conn = mock_pool

        # Mock extract_metadata
        with patch("app.services.metadata.get_connection_pool", return_value=pool):
            with patch("app.services.metadata.extract_metadata", return_value=sample_metadata) as mock_extract:
                result = await fetch_metadata(
                    test_session,
                    "test_db",
                    "postgresql://localhost/test",
                    force_refresh=False,
                )

                # Should have called extract_metadata
                mock_extract.assert_called_once()

        assert result == sample_metadata

        # Verify cache was created
        statement = select(DatabaseMetadata).where(DatabaseMetadata.database_name == "test_db")
        cached = test_session.exec(statement).first()
        assert cached is not None
        assert json.loads(cached.metadata_json) == sample_metadata
