"""High-level database service (Facade pattern)."""

import time
from typing import Tuple, Optional
import logging

from app.models.database import DatabaseType
from app.adapters.base import ConnectionConfig, QueryResult, MetadataResult
from app.adapters.registry import DatabaseAdapterRegistry, adapter_registry
from app.services.sql_validator import validate_and_transform_sql, SqlValidationError

logger = logging.getLogger(__name__)


class DatabaseService:
    """High-level service for database operations (Facade pattern).

    This class provides a simplified interface to database operations,
    coordinating between adapters, validators, and other components.

    Example:
        service = DatabaseService(adapter_registry)
        result = await service.execute_query(
            DatabaseType.POSTGRESQL,
            "mydb",
            "postgresql://...",
            "SELECT * FROM users"
        )
    """

    def __init__(self, registry: DatabaseAdapterRegistry):
        """Initialize service with adapter registry.

        Args:
            registry: Database adapter registry
        """
        self.registry = registry
        logger.info("Initialized DatabaseService")

    async def test_connection(
        self, db_type: DatabaseType, url: str
    ) -> Tuple[bool, Optional[str]]:
        """Test database connection.

        Args:
            db_type: Database type
            url: Connection URL

        Returns:
            Tuple of (success, error_message)

        Example:
            success, error = await service.test_connection(
                DatabaseType.POSTGRESQL,
                "postgresql://localhost/test"
            )
        """
        config = ConnectionConfig(url=url, name="test")
        adapter = self.registry.get_adapter(db_type, config)
        return await adapter.test_connection()

    async def execute_query(
        self,
        db_type: DatabaseType,
        name: str,
        url: str,
        sql: str,
        limit: int = 1000,
    ) -> Tuple[QueryResult, int]:
        """Execute SQL query.

        Args:
            db_type: Database type
            name: Connection name
            url: Connection URL
            sql: SQL query (will be validated)
            limit: Maximum rows to return

        Returns:
            Tuple of (QueryResult, execution_time_ms)

        Raises:
            SqlValidationError: If SQL is invalid
            Exception: If query execution fails

        Example:
            result, time_ms = await service.execute_query(
                DatabaseType.MYSQL,
                "mydb",
                "mysql://...",
                "SELECT * FROM users"
            )
        """
        # Validate SQL
        validated_sql = validate_and_transform_sql(sql, limit=limit, db_type=db_type)

        # Get adapter
        config = ConnectionConfig(url=url, name=name)
        adapter = self.registry.get_adapter(db_type, config)

        # Execute query with timing
        start_time = time.time()
        try:
            result = await adapter.execute_query(validated_sql)
            execution_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"Query executed successfully on {name}: "
                f"{result.row_count} rows in {execution_time_ms}ms"
            )

            return result, execution_time_ms

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Query failed on {name} after {execution_time_ms}ms: {e}")
            raise

    async def extract_metadata(
        self,
        db_type: DatabaseType,
        name: str,
        url: str,
    ) -> MetadataResult:
        """Extract database metadata.

        Args:
            db_type: Database type
            name: Connection name
            url: Connection URL

        Returns:
            MetadataResult

        Example:
            metadata = await service.extract_metadata(
                DatabaseType.POSTGRESQL,
                "mydb",
                "postgresql://..."
            )
        """
        config = ConnectionConfig(url=url, name=name)
        adapter = self.registry.get_adapter(db_type, config)

        logger.info(f"Extracting metadata for {name}")
        metadata = await adapter.extract_metadata()
        logger.info(
            f"Extracted metadata for {name}: "
            f"{len(metadata.tables)} tables, {len(metadata.views)} views"
        )

        return metadata

    async def close_connection(
        self,
        db_type: DatabaseType,
        name: str,
    ) -> None:
        """Close database connection.

        Args:
            db_type: Database type
            name: Connection name
        """
        await self.registry.close_adapter(db_type, name)
        logger.info(f"Closed connection for {name}")


# Global service instance
database_service = DatabaseService(adapter_registry)
